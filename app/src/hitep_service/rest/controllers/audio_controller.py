import datetime
import logging
import os

from cltl.combot.infra.event import EventBus
from connexion import request
from flask import jsonify

from hitep_service.rest.controllers.scenario_controller import ScenarioController

logger = logging.getLogger(__name__)


class AudioController:
    def __init__(self, storage_path: str, scenario_controller: ScenarioController, event_bus: EventBus):
        self._storage_path = storage_path
        self._scenario_controller = scenario_controller
        self._event_bus = event_bus

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

        logger.info("Received WAV file of length %s", len(body))