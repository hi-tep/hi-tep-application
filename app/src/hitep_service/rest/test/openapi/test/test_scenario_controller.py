import unittest

from flask import json

from openapi.models.get_scenario200_response import GetScenario200Response  # noqa: E501
from openapi.models.scenario_context import ScenarioContext  # noqa: E501
from openapi.test import BaseTestCase


class TestScenarioController(BaseTestCase):
    """ScenarioController integration test stubs"""

    def test_current_scenario(self):
        """Test case for current_scenario

        Retrieve an interaction
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/scenario/current',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_scenario(self):
        """Test case for get_scenario

        Retrieve an interaction
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_start_scenario(self):
        """Test case for start_scenario

        Start a new interaction
        """
        scenario_context = {"start":"2000-01-23T04:56:07.000+00:00","location":"https://example.com/museum","end":"2000-01-23T04:56:07.000+00:00","id":"ee6ce14a-94e4-4ddd-ac60-d1e0262f0274","user":"https://example.com/ontology/alice"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='PUT',
            headers=headers,
            data=json.dumps(scenario_context),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
