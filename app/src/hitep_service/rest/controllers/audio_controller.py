import datetime
import io
import logging
import os
import uuid

import numpy as np
from cltl.backend.api.microphone import AudioParameters
from cltl.backend.api.storage import AudioStorage
from cltl.combot.event.emissor import AudioSignalStopped
from cltl.combot.infra.event import EventBus, Event
from cltl.combot.infra.time_util import timestamp_now
from cltl_service.backend.schema import BackendAudioSignalStarted
from cltl_service.vad.schema import VadAnnotation, VadMentionEvent
from connexion import request
from emissor.representation.scenario import AudioSignal
from scipy.io import wavfile

from hitep_service.rest.controllers.scenario_controller import ScenarioController

logger = logging.getLogger(__name__)


class AudioController:
    def __init__(self, mic_topic: str, vad_topic: str,
                 storage_path: str, scenario_controller: ScenarioController,
                 audio_storage: AudioStorage, event_bus: EventBus):
        self._storage_path = storage_path
        self._scenario_controller = scenario_controller
        self._audio_storage = audio_storage
        self._event_bus = event_bus

        self._mic_topic = mic_topic
        self._vad_topic = vad_topic

        if self._storage_path:
            os.makedirs(self._storage_path, exist_ok=True)
            logger.info("Ensured %s", self._storage_path)

    def add_audio(self, scenario_id, body):  # noqa: E501
        current = self._scenario_controller.current
        if not current or current.id != scenario_id:
            return {"error": f"Scenario ID does not match, expected: {current and current.id}, actual: {scenario_id}"}, 400

        content_type = request.headers.get("Content-Type", "").lower()
        if content_type not in ["audio/wav", "audio/x-wav"]:
            return {"error": "Invalid file type. Only WAV files are allowed."}, 400

        if not body:
            return {"error": "No file content received."}, 400

        if self._storage_path:
            date_string = datetime.datetime.now().isoformat('_', 'seconds').replace(":", "_")
            file_path = os.path.join(self._storage_path, f"{date_string}.wav")

            with open(file_path, "wb") as f:
                f.write(body)

            logger.debug("Received WAV file of length %s", len(body))

        if self._audio_storage:
            sampling_rate, audio_data = wavfile.read(io.BytesIO(body))
            audio_id = str(uuid.uuid4())
            self._audio_storage.store(audio_id, audio_data, sampling_rate)

            self._publish_events(audio_id, audio_data, sampling_rate)

            logger.info("Received WAV file of %s samples (sampling rate: %s), id: %s",
                        audio_data.shape, sampling_rate, audio_id)

    def _publish_events(self, audio_id, audio_data: np.ndarray, sampling_rate: int):
        duration = len(audio_data) / sampling_rate
        end_time = timestamp_now()
        audio_params = AudioParameters(sampling_rate, audio_data.shape[1], audio_data.shape[0], 2)

        signal = self._create_audio_signal(audio_id, audio_params, length=audio_data.shape[0],
                                           start=int(end_time - duration * 1000), stop=end_time)
        started = BackendAudioSignalStarted.create_backend_signal(signal, audio_params)
        event = Event.for_payload(started)
        self._event_bus.publish(self._mic_topic, event)

        stopped = AudioSignalStopped.create(signal)
        event = Event.for_payload(stopped)
        self._event_bus.publish(self._mic_topic, event)

        vad_event = self._create_payload(signal.ruler)
        self._event_bus.publish(self._vad_topic, Event.for_payload(vad_event))

    def _create_payload(self, segment):
        annotation = VadAnnotation.for_activation(1.0, self.__class__.__name__)

        return VadMentionEvent.create(segment, annotation)

    def _create_audio_signal(self, audio_id: str, parameters: AudioParameters,
                                 start: int = None, stop: int = None, length: int = None) -> AudioSignal:
            return AudioSignal.for_scenario(self._scenario_controller.current, start, stop,
                                            f"cltl-storage:audio/{audio_id}",
                                            length, parameters.channels, signal_id=audio_id)
