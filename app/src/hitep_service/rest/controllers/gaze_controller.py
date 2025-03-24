import enum
import hashlib
import uuid

from cltl.combot.infra.event import EventBus, Event
from cltl.commons.discrete import UtteranceType

from hitep.openapi_server.models import GazeDetection
from hitep_service.rest.controllers.chat_controller import ChatController
from hitep_service.rest.controllers.scenario_controller import ScenarioController, logger


class Ontology(enum.Enum):
    TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    EVENT = "http://semanticweb.cs.vu.nl/2009/11/sem/event"
    SUB_EVENT = "http://semanticweb.cs.vu.nl/2009/11/sem/subEventOf"
    CONTEXT = "http://cltl.nl/leolani/context/context"
    HAS_CONTEXT = "http://cltl.nl/episodicawareness/hasContext"
    ACTOR = "http://semanticweb.cs.vu.nl/2009/11/sem/hasActor"
    BEGIN = "http://semanticweb.cs.vu.nl/2009/11/sem/hasBeginTimestamp"
    END = "http://semanticweb.cs.vu.nl/2009/11/sem/hasEndTimestamp"
    GAZE = "http://github.com/hi-tep/gaze/gazeEvent"
    TARGET = "http://github.com/hi-tep/gaze/hasGazeTarget"
    HAS_DISTANCE = "http://github.com/hi-tep/gaze/hasDistance"
    IS_AT = "http://github.com/hi-tep/gaze/actorAtPosition"


class GazeController:
    def __init__(self, scenario_controller: ScenarioController, chat_controller: ChatController,
                 event_bus: EventBus, knowledge_topic: str):
        self._scenario_controller = scenario_controller
        self._chat_controller = chat_controller
        self._event_bus = event_bus
        self._knowledge_topic = knowledge_topic

        self._active_gaze = {}
        self._active_painting = None

    def add_gaze(self, scenario_id, gaze_detection: GazeDetection):  # noqa: E501
        current = self._scenario_controller.current
        if not current or current.id != scenario_id:
            return {"error": f"Scenario ID does not match, expected: {current and current.id}, actual: {scenario_id}"}, 400

        if self._knowledge_topic:
            if gaze_detection.end:
                capsules = self._create_experience_end(scenario_id, gaze_detection)
                self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

                if not gaze_detection.entities:
                    self._active_painting = None
                    painting_event = ["end", scenario_id, gaze_detection.painting, gaze_detection.end]
                    self._event_bus.publish("cltl.topic.painting", Event.for_payload(painting_event))

                print("XXX g", "end", gaze_detection.entities)
            elif gaze_detection.start:
                capsules = self._create_experience_start(scenario_id, gaze_detection)
                self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

                if not gaze_detection.entities:
                    self._active_painting = gaze_detection.painting
                    painting_event = ["start", scenario_id, gaze_detection.painting, gaze_detection.start]
                    self._event_bus.publish("cltl.topic.painting", Event.for_payload(painting_event))

                print("XXX g", "start", gaze_detection.entities)
            else:
                logger.warning("Received gaze event without start and end date")

    def _create_experience_start(self, scenario_id, gaze: GazeDetection):
        user = self._scenario_controller.current.context.speaker.uri

        if gaze.entities:
            triples = [caps for entity in gaze.entities for caps in self._create_triples_start(scenario_id, user, entity, gaze)]
        else:
            triples = self._create_triples_start(scenario_id, user, None, gaze)

        return [triple.to_dict() for triple in triples]

    def _create_triples_start(self, scenario_id, user, entity, gaze: GazeDetection):
        detection = self._scenario_controller.next_counter()
        gaze_event = f"{Ontology.GAZE.value}/{uuid.uuid4()}"

        triples = [Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.TYPE.value, Ontology.EVENT.value),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.HAS_CONTEXT.value, f"{Ontology.CONTEXT.value}{scenario_id}"),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.ACTOR.value, user),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.BEGIN.value, gaze.start.isoformat(timespec='milliseconds')),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.TARGET.value, gaze.painting),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.HAS_DISTANCE.value, str(gaze.distance)),
                   Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.IS_AT.value, str(gaze.position)),
                   ]

        if entity:
            triples.append(Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.TARGET.value, entity.iri))

        gaze_key = hashlib.md5(f"{scenario_id}%{gaze.painting}%{entity}".encode("utf")).hexdigest()
        self._active_gaze[gaze_key] = (detection, gaze_event)

        return triples

    def _create_experience_end(self, scenario_id, gaze: GazeDetection):
        triples = [caps for entity in gaze.entities for caps in self._create_triples_end(scenario_id, entity, gaze)]

        return [triple.to_dict() for triple in triples]

    def _create_triples_end(self, scenario_id, entity, gaze: GazeDetection):
        gaze_key = hashlib.md5(f"{scenario_id}%{gaze.painting}%{entity}".encode("utf")).hexdigest()
        detection, gaze_event = self._active_gaze[gaze_key]
        del self._active_gaze[gaze_key]

        triples = [Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.END.value, gaze.end.isoformat(timespec='milliseconds'))]

        return triples


# class HirarchicGazeRegistry:
#     def __init__(self):
#         self._gaze = dict()
#         self._parents = []
#
#     def active(self) -> str:
#         """Get the id of the active gaze event."""
#         active_parents = self.get_parent_events()
#
#         return active_parents[-1] if active_parents else None
#
#     def start(self, scenario_id: str, gaze: GazeDetection) -> Tuple[str, List[str]]:
#         """Start a new gaze event. Return the new Id (and parents?)
#         """
#         active_parents = self.get_parent_events()
#         parent = next(filter(self._includes_filter(gaze.entities), active_parents), None)
#         parents = active_parents[:indexOf(parent, active_parents)] if parent else []
#
#         gaze_id = hashlib.md5(f"{scenario_id}%{gaze.painting}%{gaze.entities}".encode("utf")).hexdigest()
#         self._gaze[gaze_id] = gaze
#
#         return gaze_id, parents
#
#     def end(self, scenario_id: str, gaze: GazeDetection):
#         """End the gaze event, Return the parent(s)"""
#         active_parents = self.get_parent_events()
#         gaze_id = hashlib.md5(f"{scenario_id}%{gaze.painting}%{gaze.entities}".encode("utf")).hexdigest()
#         del self._gaze[gaze_id]
#         self._parents.pop()
#
#     def get_parent_events(self, event_id) -> List[str]:
#         """Return the parent events"""
#         return self._parents[:-1]
#
#     def _includes_filter(self, entities):
#         return lambda gaze: (gaze.entities | entities) == entities


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
            "subject": {'label': self._to_label(self.subject), 'type': [], 'uri': self.subject},
            "predicate": {"label": self._to_label(self.predicate), "uri": self.predicate},
            "object": ({'label': self._to_label(self.object), 'type': [], 'uri': self.object}),
            "perspective": {"certainty": 1, "polarity": 1, "sentiment": 0},
            'confidence': 1.00,
            "timestamp": self.date,
            "context_id": self.scenario_id
        }

    def _to_label(self, uri):
        if "http" not in uri:
            return uri
        else:
            return ""
        # return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
