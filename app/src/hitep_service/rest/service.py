import logging
import uuid
from typing import Union

import connexion
from connexion import RestyResolver
from flask import Response

from cltl.combot.event.emissor import TextSignalEvent, ScenarioStarted
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from emissor.representation.scenario import TextSignal, Scenario, Modality
from hitep_service.rest.controllers.api import Source, PaintingExperience, Entity
from hitep_service.rest.openapi.models import GazeDetection, ScenarioContext

from openapi_server.encoder import JSONEncoder

logger = logging.getLogger(__name__)


class HiTepRESTService:
    """
    Service used to integrate the component into applications.
    """
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.template")

        scenario_topic = config.get("topic_scenario") if "topic_scenario" in config else None

        return cls(config.get("topic_knowledge"), scenario_topic, event_bus, resource_manager)

    def __init__(self, knowledge_topic: str, scenario_topic: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._knowledge_topic = knowledge_topic
        self._scenario_topic = scenario_topic

        self._topic_worker = None
        self._app = None

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
    def app(self):
        """
        Flask endpoint for REST interface.
        """
        if self._app:
            return self._app

        app = connexion.App(__name__, resolver=RestyResolver('hitep_service.rest.controllers'))
        app.add_api('openapi.yaml', pythonic_params=True)
        app.app.json_encoder = JSONEncoder

        # # Retrieve the parsed OpenAPI specification
        # openapi_spec = api.specification
        # for path, path_item in openapi_spec["paths"].items():
        #     for method, operation in path_item.items():
        #         if method in ["get", "post", "put", "delete", "patch"]:
        #             operation_id = operation.get("operationId")
        #             if hasattr(self, operation_id):
        #                 view_func = getattr(self, operation_id)
        #                 app.add_url_rule(
        #                     path.replace("{", "<").replace("}", ">"),
        #                     endpoint=operation_id,
        #                     view_func=view_func,
        #                     methods=[method.upper()]
        #                 )

        @self._app.after_request
        def set_cache_control(response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

            return response

        return self._app

    def submit_gaze(self, scenario_id: str, gaze_detection: Union[dict, bytes]):  # noqa: E501
        """Submit gaze information of the user

        The event marks a conscious gaze of the user on the submitted entities in the painting. # noqa: E501

        :param scenario_id: The unique identifier for the interaction
        :param gaze_detection:
        """
        if connexion.request.is_json:
            gaze_detection = GazeDetection.from_dict(connexion.request.get_json())

        self._event_bus.publish(Event.for_payload(self._experience_from_gaze(scenario_id, gaze_detection)))

    def _experience_from_gaze(self, scenario_id, gaze):
        gaze_id = str(uuid.uuid4())
        source = Source(None, ["person"], self._scenario.user)
        for entity in gaze.entities:
            return PaintingExperience(gaze.painting, gaze_id, source, None, gaze.bounding_box,
                         Entity(**(entity.to_dict() | {"id": None})),
                         1.0, scenario_id, timestamp_now())

    def current_scenario(self) -> Union[ScenarioContext, Response]:
        """Retrieve the current interaction ID"""
        if self._scenario:
            return self._scenario

        return Response(status=404)

    def get_scenario(self, scenario_id: str) -> Union[ScenarioContext, Response]:
        """Retrieve an interaction by ID"""
        if self._scenario.id == scenario_id:
            return self._scenario

        # TODO stopped scenarios
        return Response(status=401)

    def start_scenario(self, scenario_id: str, scenario_context: ScenarioContext) -> ScenarioContext:
        """Start a new interaction"""
        if connexion.request.is_json:
            scenario_context = ScenarioContext.from_dict(connexion.request.get_json())  # noqa: E501

        signals = {Modality.TEXT.name: "./emissor/text.json"}
        self.scenario = Scenario.new_instance(scenario_id, timestamp_now(), None, scenario_context, signals)
        self._event_bus.publish(self._scenario_topic, Event.for_payload(ScenarioStarted.create(self._scenario)))

        return self.scenario

    def _process(self, event: Event[TextSignalEvent]):
        pass
