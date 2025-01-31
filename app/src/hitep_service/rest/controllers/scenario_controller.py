from datetime import datetime
from typing import Optional

import connexion

from openapi_server.models.scenario_context import ScenarioContext  # noqa: E501
from openapi_server.models.stop_scenario_request import StopScenarioRequest  # noqa: E501


current_scenario: Optional[ScenarioContext] = None


def current_scenario():  # noqa: E501
    """Current session metadata

    Retrieve session metadata of the current session # noqa: E501


    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    if current_scenario:
        return current_scenario

    return None, 404


def get_scenario(scenario_id):  # noqa: E501
    """Session metadata by ID

    Retrieve session metadata by ID # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str

    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    if current_scenario.id == scenario_id:
        return current_scenario

    return None, 404


def start_scenario(scenario_id, scenario_context):  # noqa: E501
    """Session start

    Start a new session (scenario) # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str
    :param scenario_context: The metadata of the session. Optional properties of the submitted ScenarioContext, as for instance the start time, will be filled in automatically. The end time of the ScenarioContext must not be filled in.
    :type scenario_context: dict | bytes

    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    if current_scenario:
        raise ValueError("Scenario already started")

    if scenario_context.id != scenario_id:
        raise ValueError('Scenario ID does not match')

    if connexion.request.is_json:
        scenario_context = ScenarioContext.from_dict(connexion.request.get_json())  # noqa: E501

    if not scenario_context.id:
        scenario_context.id = scenario_id

    if not scenario_context.start:
        scenario_context.start = datetime.now().isoformat()

    current_scenario = scenario_context

    return scenario_context


def stop_scenario(scenario_id, stop_scenario_request=None):  # noqa: E501
    """Session end

    Stop a session # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str
    :param stop_scenario_request: Optionally the end time of the session may be provided. If none is specified, the date of submission is used
    :type stop_scenario_request: dict | bytes

    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    if current_scenario.id != scenario_id:
        raise ValueError('Scenario ID does not match current scenario')

    if connexion.request.is_json:
        stop_scenario_request = StopScenarioRequest.from_dict(connexion.request.get_json())  # noqa: E501

    if stop_scenario_request.end:
        current_scenario.end = stop_scenario_request.end
    else:
        current_scenario.end = datetime.now().isoformat()

    stopped_context = current_scenario
    current_scenario = None

    return stopped_context
