import argparse
import logging.config
import logging.config
import os
import pathlib
import time

from a2wsgi import ASGIMiddleware
from cltl.backend.api.storage import AudioStorage
from cltl.brain import LongTermMemory
from cltl.chatui.api import Chats
from cltl.chatui.memory import MemoryChats
from cltl.combot.infra.config.k8config import K8LocalConfigurationContainer
from cltl.combot.infra.di_container import singleton
from cltl.combot.infra.event.memory import SynchronousEventBusContainer
from cltl.combot.infra.event_log import LogWriter
from cltl.combot.infra.resource.threaded import ThreadedResourceContainer
from cltl.backend.impl.cached_storage import CachedAudioStorage
from cltl.emissordata.api import EmissorDataStorage
from cltl.emissordata.file_storage import EmissorDataFileStorage
from cltl_service.asr.service import AsrService
from cltl_service.backend.storage import StorageService
from cltl_service.brain.service import BrainService
from cltl_service.chatui.service import ChatUiService
from cltl_service.combot.event_log.service import EventLogService
from cltl_service.emissordata.client import EmissorDataClient
from cltl_service.emissordata.service import EmissorDataService
from emissor.representation.util import serializer as emissor_serializer
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

from hitep_service.importance.service import HiTepImportanceConvService
from hitep_service.rest.service import HiTepRESTService

logging.config.fileConfig(os.environ.get('CLTL_LOGGING_CONFIG', default='config/logging.config'),
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class InfraContainer(SynchronousEventBusContainer, K8LocalConfigurationContainer, ThreadedResourceContainer):
    pass


class EmissorStorageContainer(InfraContainer):
    @property
    @singleton
    def emissor_storage(self) -> EmissorDataStorage:
        return EmissorDataFileStorage.from_config(self.config_manager)

    @property
    @singleton
    def emissor_data_service(self) -> EmissorDataService:
        return EmissorDataService.from_config(self.emissor_storage,
                                              self.event_bus, self.resource_manager, self.config_manager)

    @property
    @singleton
    def emissor_data_client(self) -> EmissorDataClient:
        return EmissorDataClient("http://0.0.0.0:8000/emissor")

    def start(self):
        logger.info("Start Emissor Data Storage")
        super().start()
        self.emissor_data_service.start()

    def stop(self):
        try:
            logger.info("Stop Emissor Data Storage")
            self.emissor_data_service.stop()
        finally:
            super().stop()


class ChatUIContainer(InfraContainer):
    @property
    @singleton
    def chats(self) -> Chats:
        return MemoryChats()

    @property
    @singleton
    def chatui_service(self) -> ChatUiService:
        return ChatUiService.from_config(MemoryChats(), self.event_bus, self.resource_manager, self.config_manager)

    def start(self):
        logger.info("Start Chat UI")
        super().start()
        self.chatui_service.start()

    def stop(self):
        try:
            logger.info("Stop Chat UI")
            self.chatui_service.stop()
        finally:
            super().stop()


class BrainContainer(InfraContainer):
    @property
    @singleton
    def brain(self) -> LongTermMemory:
        config = self.config_manager.get_config("cltl.brain")
        brain_address = config.get("address")
        if not brain_address:
            return False

        brain_log_dir = config.get("log_dir")
        clear_brain = bool(config.get_boolean("clear_brain"))

        # TODO figure out how to put the brain RDF files in the EMISSOR scenario folder
        return LongTermMemory(address=brain_address,
                              log_dir=pathlib.Path(brain_log_dir),
                              clear_all=clear_brain)

    @property
    @singleton
    def brain_service(self) -> BrainService:
        if self.brain:
            return BrainService.from_config(self.brain, self.event_bus, self.resource_manager, self.config_manager)

        return False

    def start(self):
        logger.info("Start Brain")
        super().start()
        if self.brain_service:
            self.brain_service.start()

    def stop(self):
        try:
            if self.brain_service:
                logger.info("Stop Brain")
                self.brain_service.stop()
        finally:
            super().stop()


class BackendContainer(InfraContainer):
    @property
    @singleton
    def audio_storage(self) -> AudioStorage:
        return CachedAudioStorage.from_config(self.config_manager)

    @property
    @singleton
    def storage_service(self) -> StorageService:
        return StorageService(self.audio_storage, None)

    def start(self):
        logger.info("Start Backend service")
        super().start()
        self.storage_service.start()

    def stop(self):
        try:
            logger.info("Stop Backend service")
            self.storage_service.stop()
        finally:
            super().stop()


class ASRContainer(EmissorStorageContainer, InfraContainer):
    @property
    @singleton
    def asr_service(self) -> AsrService:
        config = self.config_manager.get_config("cltl.asr")
        sampling_rate = config.get_int("sampling_rate")
        implementation = config.get("implementation")

        storage = None
        # DEBUG
        # storage = "/Users/tkb/automatic/workspaces/robo/eliza-parent/cltl-eliza-app/py-app/storage/audio/debug/asr"

        if implementation == "google":
            from cltl.asr.google_asr import GoogleASR
            impl_config = self.config_manager.get_config("cltl.asr.google")
            asr = GoogleASR(impl_config.get("language"), impl_config.get_int("sampling_rate"),
                            hints=impl_config.get("hints", multi=True))
        elif implementation == "whisper":
            from cltl.asr.whisper_asr import WhisperASR
            impl_config = self.config_manager.get_config("cltl.asr.whisper")
            asr = WhisperASR(impl_config.get("model"), impl_config.get("language"), storage=storage)
        elif implementation == "speechbrain":
            from cltl.asr.speechbrain_asr import SpeechbrainASR
            impl_config = self.config_manager.get_config("cltl.asr.speechbrain")
            model = impl_config.get("model")
            asr = SpeechbrainASR(model, storage=storage)
        elif implementation == "wav2vec":
            from cltl.asr.wav2vec_asr import Wav2Vec2ASR
            impl_config = self.config_manager.get_config("cltl.asr.wav2vec")
            model = impl_config.get("model")
            asr = Wav2Vec2ASR(model, sampling_rate=sampling_rate, storage=storage)
        elif not implementation:
            asr = False
        else:
            raise ValueError("Unsupported implementation " + implementation)

        if asr:
            return AsrService.from_config(asr, self.emissor_data_client,
                                          self.event_bus, self.resource_manager, self.config_manager)
        else:
            logger.warning("No ASR implementation configured")
            return False

    def start(self):
        super().start()
        if self.asr_service:
            logger.info("Start ASR")
            self.asr_service.start()

    def stop(self):
        if self.asr_service:
            logger.info("Stop ASR")
            self.asr_service.stop()
        super().stop()


class HiTepRESTContainer(BackendContainer, InfraContainer):
    @property
    @singleton
    def hitep_rest_service(self) -> ChatUiService:
        return HiTepRESTService.from_config(self.audio_storage, self.event_bus, self.resource_manager, self.config_manager)

    def start(self):
        logger.info("Start HiTep REST service")
        super().start()
        self.hitep_rest_service.start()

    def stop(self):
        try:
            logger.info("Stop HiTep REST service")
            self.hitep_rest_service.stop()
        finally:
            super().stop()


class HiTepConvContainer(BrainContainer, InfraContainer):
    @property
    @singleton
    def hitep_conv_service(self) -> ChatUiService:
        return HiTepImportanceConvService.from_config(self.brain, self.event_bus, self.resource_manager, self.config_manager)

    def start(self):
        logger.info("Start HiTep Converstation service")
        super().start()
        self.hitep_conv_service.start()

    def stop(self):
        try:
            logger.info("Stop HiTep Converstation service")
            self.hitep_conv_service.stop()
        finally:
            super().stop()


class ApplicationContainer(HiTepConvContainer, HiTepRESTContainer, ChatUIContainer, BrainContainer,
                           ASRContainer, BackendContainer, EmissorStorageContainer):
    def __init__(self):
        pass

    @property
    @singleton
    def log_writer(self):
        config = self.config_manager.get_config("cltl.event_log")

        return LogWriter(config.get("log_dir"), serializer)

    @property
    @singleton
    def event_log_service(self):
        return EventLogService.from_config(self.log_writer, self.event_bus, self.config_manager)

    def start(self):
        logger.info("Start EventLog")
        super().start()
        self.event_log_service.start()

    def stop(self):
        try:
            time.sleep(1)
            logger.info("Stop EventLog")
            self.event_log_service.stop()
        finally:
            super().stop()


def serializer(obj):
    try:
        return emissor_serializer(obj)
    except Exception:
        try:
            return vars(obj)
        except Exception:
            return str(obj)


def main():
    ApplicationContainer.load_configuration()
    logger.info("Initialized Application")
    application = ApplicationContainer()
    with application as started_app:
        routes = {
            '/storage': started_app.storage_service.app,
            '/emissor': started_app.emissor_data_service.app,
            '/chatui': started_app.chatui_service.app,
            '/hitep': ASGIMiddleware(started_app.hitep_rest_service.app)
        }

        web_app = DispatcherMiddleware(Flask("HiTep app"), routes)

        run_simple('0.0.0.0', 8000, web_app, threaded=True, use_reloader=False, use_debugger=False, use_evalex=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hi=TEP app')
    args, _ = parser.parse_known_args()

    main()
