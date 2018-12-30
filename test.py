import unittest
import json
from urllib.parse import urlparse

from graphene.test import Client
from starlette.testclient import TestClient

from app import schema, app
from cache import cache

import pook

url_fixture = urlparse('http://localhost:8001/')

expected_title = 'Example title'
expected_body = 'Example body'
expected_hostname = url_fixture.hostname

message = '''
<!DOCTYPE html>
<html>
    <head>
        <title>{}</title>
    </head>
    <body>
        <h1>{}</h1>
    </body>
</html>
'''.format(expected_title, expected_body)


class TestSchemaQueries(unittest.TestCase):
    def test_app(self):
        client = TestClient(app)
        response = client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_cache(self):
        cache.set('foo', 'bar')
        result = cache.get('foo')
        no_result = cache.get('baz')
        self.assertEqual(result, bytes('bar', 'utf-8'))
        self.assertEqual(no_result, None)

    def test_article_ok(self):
        pook.get('http://localhost:8001/',
                reply=200,
                response_headers={'Content-Type': 'text/html'},
                response_body=message)

        query = '''
            {
                article(url: "http://localhost:8001")
                {
                    title
                    hostname
                }
            }
            '''

        client = Client(schema)
        executed = client.execute(query)
        expected = {
            'data': {
                'article': {
                    'title': expected_title,
                    'hostname': expected_hostname
                }
            }
        }

        self.assertEqual(json.loads(json.dumps(executed)), expected)

    def test_articles_ok(self):
        pook.get('http://localhost:8001/',
                reply=200,
                response_headers={'Content-Type': 'text/html'},
                response_body=message)

        query = '''
            {
                articles(urls: ["http://localhost:8001"])
                {
                    title
                    hostname
                }
            }
            '''
        client = Client(schema)
        executed = client.execute(query)
        expected = {
            'data': {
                'articles': [{
                    'title': expected_title,
                    'hostname': expected_hostname
                }]
            }
        }

        self.assertEqual(json.loads(json.dumps(executed)), expected)

    def test_articles_failure(self):
        pook.get('http://localhost:8001/',
                reply=200,
                response_headers={'Content-Type': 'text/html'},
                response_body=message)

        query = '''
            {
                articles(urls: ["http://localhost:8001", "unscrapeableurl"])
                {
                    title
                    hostname
                }
            }
            '''

        client = Client(schema)
        executed = client.execute(query)
        expected = {
            'data': {
                'articles': [{
                    'title': expected_title,
                    'hostname': expected_hostname,
                },
                    None
                ]
            },
            'errors': [{
                'locations': [{'column': 17, 'line': 3}],
                'message': 'Failed to parse url unscrapeableurl',
                'path': ['articles', 1]
            }]
        }

        self.assertEqual(json.loads(json.dumps(executed)), expected)


if __name__ == '__main__':
    pook.on()
    unittest.main()
