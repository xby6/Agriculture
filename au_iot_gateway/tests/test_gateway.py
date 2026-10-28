import os
import sys
import unittest
from datetime import datetime, timezone

import httpx

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.client import Cloud0531Client, is_success_code
from app.config import GatewaySettings
from app.normalizer import (
    build_telemetry_batch,
    get_lng,
    normalize_history_response,
    normalize_realtime_response,
    parse_number,
    parse_observed_at,
)


class GatewayClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_token_is_cached(self):
        calls = {'token': 0}

        def handler(request: httpx.Request):
            if request.url.path == '/api/getToken':
                calls['token'] += 1
                return httpx.Response(200, json={'code': 0, 'data': {'token': 'cached-token', 'expiration': 4102416000000}})
            return httpx.Response(200, json={'code': 0, 'data': []})

        settings = GatewaySettings(cloud_0531_base_url='http://testserver')
        client = Cloud0531Client(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url='http://testserver'))
        self.assertEqual(await client.get_token(), 'cached-token')
        self.assertEqual(await client.get_token(), 'cached-token')
        self.assertEqual(calls['token'], 1)
        await client.close()

    async def test_auth_failed_refreshes_token_and_retries_once(self):
        calls = {'token': 0, 'data': 0}

        def handler(request: httpx.Request):
            if request.url.path == '/api/getToken':
                calls['token'] += 1
                token = f"token-{calls['token']}"
                return httpx.Response(200, json={'code': 0, 'data': {'token': token, 'expiration': 4102416000000}})
            if request.url.path == '/api/data/getRealTimeData':
                calls['data'] += 1
                if calls['data'] == 1:
                    return httpx.Response(200, json={'code': 1004, 'msg': 'auth failed'})
                return httpx.Response(200, json={'code': 1000, 'data': [{'deviceAddr': 'D1'}]})
            return httpx.Response(404)

        settings = GatewaySettings(cloud_0531_base_url='http://testserver')
        client = Cloud0531Client(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url='http://testserver'))
        result = await client.request('/api/data/getRealTimeData', {'groupId': 'g1'})
        self.assertTrue(is_success_code(result['code']))
        self.assertEqual(calls['token'], 2)
        self.assertEqual(calls['data'], 2)
        self.assertEqual(client.token, 'token-2')
        await client.close()

    async def test_network_failure_is_raised_for_scheduler_logging(self):
        def handler(request: httpx.Request):
            raise httpx.ConnectError('network down', request=request)

        settings = GatewaySettings(cloud_0531_base_url='http://testserver')
        client = Cloud0531Client(settings, httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url='http://testserver'))
        with self.assertRaises(httpx.ConnectError):
            await client.get_token(force_refresh=True)
        await client.close()


class GatewayNormalizerTest(unittest.TestCase):
    def test_success_codes(self):
        self.assertTrue(is_success_code(0))
        self.assertTrue(is_success_code(1000))
        self.assertFalse(is_success_code(1001))

    def test_lng_and_Lng_are_supported(self):
        self.assertEqual(get_lng({'lng': '122.76'}), 122.76)
        self.assertEqual(get_lng({'Lng': '122.77'}), 122.77)

    def test_realtime_data_item_is_normalized(self):
        response = {
            'code': 0,
            'data': [
                {
                    'deviceAddr': 'D1',
                    'deviceName': '海城环境站',
                    'deviceStatus': 'normal',
                    'lat': '40.88',
                    'Lng': '122.75',
                    'timeStamp': 1721563200000,
                    'dataItem': [
                        {
                            'nodeId': 1,
                            'registerItem': [
                                {
                                    'registerId': 11,
                                    'registerName': '空气温度',
                                    'value': '24.6',
                                    'unit': '℃',
                                    'alarmLevel': 0,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        records = normalize_realtime_response(response)
        self.assertEqual(records[0]['deviceAddr'], 'D1')
        self.assertEqual(records[0]['longitude'], 122.75)
        self.assertEqual(records[0]['metrics'][0]['nodeId'], 1)
        self.assertEqual(records[0]['metrics'][0]['value'], 24.6)

    def test_history_data_is_normalized(self):
        response = {
            'code': 1000,
            'data': [
                {
                    'recordId': 'R1',
                    'deviceAddr': 'D1',
                    'nodeId': 1,
                    'recordTimeStr': '2026-07-21 10:00:00',
                    'lng': '122.75',
                    'lat': '40.88',
                    'data': [{'registerId': 12, 'registerName': '湿度', 'text': '91.2 %', 'alarmLevel': 3}],
                }
            ],
        }
        records = normalize_history_response(response)
        self.assertEqual(records[0]['metrics'][0]['registerId'], 12)
        self.assertEqual(records[0]['metrics'][0]['value'], 91.2)

    def test_timestamp_to_iso8601(self):
        observed = parse_observed_at(1721563200000)
        parsed = datetime.fromisoformat(observed)
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_invalid_value_is_marked(self):
        value, flag = parse_number('', '异常')
        self.assertIsNone(value)
        self.assertEqual(flag, 'invalid')

    def test_unmapped_factor_is_retained_without_metric_code(self):
        response = {
            'code': 0,
            'data': [{'deviceAddr': 'D1', 'timeStamp': 1721563200000, 'dataItem': [{'nodeId': 1, 'registerItem': [{'registerId': 99, 'registerName': '未知因子', 'value': '7'}]}]}],
        }
        batch = build_telemetry_batch('realtime', normalize_realtime_response(response))
        self.assertEqual(batch['records'][0]['metrics'][0]['factorName'], '未知因子')
        self.assertIsNone(batch['records'][0]['metrics'][0]['metricCode'])

    def test_duplicate_records_keep_same_backend_unique_key(self):
        response = {
            'code': 0,
            'data': [
                {'deviceAddr': 'D1', 'timeStamp': 1721563200000, 'dataItem': [{'nodeId': 1, 'registerItem': [{'registerId': 1, 'value': '1'}]}]},
                {'deviceAddr': 'D1', 'timeStamp': 1721563200000, 'dataItem': [{'nodeId': 1, 'registerItem': [{'registerId': 1, 'value': '1'}]}]},
            ],
        }
        records = normalize_realtime_response(response)
        keys = [
            (item['deviceAddr'], item['metrics'][0]['nodeId'], item['metrics'][0]['registerId'], item['observedAt'])
            for item in records
        ]
        self.assertEqual(keys[0], keys[1])


if __name__ == '__main__':
    unittest.main()
