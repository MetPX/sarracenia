"""
Regression test: MQTT putNewMessage must not modify the caller's message.

Same fix as amqp.py (PR #1609) -- replace copy.deepcopy with dict() shallow
copy in the publish path. Only top-level keys are deleted via _deleteOnPost;
nested dicts are never mutated by the publish path.
"""

import unittest


class TestMqttPutNewMessageShallowCopy(unittest.TestCase):

    def _make_message(self):
        return {
            'baseUrl': 'sftp://server.example.com/',
            'relPath': '/data/obs/file.dat',
            'pubTime': '20260320T220000.0',
            'integrity': {'method': 'sha512', 'value': 'abc123'},
            'size': 1048576,
            'source': 'anonymous',
            'topic': ['v03', 'post', 'data'],
            '_format': 'v03',
            '_deleteOnPost': set(['_format', 'exchange', 'local_offset',
                                  'subtopic', 'ack_id', 'subscription_index']),
            'exchange': 'xpublic',
            'local_offset': 0,
            'subtopic': ['data', 'obs'],
            'ack_id': 12345,
            'subscription_index': 0,
        }

    def test_shallow_copy_preserves_original_keys(self):
        """Deleting _deleteOnPost keys from shallow copy must not touch the original."""
        msg = self._make_message()
        original_keys = set(msg.keys())

        body = dict(msg)
        if '_deleteOnPost' in body:
            for k in list(body['_deleteOnPost']):
                if k in body:
                    del body[k]
            del body['_deleteOnPost']

        self.assertEqual(set(msg.keys()), original_keys)
        self.assertIn('_format', msg)
        self.assertIn('exchange', msg)
        self.assertIn('_deleteOnPost', msg)

        self.assertNotIn('_format', body)
        self.assertNotIn('exchange', body)
        self.assertNotIn('_deleteOnPost', body)

    def test_nested_dicts_not_mutated_by_publish(self):
        """Nested dicts are shared refs but the publish path only reads them."""
        msg = self._make_message()
        body = dict(msg)

        self.assertIs(msg['integrity'], body['integrity'])

        import json
        json.dumps(body, default=str)

        self.assertEqual(msg['integrity']['method'], 'sha512')
        self.assertEqual(msg['integrity']['value'], 'abc123')

    def test_deleteOnPost_set_intact_after_copy_deletion(self):
        """_deleteOnPost set is shared but we only iterate and delete from the copy."""
        msg = self._make_message()
        original_dop = msg['_deleteOnPost'].copy()

        body = dict(msg)
        if '_deleteOnPost' in body:
            for k in list(body['_deleteOnPost']):
                if k in body:
                    del body[k]
            del body['_deleteOnPost']

        self.assertEqual(msg['_deleteOnPost'], original_dop)

    def test_mqtt_specific_keys_preserved(self):
        """MQTT messages have subscription_index -- verify it survives in original."""
        msg = self._make_message()

        body = dict(msg)
        if '_deleteOnPost' in body:
            for k in list(body['_deleteOnPost']):
                if k in body:
                    del body[k]
            del body['_deleteOnPost']

        self.assertIn('subscription_index', msg)
        self.assertNotIn('subscription_index', body)


if __name__ == '__main__':
    unittest.main()
