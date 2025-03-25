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
    EVENT = "http://semanticweb.cs.vu.nl/2009/11/sem/Event"
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
            if gaze_detection.start:
                capsules = self._create_experience_start(scenario_id, gaze_detection)
                self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

                if not gaze_detection.entities:
                    self._active_painting = gaze_detection.painting
                    painting_event = ["start", scenario_id, gaze_detection.painting, gaze_detection.start]
                    self._event_bus.publish("cltl.topic.painting", Event.for_payload(painting_event))

                logger.debug("Detected gaze start on %s", gaze_detection.entities)
            elif gaze_detection.end:
                capsules = self._create_experience_end(scenario_id, gaze_detection)
                self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsules))

                if not gaze_detection.entities:
                    self._active_painting = None
                    painting_event = ["end", scenario_id, gaze_detection.painting, gaze_detection.end]
                    self._event_bus.publish("cltl.topic.painting", Event.for_payload(painting_event))

                logger.debug("Detected gaze end on %s", gaze_detection.entities)
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
        gaze_key = self._to_gaze_key(entity, gaze, scenario_id)

        # Gaze on entity already started
        if gaze_key in self._active_gaze:
            det, ev, cnt = self._active_gaze[gaze_key]
            self._active_gaze[gaze_key] = (det, ev, cnt + 1)

            return []

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
            # TODO Fix for demo, VRM doesn't transfer URIs
            painting_label = gaze.painting.split("/")[-1]
            entity_iri = (entity.iri if entity.iri.startswith("http://")
                          else f"http://vrmtwente.nl/{painting_label}/{entity.iri}")
            triples.append(Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.TARGET.value, entity_iri))

        self._active_gaze[gaze_key] = (detection, gaze_event, 1)

        return triples

    def _create_experience_end(self, scenario_id, gaze: GazeDetection):
        triples = [caps for entity in gaze.entities for caps in self._create_triples_end(scenario_id, entity, gaze)]

        return [triple.to_dict() for triple in triples]

    def _create_triples_end(self, scenario_id, entity, gaze: GazeDetection):
        try:
            gaze_key = self._to_gaze_key(entity, gaze, scenario_id)
            detection, gaze_event, cnt = self._active_gaze[gaze_key]
        except KeyError:
            logger.warning("No active gaze found for %s", gaze)
            return

        if cnt == 1:
            del self._active_gaze[gaze_key]
            triples = [Triple(scenario_id, detection, gaze.start, gaze_event, Ontology.END.value,
                              gaze.end.isoformat(timespec='milliseconds'))]
        else:
            det, ev, cnt = self._active_gaze[gaze_key]
            self._active_gaze[gaze_key] = (det, ev, cnt - 1)
            triples = []

        return triples

    def _to_gaze_key(self, entity, gaze, scenario_id: str):
        entity_str = ''.join(str(entity).split()) if entity else ''
        painting_str = ''.join(str(gaze.painting).split())

        return hashlib.md5(f"{scenario_id.strip()}%{painting_str}%{entity_str}".encode("utf-8")).hexdigest()


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
            "subject": {'label': self._to_label(self.subject), 'type': self._get_type(self.subject), 'uri': self.subject},
            "predicate": {"label": self._to_label(self.predicate), "uri": self.predicate},
            "object": ({'label': self._to_label(self.object), 'type': self._get_type(self.object), 'uri': self.object}),
            "perspective": {"certainty": 1, "polarity": 1, "sentiment": 0},
            'confidence': 1.00,
            "timestamp": self.date,
            "context_id": self.scenario_id
        }

    def _get_type(self, entity: str):
        return ['class'] if entity.startswith("http://") else []

    def _to_label(self, uri):
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
