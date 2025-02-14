from pprint import pprint

from cltl.combot.infra.event import EventBus, Event
from cltl.commons.discrete import UtteranceType

from hitep.openapi_server.models import GazeDetection


class GazeController:
    def __init__(self, scenario_controller, event_bus: EventBus, knowledge_topic: str):
        self._scenario_controller = scenario_controller
        self._event_bus = event_bus
        self._knowledge_topic = knowledge_topic

    def add_gaze(self, scenario_id, gaze_detection: GazeDetection):  # noqa: E501
        current = self._scenario_controller.current
        if not current or current.id != scenario_id:
            raise ValueError(f"Scenario ID does not match, expected: {current and current.id}, actual: {scenario_id}")

        capsule = self._create_triples(scenario_id, gaze_detection.start, gaze_detection.start)

        pprint(capsule, indent=4)
        self._event_bus.publish('cltl.topic.knowledge', Event.for_payload(capsule[1]))

    def _create_triples(self, context_id, start_date, triples):
        return [
                       {
                           "visual": 1,
                           "detection": 1,
                           "source": {"label": "front-camera", "type": ["sensor"],
                                      'uri': "http://cltl.nl/leolani/inputs/front-camera"},
                           "image": None,
                           "utterance_type": UtteranceType.EXPERIENCE_TRIPLE,
                           "region": [752, 46, 1148, 716],
                           "item": {'label': 'chair 1', 'type': ['chair'], 'id': 1,
                                    'uri': "http://cltl.nl/leolani/world/chair-1"},
                           "subject": {'label': 'chair 1', 'type': ['chair'], 'id': 1,
                                    'uri': "http://cltl.nl/leolani/world/chair-1"},
                           "predicate": {"label": "be-in", 'id': 1, "uri": "http://cltl.nl/leolani/n2mu/be-in"},
                           "object": {"label": "Piek's office", "type": ["location"], 'id': 1,
                                      "uri": "http://cltl.nl/leolani/world/pieks-office"},
                           "perspective": {"certainty": 68,
                                           "polarity": 1,
                                           "sentiment": 0
                                           },

                           'confidence': 0.68,
                           "timestamp": start_date,
                           "context_id": context_id
                       },
                       {
                           "visual": 1,
                           "detection": 2,
                           "source": {"label": "front-camera", "type": ["sensor"],
                                      'uri': "http://cltl.nl/leolani/inputs/front-camera"},
                           "image": None,
                           "utterance_type": UtteranceType.EXPERIENCE_TRIPLE,
                           "region": [752, 46, 1148, 716],
                           "item": {'label': 'apple 1', 'type': ['fruit'], 'id': 1,
                                    'uri': "http://cltl.nl/leolani/world/apple-1"},
                           "subject": {'label': 'apple 1', 'type': ['fruit'],
                                    'uri': "http://cltl.nl/leolani/world/apple-1"},
                           "predicate": {"label": "be-in", "uri": "http://cltl.nl/leolani/n2mu/be-in"},
                           "object": {"label": "Piek's office", "type": ["location"],
                                      "uri": "http://cltl.nl/leolani/world/pieks-office"},
                           "perspective": {"certainty": 68,
                                           "polarity": 1,
                                           "sentiment": 0
                                           },
                           'confidence': 0.98,
                           "timestamp": start_date,
                           "context_id": context_id
                       },
                       {
                           "visual": 1,
                           "detection": 2,
                           "source": {"label": "front-camera", "type": ["sensor"],
                                      'uri': "http://cltl.nl/leolani/inputs/front-camera"},
                           "image": None,
                           "utterance_type": UtteranceType.EXPERIENCE_TRIPLE,
                           "region": [752, 46, 1700, 716],
                           "item": {'label': 'Carl', 'type': ['person'], 'id': None,
                                    'uri': "http://cltl.nl/leolani/world/carl-1"},
                           "subject": {'label': 'Carl', 'type': ['person'],
                                    'uri': "http://cltl.nl/leolani/world/carl-1"},
                           "predicate": {"label": "be-in", "uri": "http://cltl.nl/leolani/n2mu/be-in"},
                           "object": {"label": "Piek's office", "type": ["location"],
                                      "uri": "http://cltl.nl/leolani/world/pieks-office"},
                           "perspective": {"certainty": 68,
                                           "polarity": 1,
                                           "sentiment": 0
                                           },
                           'confidence': 0.94,
                           "timestamp": start_date,
                           "context_id": context_id
                       }
                   ]

class Triple:
    def __init__(self, scenario_id, date, item, subject, predicate, object):
        self.scenario_id = scenario_id
        self.date = date
        self.item = item
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def to_dict(self, triple):
        return {
            "visual": 1,
            "detection": 1,
            "source": {"label": "HiTep REST gaze", "type": ["sensor"],
                       'uri': "http://cltl.nl/leolani/inputs/hhitep/rest/gaze"},
            "image": None,
            "utterance_type": UtteranceType.EXPERIENCE_TRIPLE,
            "region": [0, 0, 0, 0],
            "item": self.item,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "perspective": {"certainty": 1, "polarity": 1, "sentiment": 0},
            'confidence': 1.00,
            "timestamp": self.date,
            "context_id": self.scenario_id
        }
