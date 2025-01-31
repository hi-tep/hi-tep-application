import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi.models.get_scenario200_response import GetScenario200Response  # noqa: E501
from openapi.models.scenario_context import ScenarioContext  # noqa: E501
from openapi import util


def current_scenario():  # noqa: E501
    """Retrieve an interaction

     # noqa: E501


    :rtype: Union[GetScenario200Response, Tuple[GetScenario200Response, int], Tuple[GetScenario200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_scenario(scenario_id):  # noqa: E501
    """Retrieve an interaction

     # noqa: E501

    :param scenario_id: The unique identifier for the interaction
    :type scenario_id: str
    :type scenario_id: str

    :rtype: Union[GetScenario200Response, Tuple[GetScenario200Response, int], Tuple[GetScenario200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def start_scenario(scenario_id, scenario_context):  # noqa: E501
    """Start a new interaction

     # noqa: E501

    :param scenario_id: The unique identifier for the interaction
    :type scenario_id: str
    :type scenario_id: str
    :param scenario_context: 
    :type scenario_context: dict | bytes

    :rtype: Union[ScenarioContext, Tuple[ScenarioContext, int], Tuple[ScenarioContext, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        scenario_context = ScenarioContext.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
