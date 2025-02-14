import logging
import uuid

from hitep.openapi_server.models import Utterance
from hitep_service.rest.controllers.scenario_controller import ScenarioController

logger = logging.getLogger(__name__)


class ChatController:
    def __init__(self, scenario_controller: ScenarioController):
        self._scenario_controller = scenario_controller

        self._latest = None

    @property
    def latest(self) -> Utterance:
        return self._latest

    def set_latest(self, latest: str):
        self._latest = Utterance(id=str(uuid.uuid4()), text=latest)
        logger.info("Set latest response to %s", self._latest)
