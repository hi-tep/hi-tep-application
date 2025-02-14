from flask.views import MethodView


class StreamAudioView(MethodView):
    def post(self, scenario_id, content_type, body):  # noqa: E501
        """Audio stream

        Stream audio recorded during the session. The stream can be interrupted and started again by calling the endpoint subsequently as many times as needed. Note that interruption of the stream may lead to interruption of speech transcription if it happens during voice activity of the user. # noqa: E501

        :param scenario_id: The unique identifier for the session
        :type scenario_id: str
        :type scenario_id: str
        :param content_type:
        :type content_type: str
        :param body:
        :type body: str

        :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
        """
        return None
