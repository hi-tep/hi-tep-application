import argparse
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from attr import dataclass

from hitep_service.rest.handlers.encoder import JSONEncoder
from hitep.openapi_server.models import GazeDetection, Model3DCoordinate, Entity, ScenarioContext

logger = logging.getLogger(__name__)


DEFAULT_CONTEXT = ScenarioContext(location="https://example.com/ontology/museum/twente", user="https://example.com/ontology/alice")


class RESTScenario:
    def __init__(self, url, scenario_data):
        self._url = url
        self._scenario_data = scenario_data

        self.json = JSONEncoder()

    def resolve(self, path):
        return urljoin(self._url, path)

    def to_dict(self, obj):
        return json.loads(self.json.dumps(obj))

    def start_scenario(self, scenario_id, data=DEFAULT_CONTEXT):
        url = self.resolve(f"scenario/{scenario_id}")
        data_dict = self.to_dict(data)

        logger.debug("Starting scenario %s at %s: %s", scenario_id, url, data_dict)
        response = requests.put(url, json=data_dict)
        logger.info("Scenario %s started: %s [%s]", scenario_id, response, response.text)

    def stop_scenario(self, scenario_id, end):
        url = self.resolve(f"scenario/{scenario_id}/stop")
        data_dict = self.to_dict({"end": end})

        logger.info("Stoppinbg scenario %s at %s: %s", scenario_id, url, data_dict)
        response = requests.post(url, json=data_dict)
        logger.info("Scenario %s stopped: %s [%s]", scenario_id, response, response.text)

    def gaze_detection(self, scenario_id, gaze_data):
        url = self.resolve(f"scenario/{scenario_id}/gaze")
        data_dict = self.to_dict(gaze_data)

        logger.info("Sending gaze for scenario %s to %s: %s", scenario_id, url, data_dict)
        response = requests.post(url, json=data_dict)
        logger.info("Gaze posted for scenario %s: %s [%s]", scenario_id, response, response.text)

    def run(self):
        for action, args, wait in self._scenario_data:
            fct = getattr(self, action)
            fct(*args)


@dataclass
class GazeDetectionData:
    position: Model3DCoordinate
    painting: str
    distance: float
    entities: List[Entity]
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    def to_start(self):
        self.start = self.start if self.start else datetime.now()
        return GazeDetection(position=self.position, distance=self.distance,
                             painting=self.painting, entities=self.entities,
                             start=self.start)

    def to_end(self):
        self.end = self.end if self.end else datetime.now()
        return GazeDetection(position=self.position, distance=self.distance,
                             painting=self.painting, entities=self.entities,
                             start=self.start, end=self.end)


SCENARIO_ID = str(uuid.uuid4())

GAZE_DETECTIONS = [
    GazeDetectionData(position=Model3DCoordinate(0, 0, 0), distance=1.0,
                  entities=[Entity(iri="http://vrmtwente.nl/jar1")],
                  painting="http://vrmtwente.nl/painting1"),
    GazeDetection(position=Model3DCoordinate(0, 0, 0), distance=1.0,
                  entities=[Entity(iri="http://vrmtwente.nl/jar1"), Entity(iri="http://vrmtwente.nl/king-george")],
                  painting="http://vrmtwente.nl/painting1"),
]

SCENARIO1 = [
    (RESTScenario.start_scenario.__name__, (SCENARIO_ID,), 0.1),
    (RESTScenario.gaze_detection.__name__, (SCENARIO_ID, GAZE_DETECTIONS[0].to_start()), 0.1),
    (RESTScenario.gaze_detection.__name__, (SCENARIO_ID, GAZE_DETECTIONS[0].to_end()), 0.1),
    (RESTScenario.stop_scenario.__name__, (SCENARIO_ID, datetime.now()), 0.1),
]

def main(url):
    test_scenario = RESTScenario(url, SCENARIO1)
    test_scenario.run()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hi=TEP app test')
    parser.add_argument('--url', type=str, default="http://localhost:8000/hitep/", help='Server URL.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Server URL.')
    args, _ = parser.parse_known_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    main(args.url)