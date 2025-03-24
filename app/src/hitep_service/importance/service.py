import enum
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone

import importlib_resources as pkg_resources
from cltl.brain import LongTermMemory
from cltl.combot.event.emissor import TextSignalEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.commons.discrete import UtteranceType
from emissor.representation.scenario import TextSignal

import hitep_service.importance

logger = logging.getLogger(__name__)


class Ontology(enum.Enum):
    LEOLANI = "http://cltl.nl/leolani/friends/leolani"
    CAUSE = "http://semanticweb.cs.vu.nl/2009/11/sem/causes"
    TALK = "http://cltl.nl/leolani/talk/"


def read_query(query_filename):
    """
    Read a query from file and return as a string
    Parameters
    ----------
    query_filename: str name of the query. It will be looked for in the queries folder of this project

    Returns
    -------
    query: str the query with placeholders for the query parameters, as a string to be formatted

    """
    resources = pkg_resources.files(hitep_service.importance)

    return (resources / f"{query_filename}.rq").read_text()


class HiTepImportanceConvService:
    """
    Service used to integrate the component into applications.
    """
    @classmethod
    def from_config(cls, brain: LongTermMemory,
                    event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("hitep.importance")

        knowledge_topic = config.get("topic_knowledge")
        gaze_topic = config.get("topic_gaze")
        text_in_topic = config.get("topic_text_in")
        text_out_topic = config.get("topic_text_out")
        init_time = config.get_int("init_time")

        return cls(knowledge_topic, gaze_topic, text_in_topic, text_out_topic, init_time, brain, event_bus, resource_manager)

    def __init__(self, knowledge_topic: str, gaze_topic: str, text_in_topic: str, text_out_topic: str,
                 init_time: int, brain: LongTermMemory,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._brain = brain

        self._knowledge_topic = knowledge_topic
        self._gaze_topic = gaze_topic
        self._text_in_topic = text_in_topic
        self._text_out_topic = text_out_topic

        self._topic_worker = None
        self._app = None

        self._scenario_id = None
        self._active_painting = None
        self._active_start = None
        self._active_targets = None

        self._init_time = init_time

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._gaze_topic, self._text_in_topic], self._event_bus,
                                         provides=[self._text_out_topic],
                                         resource_manager=self._resource_manager, processor=self._process,
                                         scheduled=1)
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
        return None

    def _process(self, event: Event[TextSignalEvent]):
        # listen to painting events
        # after 20 sec query gaze event and find longest
        # Ask about longest, attach/relate utterances to gaze-event
        # Ask about shortest/related, attach/relate utterances to gaze-event
        if not self._active_painting and (not event or event.metadata.topic != self._gaze_topic):
            return

        if event and event.metadata.topic == self._gaze_topic and event.payload[0] == "start":
            if self._active_painting:
                self.stop_painting()

            self._scenario_id = event.payload[1]
            self._active_painting = event.payload[2]

            # TODO
            self._active_start = event.payload[3].timestamp() * 1000
            self._active_start = timestamp_now()
            logger.info("Painting %s turned active", self._active_painting)
        elif event and event.metadata.topic == self._gaze_topic and event.payload[0] == "end":
            logger.info("Painting %s turned inactive", self._active_painting)
            self.stop_painting()
        elif not event and self._active_targets is None and timestamp_now() - self._active_start > self._init_time:
            self._active_targets = []
            self._start_conversation()
            logger.info("Started conversation on painting %s", self._active_painting)
        elif event and event.metadata.topic == self._text_in_topic:
            self._handle_utterance(event.payload.signal)
            logger.debug("Handled utterance %s for painting %s", event.payload.signal.text, self._active_painting)
        else:
            logger.warning("Unhandled event %s", event)

    def _start_conversation(self):
        query = self._get_query(self._scenario_id, self._active_painting)
        # print(query)
        results = self._brain._submit_query(query)
        gazes = list(self._parse_gaze_results(results))
        logger.debug("Found gazes %s", gazes)

        if not gazes:
            self._active_start = timestamp_now()
            logger.debug("Reset conversation initialization %s", results)
            return

        durations = self._get_gaze_durations(gazes)
        most_important = durations.pop()
        gaze_target = most_important["target"].split("/")[-1]

        logger.debug("Found durations %s with most viewd %s", durations, most_important)

        utterance = f"Why are you looking at {gaze_target}"
        signal_id = self._send_response(utterance)
        self._utterance_capsule(signal_id, self._get_author(), most_important["target"], utterance)

        self._active_targets = ([durations[0]] if durations else [], most_important["target"])

    def _parse_gaze_results(self, sparql_results):
        # Initialize a dict to collect data per gaze IRI
        gazes = defaultdict(lambda: {
            'gaze': None,
            'target': None,
            'beginTimestamp': None,
            'endTimestamp': None,
            'duration': None
        })

        # Predicate URIs
        HAS_GAZE_TARGET = "http://github.com/hi-tep/gaze/hasGazeTarget"
        HAS_BEGIN_TIMESTAMP = "http://semanticweb.cs.vu.nl/2009/11/sem/hasBeginTimestamp"
        HAS_END_TIMESTAMP = "http://semanticweb.cs.vu.nl/2009/11/sem/hasEndTimestamp"

        # Process each triple
        for result in sparql_results:
            gaze_iri = result['gaze']['value']
            predicate = result['predicate']['value']
            obj_value = result['object']['value']

            # Make sure gaze IRI is recorded
            gaze = gazes[gaze_iri]
            gaze['gaze'] = gaze_iri

            # Assign fields based on predicate
            if predicate == HAS_GAZE_TARGET:
                gaze['target'] = obj_value
            elif predicate == HAS_BEGIN_TIMESTAMP:
                gaze['beginTimestamp'] = self._extract_timestamp(obj_value)
            elif predicate == HAS_END_TIMESTAMP:
                gaze['endTimestamp'] = self._extract_timestamp(obj_value)

            if gaze['beginTimestamp']:
                gaze['endTimestamp'] = datetime.now(timezone.utc) if not gaze['endTimestamp'] else gaze['endTimestamp']
                gaze['duration'] = (gaze['endTimestamp'] - gaze['beginTimestamp']).total_seconds()

        return gazes.values()

    def _extract_timestamp(self, iri):
        # Match ISO 8601 from IRI
        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)', iri)
        if match:
            return datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))

        return None

    def _get_gaze_durations(self, gazes):
        durations = defaultdict(lambda: {
            'target': None,
            'total': 0
        })

        for gaze in gazes:
            target = gaze["target"]
            target_gaze = durations[target]
            target_gaze['target'] = target
            target_gaze['total'] += gaze["duration"]

        return sorted(durations.values(), key=lambda x: x['total'])

    def _handle_utterance(self, text_signal):
        if self._active_targets and self._active_targets[0]:
            targets, gaze_iri = self._active_targets
            target = targets.pop()

            self._utterance_capsule(text_signal.id, self._get_author(), gaze_iri, text_signal.text)

            gaze_target = target["target"].split("/")[-1]
            utterance = f"Why did {gaze_target} not catch your attention?"
            self._send_response(utterance)
            self._utterance_capsule(text_signal.id, self._get_author(), gaze_iri, utterance)

    def stop_painting(self):
        self._active_targets = None
        self._active_painting = None
        self._active_start = None

    def _get_query(self, scenario_id, painting):
        query = read_query('./queries/gaze')
        query = query % {"painting": painting, "context": scenario_id}

        return query

    def _send_response(self, text):
        signal = TextSignal.for_scenario(self._scenario_id, timestamp_now(), timestamp_now(), None, text)

        payload = TextSignalEvent.for_agent(signal)
        self._event_bus.publish(self._text_out_topic, Event.for_payload(payload))

        return payload.signal.id

    def _utterance_capsule(self, signal_id, author, gaze_iri, text):
        capsule = {"chat": self._scenario_id,
                   "turn": signal_id,
                   "author": author,
                   "utterance": text,
                   "utterance_type": UtteranceType.STATEMENT,
                   "position": "0-" + str(len(text)),
                   "subject": {"label": "", "type": [], "uri": gaze_iri},
                   "predicate": {"label": "", "type": [], "uri": Ontology.CAUSE.value},
                   "object": {"label": "", "type": [], "uri": f"{Ontology.TALK.value}chat{self._scenario_id}_utterance{signal_id}"},
                   "perspective": {'certainty': 1.0, 'polarity': 1.0, 'sentiment': 0.0},
                   "context_id": self._scenario_id,
                   "timestamp": timestamp_now()
                   }
        self._event_bus.publish(self._knowledge_topic, Event.for_payload([capsule]))

    def _get_author(self):
        return {
            "label": "Leolani",
            "type": ["person"],
            "uri": Ontology.LEOLANI.value
        }