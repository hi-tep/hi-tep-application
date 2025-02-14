import logging
from datetime import datetime

from flask.views import MethodView

from hitep.openapi_server.models import GazeDetection
from hitep.openapi_server.models.scenario_context import ScenarioContext  # noqa: E501
from hitep.openapi_server.models.stop_scenario_request import StopScenarioRequest  # noqa: E501
from hitep_service.rest.controllers.gaze_controller import GazeController
from hitep_service.rest.controllers.scenario_controller import ScenarioController

logger = logging.getLogger(__name__)


class CurrentView(MethodView):
    def __init__(self, controller: ScenarioController):
        self._controller = controller

    def get(self, scenario_id):  # noqa: E501
        current = self._controller.current

        return current if current else (None, 404)


class ScenarioView(MethodView):
    def __init__(self, controller: ScenarioController):
        self._controller = controller

    def get(self, scenario_id):  # noqa: E501
        current = self._controller.current
        if current and current == scenario_id:
            return current

        return None, 404

    def put(self, scenario_id, body):  # noqa: E501
        # TODO thread safty
        if self._controller.current:
            return (f"Scenario already started: {self._controller.current and self._controller.current.id}"), 409

        scenario_context = body if isinstance(body, ScenarioContext) else ScenarioContext.from_dict(body)

        if scenario_context.id and scenario_context.id != scenario_id:
            return 'Scenario ID does not match, expected: {scenario_id}, was {scenario_context.id}', 422

        if not scenario_context.id:
            scenario_context.id = scenario_id

        self._controller.start_scenario(scenario_context)

        return scenario_context


class StopView(MethodView):
    def __init__(self, controller: ScenarioController):
        self._controller = controller

    def post(self, scenario_id, body):  # noqa: E501
        current = self._controller.current
        if not current or current.id != scenario_id:
            return f'Scenario ID does not match current scenario, expected: {current and current.id}, was {scenario_id}', 422

        stop_scenario_request = body if isinstance(body, StopScenarioRequest) else StopScenarioRequest.from_dict(body)  # noqa: E501

        # TODO Threadsafty
        return self._controller.stop_scenario(stop_scenario_request.end)


class GazeView(MethodView):
    def __init__(self, controller: GazeController):
        self._controller = controller

    def post(self, scenario_id, body):  # noqa: E501
        gaze_detection = body if isinstance(body, GazeDetection) else GazeDetection.from_dict(body)
        self._controller.add_gaze(scenario_id, gaze_detection)
