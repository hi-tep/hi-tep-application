import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from hitep.openapi_server.models.gaze_detection import GazeDetection  # noqa: E501
from hitep.openapi_server import util


def submit_gaze(scenario_id, gaze_detection):  # noqa: E501
    """Gaze event of the user

    The event marks a sustained gaze of the user on an Area of Interest (AoI) in the painting, containing the submitted entities. There can be multiple gaze detections on with the same gaze target(s) in sequence, differing only by start and stop date. # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str
    :param gaze_detection: The gaze information
    :type gaze_detection: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gaze_detection = GazeDetection.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
