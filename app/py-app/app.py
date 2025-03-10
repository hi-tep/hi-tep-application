import argparse
import logging.config
import logging.config
import os
import pathlib
import time

from a2wsgi import ASGIMiddleware
from cltl.brain import LongTermMemory
from cltl.chatui.api import Chats
from cltl.chatui.memory import MemoryChats
from cltl.combot.infra.config.k8config import K8LocalConfigurationContainer
from cltl.combot.infra.di_container import singleton
from cltl.combot.infra.event.memory import SynchronousEventBusContainer
from cltl.combot.infra.event_log import LogWriter
from cltl.combot.infra.resource.threaded import ThreadedResourceContainer
from cltl.emissordata.api import EmissorDataStorage
from cltl.emissordata.file_storage import EmissorDataFileStorage
from cltl_service.brain.service import BrainService
from cltl_service.chatui.service import ChatUiService
from cltl_service.combot.event_log.service import EventLogService
from cltl_service.emissordata.client import EmissorDataClient
from cltl_service.emissordata.service import EmissorDataService
from emissor.representation.util import serializer as emissor_serializer
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

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


class HiTepRESTContainer(InfraContainer):
    @property
    @singleton
    def hitep_rest_service(self) -> ChatUiService:
        return HiTepRESTService.from_config(self.event_bus, self.resource_manager, self.config_manager)

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


class ApplicationContainer(HiTepRESTContainer, ChatUIContainer, BrainContainer, EmissorStorageContainer):
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
