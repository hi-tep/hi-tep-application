import connexion

from openapi_server.models.gaze_detection import GazeDetection  # noqa: E501


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

    return None


#     self._event_bus.publish(Event.for_payload(self._experience_from_gaze(scenario_id, gaze_detection)))
#
# def _experience_from_gaze(self, scenario_id, gaze):
#     gaze_id = str(uuid.uuid4())
#     source = Source(None, ["person"], self._scenario.user)
#     for entity in gaze.entities:
#         return PaintingExperience(gaze.painting, gaze_id, source, None, gaze.bounding_box,
#                      Entity(**(entity.to_dict() | {"id": None})),
#                      1.0, scenario_id, timestamp_now())
