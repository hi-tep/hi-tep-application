import random
import uuid

from openapi_server.models.utterance import Utterance  # noqa: E501


def get_latest_response(scenario_id, if_none_match=None):  # noqa: E501
    """Latest response

    Retrieve the most recent response of the agent, maybe empty if there was no response yet. This endpoint is intended for constant polling and supports caching through ETag headers. The response contains only a start timestamp, as the duration of the utterance is not known. # noqa: E501

    :param scenario_id: The unique identifier for the session
    :type scenario_id: str
    :type scenario_id: str
    :param if_none_match: 
    :type if_none_match: str

    :rtype: Union[Utterance, Tuple[Utterance, int], Tuple[Utterance, int, Dict[str, str]]
    """
    if random.random() < 0.5:
        return Utterance(id=str(uuid.uuid4()), text="Hello world!")

    return None, 304
