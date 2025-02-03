import unittest

from flask import json

from hitep.openapi_server.models.utterance import Utterance  # noqa: E501
from hitep.openapi_server.test import BaseTestCase


class TestChatController(BaseTestCase):
    """ChatController integration test stubs"""

    def test_get_latest_response(self):
        """Test case for get_latest_response

        Latest response
        """
        headers = { 
            'Accept': 'application/json',
            'if_none_match': 'W/\"1234567890\"',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/chat/response/latest'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
