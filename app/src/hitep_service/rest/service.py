import datetime
import logging
import os.path

import connexion
from cltl.combot.event.emissor import TextSignalEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from connexion.jsonifier import Jsonifier
from connexion.resolver import MethodViewResolver
from flask import request

from hitep_service.rest.controllers.audio_controller import AudioController
from hitep_service.rest.controllers.chat_controller import ChatController
from hitep_service.rest.controllers.position_controller import PositionController
from hitep_service.rest.handlers.encoder import JSONEncoder
from hitep_service.rest.controllers.gaze_controller import GazeController
from hitep_service.rest.controllers.scenario_controller import ScenarioController

logger = logging.getLogger(__name__)


class ConnexionEncoder(Jsonifier):
    def __init__(self, encoder):
        self._encoder = encoder

    def jsonify(self, obj):
        return self._encoder(obj)


class HiTepRESTService:
    """
    Service used to integrate the component into applications.
    """
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("hitep.rest")

        scenario_topic = config.get("topic_scenario")
        knowledge_topic = config.get("topic_knowledge") if "topic_knowledge" in config else None
        request_log = config.get("request_log") if "request_log" in config else None
        audio_log = config.get("audio_log") if "audio_log" in config else None

        return cls(knowledge_topic, scenario_topic, request_log, audio_log, event_bus, resource_manager)

    def __init__(self, knowledge_topic: str, scenario_topic: str, request_log: str, audio_log: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._knowledge_topic = knowledge_topic
        self._scenario_topic = scenario_topic

        self._scenario_controller = ScenarioController(self._event_bus, self._scenario_topic, self._knowledge_topic)
        self._chat_controller = ChatController(self._scenario_controller)
        self._gaze_controller = GazeController(self._scenario_controller, self._chat_controller, self._event_bus, self._knowledge_topic)
        self._position_controller = PositionController(self._scenario_controller, self._chat_controller, self._event_bus, self._knowledge_topic)
        self._audio_controller = AudioController(audio_log, self._scenario_controller, self._event_bus)

        self._topic_worker = None
        self._app = None
        self._request_log = request_log

        self._scenario = None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._scenario_topic], self._event_bus, provides=[self._knowledge_topic],
                                         resource_manager=self._resource_manager, processor=self._process)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    @property
    def scenario(self):
        # TODO thread-safty
        return self._scenario

    @scenario.setter
    def scenario(self, scenario):
        self._scenario = scenario

    @property
    def app(self):
        """
        Flask endpoint for REST interface.
        """
        if self._app:
            return self._app

        self._app = connexion.App(__name__, resolver=MethodViewResolver('hitep_service.rest.handlers',
                            class_arguments={
                                "ScenarioView": {"kwargs": {"controller": self._scenario_controller}},
                                "CurrentView": {"kwargs": {"controller": self._scenario_controller}},
                                "StopView": {"kwargs": {"controller": self._scenario_controller}},
                                "GazeView": {"kwargs": {"controller": self._gaze_controller}},
                                "PositionchangeView": {"kwargs": {"controller": self._position_controller}},
                                "AudioView": {"kwargs": {"controller": self._audio_controller}},
                                "LatestView": {"kwargs": {"controller": self._chat_controller}},
                            }), jsonifier=JSONEncoder())
        # self._app.add_api('https://raw.githubusercontent.com/hi-tep/tep-rest-api/refs/heads/main/leolani-tep-api.yaml', pythonic_params=True)
        self._app.add_api(os.path.join(os.getcwd(), 'leolani-tep-api.yaml'), pythonic_params=True)

        @self._app.app.after_request
        def set_cache_control(response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

            return response

        @self._app.app.before_request
        def request_log():
            if self._request_log:
                headers = request.headers
                # TODO check content length
                if request.method == "GET":
                    body = "GET"
                else:
                    body = (request.get_data().decode('utf-8')
                            if "Content-Type" in headers and headers["Content-Type"] == "application/json"
                            else headers["Content-Type"] if "Content-Type" in headers else "Unknown Content-Type")
                path = request.path

                with open(self._request_log, 'a') as logfile:
                    logfile.writelines(f"{datetime.datetime.now().isoformat()}\n{path}\n{headers}| {body}\n\n")

        return self._app

    def _process(self, event: Event[TextSignalEvent]):
        pass
