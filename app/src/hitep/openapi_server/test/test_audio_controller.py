import unittest

from flask import json

from hitep.openapi_server.test import BaseTestCase


class TestAudioController(BaseTestCase):
    """AudioController integration test stubs"""

    @unittest.skip("Connexion does not support multiple consumes. See https://github.com/zalando/connexion/pull/760")
    def test_stream_audio(self):
        """Test case for stream_audio

        Audio stream
        """
        body = '/path/to/file'
        headers = { 
            'Content-Type': 'audio/l16',
            'content_type': 'audio/l16;rate=16000;channels=2',
        }
        response = self.client.open(
            '/scenario/{scenario_id}/audio'.format(scenario_id='ee6ce14a-94e4-4ddd-ac60-d1e0262f0274'),
            method='POST',
            headers=headers,
            data=json.dumps(body),
            content_type='audio/l16')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
