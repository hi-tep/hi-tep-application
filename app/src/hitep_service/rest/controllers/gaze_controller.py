import enum
import hashlib
import itertools
from threading import Timer

from cltl.combot.infra.event import EventBus, Event
from cltl.commons.discrete import UtteranceType

from hitep.openapi_server.models import GazeDetection
from hitep_service.rest.controllers.chat_controller import ChatController
from hitep_service.rest.controllers.scenario_controller import ScenarioController


class Predicate(enum.Enum):
    GAZE = "gaze"
    HAS_DISTANCE = "has-distance"
    IS_AT = "is-at"


class GazeController:
    def __init__(self, scenario_controller: ScenarioController, chat_controller: ChatController,
                 event_bus: EventBus, knowledge_topic: str):
        self._scenario_controller = scenario_controller
        self._chat_controller = chat_controller
        self._event_bus = event_bus
        self._knowledge_topic = knowledge_topic

        self._counter = None

        self._active_gaze = {}

    def add_gaze(self, scenario_id, gaze_detection: GazeDetection):  # noqa: E501
        current = self._scenario_controller.current
        if not current or current.id != scenario_id:
            raise ValueError(f"Scenario ID does not match, expected: {current and current.id}, actual: {scenario_id}")

        capsules = self._create_experience(scenario_id, gaze_detection)

        # pprint(capsules, indent=4)
        self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

    def _create_experience(self, scenario_id, gaze: GazeDetection):
        user = self._scenario_controller.current.context.speaker.uri
        if not self._counter or scenario_id not in self._counter:
            self._counter = {scenario_id: itertools.count()}

        # TODO Threadsafty
        detection = next(self._counter[scenario_id])

        triples = [caps for entity in gaze.entities for caps in self._create_triples(scenario_id, detection, user, entity, gaze)]
        triples.extend(self._create_triples(scenario_id, detection, user, None, gaze))

        gaze_id = hashlib.md5(f"{scenario_id}%{gaze.painting}%{gaze.entities}".encode("utf")).hexdigest()

        if gaze.end:
            # Add end timestamp to triples
            del self._active_gaze[gaze_id]
        else:
            self._active_gaze[gaze_id] = gaze
            def set_latest(gaze_id):
                active_gaze = self._active_gaze.get(gaze_id)
                if gaze:
                    text = ", ".join(ent.iri.split("/")[-1] for ent in active_gaze.entities)
                    utterance = f"You looked at {text} in {gaze.painting.split('/')[-1]}"
                    self._chat_controller.set_latest(utterance)
            Timer(interval=1, function=set_latest, args=(gaze_id,)).start()

        return [triple.to_dict() for triple in triples]

    def _create_triples(self, scenario_id, detection, user, entity, gaze: GazeDetection):
        triples = [Triple(scenario_id, detection, gaze.start, user, Predicate.GAZE.value, gaze.painting),]
                   # Triple(scenario_id, detection, gaze.start, user, Predicate.HAS_DISTANCE.value, gaze.distance),
                   # Triple(scenario_id, detection, gaze.start, user, Predicate.IS_AT.value, gaze.position)]

        if entity:
            triples.append(Triple(scenario_id, detection, gaze.start, user, Predicate.GAZE.value, entity.iri))

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
                       "uri": "http://cltl.nl/leolani/inputs/hitep/rest/gaze"},
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
