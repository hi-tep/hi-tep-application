import unittest

from flask import json

from hitep.openapi_server.models.gaze_detection import GazeDetection  # noqa: E501
from hitep.openapi_server.test import BaseTestCase


class TestGazeController(BaseTestCase):
    """GazeController integration test stubs"""

    def test_submit_gaze(self):
        """Test case for submit_gaze

        Gaze event of the user
        """
        gaze_detection = {"position":{"x":1.0,"y":2.0,"z":3.0},"painting":"https://example.com/image.jpg","distance":1.0,"entities":[{"IRI":"https://example.com/ontology/king-tubby","label":"King Tubby"},{"IRI":"https://example.com/ontology/king-george","label":"King George"}],"start":"2000-01-23T04:56:07.000+00:00","end":"2000-01-23T04:56:07.000+00:00"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/gaze'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='POST',
            headers=headers,
            data=json.dumps(gaze_detection),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
