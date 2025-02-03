import unittest

from flask import json

from hitep.openapi_server.models.position_change import PositionChange  # noqa: E501
from hitep.openapi_server.test import BaseTestCase


class TestPositionController(BaseTestCase):
    """PositionController integration test stubs"""

    def test_submit_position_change(self):
        """Test case for submit_position_change

        Position change of the user
        """
        position_change = {"previous":{"x":0.0,"y":0.0,"z":0.0},"current":{"x":1.0,"y":2.0,"z":3.0},"timestamp":"2000-01-23T04:56:07.000+00:00"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/positionchange'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='POST',
            headers=headers,
            data=json.dumps(position_change),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
