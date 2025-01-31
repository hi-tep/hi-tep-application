import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi.models.submit_gaze_request import SubmitGazeRequest  # noqa: E501
from openapi import util


def submit_gaze(scenario_id, submit_gaze_request):  # noqa: E501
    """Submit gaze information of the user

    The event marks a conscious gaze of the user on the submitted entities in the painting. # noqa: E501

    :param scenario_id: The unique identifier for the interaction
    :type scenario_id: str
    :type scenario_id: str
    :param submit_gaze_request: 
    :type submit_gaze_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        submit_gaze_request = SubmitGazeRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
