import enum
import hashlib
import itertools
from threading import Timer

from cltl.combot.infra.event import EventBus, Event
from cltl.commons.discrete import UtteranceType

from hitep.openapi_server.models import GazeDetection
from hitep_service.rest.controllers.chat_controller import ChatController
from hitep_service.rest.controllers.scenario_controller import ScenarioController
from hitep.openapi_server.models.position_change import PositionChange


class Predicate(enum.Enum):
    MOVED_FROM = "moved-to"
    MOVED_TO = "moved-from"


class PositionController:
    def __init__(self, scenario_controller: ScenarioController, chat_controller: ChatController,
                 event_bus: EventBus, knowledge_topic: str):
        self._scenario_controller = scenario_controller
        self._chat_controller = chat_controller
        self._event_bus = event_bus
        self._knowledge_topic = knowledge_topic

        self._counter = None

        self._active_gaze = {}

    def add_position_change(self, scenario_id, position_change: PositionChange):  # noqa: E501
        current = self._scenario_controller.current
        if not current or current.id != scenario_id:
            return {"error": f"Scenario ID does not match, expected: {current and current.id}, actual: {scenario_id}"}, 400

        capsules = self._create_experience(scenario_id, position_change)

        # pprint(capsules, indent=4)
        self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

    def _create_experience(self, scenario_id, position_change: PositionChange):
        user = self._scenario_controller.current.context.speaker.uri
        if not self._counter or scenario_id not in self._counter:
            self._counter = {scenario_id: itertools.count()}

        # TODO Threadsafty
        detection = self._scenario_controller.next_counter()

        triples = self._create_triples(scenario_id, detection, user, None, position_change)

        utterance = f"You moved from {position_change.previous} in {position_change.current}"
        self._chat_controller.set_latest(utterance)

        return [triple.to_dict() for triple in triples]

    def _create_triples(self, scenario_id, detection, user, entity, position_change: PositionChange):
        triples = [Triple(scenario_id, detection, position_change.timestamp, user, Predicate.MOVED_FROM.value,
                          f"https://cltl.nl/leolani/position/{position_change.previous}"),
                   Triple(scenario_id, detection, position_change.timestamp, user, Predicate.MOVED_TO.value,
                          f"https://cltl.nl/leolani/position/{position_change.current}")]

        return triples


class Triple:
    def __init__(self, scenario_id, detection, date, subject, predicate, object):
        self.scenario_id = scenario_id
        self.detection = detection
        self.date = date
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def to_dict(self):
        return {
            "visual": self.scenario_id,
            "detection": self.detection,
            "source": {"label": "HiTep REST gaze", "type": ["sensor"],
                       "uri": "http://cltl.nl/leolani/inputs/hitep/rest/position"},
            "image": None,
            "utterance_type": UtteranceType.EXPERIENCE_TRIPLE,
            "region": [0, 0, 0, 0],
            "item": None,
            "subject": {'label': self.subject.split("/")[-1], 'type': [], 'uri': self.subject},
            "predicate": {"label": "self.predicate", "uri": f"http://cltl.nl/leolani/hitep/{self.predicate}"},
            "object": ({'label': self.object.split("/")[-1], 'type': [], 'uri': self.object}),
            "perspective": {"certainty": 1, "polarity": 1, "sentiment": 0},
            'confidence': 1.00,
            "timestamp": self.date,
            "context_id": self.scenario_id
        }
