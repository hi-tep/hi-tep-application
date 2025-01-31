import unittest

from flask import json

from openapi.models.submit_gaze_request import SubmitGazeRequest  # noqa: E501
from openapi.test import BaseTestCase


class TestGazeController(BaseTestCase):
    """GazeController integration test stubs"""

    def test_submit_gaze(self):
        """Test case for submit_gaze

        Submit gaze information of the user
        """
        submit_gaze_request = openapi.SubmitGazeRequest()
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/gaze'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='POST',
            headers=headers,
            data=json.dumps(submit_gaze_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
