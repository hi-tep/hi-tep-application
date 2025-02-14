import logging
import uuid
from datetime import datetime, timezone

import requests
from cltl.combot.event.emissor import ScenarioStarted, ScenarioStopped, Agent
from cltl.combot.infra.event import Event
from cltl.combot.infra.time_util import timestamp_now
from emissor.representation.ldschema import emissor_dataclass
from emissor.representation.scenario import Modality, Scenario, ScenarioContext

import hitep.openapi_server.models as models

logger = logging.getLogger(__name__)


AGENT = Agent("Leolani", "http://cltl.nl/leolani/world/leolani")


@emissor_dataclass
class HiTepContext(ScenarioContext):
    agent: Agent
    speaker: Agent
    location_id: str
    location: str


class ScenarioController:
    def __init__(self, event_bus, scenario_topic, knowledge_topic):
        self._event_bus = event_bus
        self._scenario_topic = scenario_topic
        self._knowledge_topic = knowledge_topic

        self._scenario = None

    @property
    def current(self):
        return self._scenario

    def start_scenario(self, context: models.ScenarioContext):
        scenario, capsule = self._create_scenario(context)
        self._event_bus.publish(self._scenario_topic, Event.for_payload(ScenarioStarted.create(scenario)))
        self._event_bus.publish(self._knowledge_topic, Event.for_payload([capsule]))
        self._scenario = scenario
        logger.info("Started scenario %s", scenario)

    def stop_scenario(self, timestamp):
        self._scenario.ruler.end = timestamp if timestamp else timestamp_now()
        self._event_bus.publish(self._scenario_topic,
                                Event.for_payload(ScenarioStopped.create(self._scenario)))
        logger.info("Stopped scenario %s", self._scenario)

    def _create_scenario(self, context: models.ScenarioContext):
        signals = {
            Modality.TEXT.name.lower(): "./text.json",
            Modality.AUDIO.name.lower(): "./audio.json"
        }

        scenario_start = int(context.start.timestamp() * 1000) if context.start else timestamp_now()
        location = context.location if context.location else self._get_location()
        user = Agent(context.user.split("/")[-1], context.user)

        scenario_context = HiTepContext(AGENT, user, str(uuid.uuid4()), location)
        scenario = Scenario.new_instance(context.id if context.id else str(uuid.uuid4()),
                                         scenario_start, None, scenario_context, signals)

        capsule = {
            "type": "context",
            "context_id": scenario.id,
            "date": datetime.fromtimestamp(scenario_start // 1000, timezone.utc).isoformat(),
            "place": None,
            "place_id": location,
            "country": "",
            "region": "",
            "city": ""
        }

        return scenario, capsule

    def _get_location(self):
        try:
            return requests.get("https://ipinfo.io").json()
        except:
            return {"country": "", "region": "", "city": ""}

