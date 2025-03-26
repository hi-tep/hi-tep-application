import itertools
import logging
import uuid
from datetime import datetime, timezone
from threading import Lock, RLock
from typing import Optional

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


class ScenarioController:
    def __init__(self, event_bus, scenario_topic, knowledge_topic):
        self._event_bus = event_bus
        self._scenario_topic = scenario_topic
        self._knowledge_topic = knowledge_topic

        self._scenario = None
        self._perception_counter = None
        self._scenario_lock = RLock()

    @property
    def current(self) -> Optional[Scenario[HiTepContext]]:
        with self._scenario_lock:
            return self._scenario

    @property
    def current_context(self) -> Optional[models.ScenarioContext]:
        if self.current is None:
            return None

        if not self.current.end:
            return models.ScenarioContext(id=self.current.id,
                                   user=self.current.context.speaker.uri, location=self.current.context.location_id,
                                   start=datetime.fromtimestamp(self.current.start//1000, timezone.utc))

        return models.ScenarioContext(id=self.current.id,
                               user=self.current.context.speaker.uri, location=self.current.context.location_id,
                               start=datetime.fromtimestamp(self.current.start//1000, timezone.utc),
                               end=datetime.fromtimestamp(self.current.end//1000, timezone.utc))

    def next_counter(self):
        return next(self._perception_counter) if self._perception_counter else None

    def start_scenario(self, context: models.ScenarioContext) -> models.ScenarioContext:
        with self._scenario_lock:
            logger.debug("Starting scenario %s", context.id)

            scenario, capsule = self._create_scenario(context)
            self._event_bus.publish(self._scenario_topic, Event.for_payload(ScenarioStarted.create(scenario)))
            if self._knowledge_topic:
                self._event_bus.publish(self._knowledge_topic, Event.for_payload([capsule]))
            self._scenario = scenario
            self._perception_counter = itertools.count()

            logger.info("Started scenario %s", scenario)

        return self.current_context

    def stop_scenario(self, timestamp: datetime) -> models.ScenarioContext:
        with self._scenario_lock:
            logger.debug("Stopping scenario %s", self._scenario)

            scenario_end = int(timestamp.timestamp() * 1000) if timestamp else timestamp_now()
            self._scenario.ruler.end = scenario_end

            self._event_bus.publish(self._scenario_topic,
                                    Event.for_payload(ScenarioStopped.create(self._scenario)))
            stopped_context = self.current_context
            self._scenario = None
            self._perception_counter = None

            logger.info("Stopped scenario %s", self._scenario)

        return stopped_context

    def _create_scenario(self, context: models.ScenarioContext):
        signals = {
            Modality.TEXT.name.lower(): "./text.json",
            Modality.AUDIO.name.lower(): "./audio.json",
            Modality.VIDEO.name.lower(): "./detection.json"
        }

        scenario_start = int(context.start.timestamp() * 1000) if context.start else timestamp_now()
        location_id = context.location if context.location else str(uuid.uuid4())
        user = Agent(context.user.split("/")[-1], context.user)

        scenario_context = HiTepContext(AGENT, user, location_id)
        scenario = Scenario.new_instance(context.id if context.id else str(uuid.uuid4()),
                                         scenario_start, None, scenario_context, signals)

        capsule = {
            "type": "context",
            "context_id": scenario.id,
            "date": datetime.fromtimestamp(scenario_start // 1000, timezone.utc).isoformat(),
            "place": None,
            "place_id": location_id,
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

