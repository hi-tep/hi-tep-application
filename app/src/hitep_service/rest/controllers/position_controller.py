import connexion

from openapi_server.models.position_change import PositionChange  # noqa: E501


def submit_position_change(scenario_id, position_change):  # noqa: E501
    """Position change of the user

    The event indicates the visitor&#39;s change in position. The position change can be instantly, the provided timestamp indicates that the user was at the provided current position at the provided timestamp. # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str
    :param position_change: 
    :type position_change: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        position_change = PositionChange.from_dict(connexion.request.get_json())  # noqa: E501

    return None
