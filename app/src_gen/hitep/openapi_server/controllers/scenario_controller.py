import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from hitep.openapi_server.models.scenario_context import ScenarioContext  # noqa: E501
from hitep.openapi_server.models.stop_scenario_request import StopScenarioRequest  # noqa: E501
from hitep.openapi_server import util


def current_scenario():  # noqa: E501
    """Current session metadata

    Retrieve session metadata of the current session # noqa: E501


    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_scenario(scenario_id):  # noqa: E501
    """Session metadata by ID

    Retrieve session metadata by ID # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str

    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    return 'do some magic!'


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
    if connexion.request.is_json:
        scenario_context = ScenarioContext.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


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
    if connexion.request.is_json:
        stop_scenario_request = StopScenarioRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
