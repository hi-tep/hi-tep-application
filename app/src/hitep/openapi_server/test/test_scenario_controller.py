import unittest

from flask import json

from hitep.openapi_server.models.scenario_context import ScenarioContext  # noqa: E501
from hitep.openapi_server.models.stop_scenario_request import StopScenarioRequest  # noqa: E501
from hitep.openapi_server.test import BaseTestCase


class TestScenarioController(BaseTestCase):
    """ScenarioController integration test stubs"""

    def test_current_scenario(self):
        """Test case for current_scenario

        Current session metadata
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

        Session metadata by ID
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

        Session start
        """
        scenario_context = {"start":"2000-01-01T00:00:00.000+00:00","location":"https://example.com/ontology/museum/twente","end":"2000-01-01T01:00:00.000+00:00","id":"ee6ce14a-94e4-4ddd-ac60-d1e0262f0274","user":"https://example.com/ontology/alice"}
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

    def test_stop_scenario(self):
        """Test case for stop_scenario

        Session end
        """
        stop_scenario_request = {"end":"2000-01-23T04:56:07.000+00:00"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/stop'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='POST',
            headers=headers,
            data=json.dumps(stop_scenario_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
