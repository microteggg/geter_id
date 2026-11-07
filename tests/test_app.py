"""Uji memakai fixture sintetis, bukan data saham live."""
import asyncio
import base64
import time
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend import app as m

class ApiTests(unittest.TestCase):
    def setUp(self):
        m.CACHE.clear();m.PENDING.clear();m.RATE.clear()
        self.client=TestClient(m.app)
    def test_static_and_health(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/api/health').json()['version'],'1.0.0')
        self.assertEqual(self.client.get('/app.js').status_code,200)
        self.assertEqual(self.client.get('/api/not-found').status_code,404)
    def test_validation(self):
        self.assertEqual(self.client.get('/api/stock/BBCA/history?period=bad').status_code,422)
        self.assertEqual(self.client.get('/api/stock/INVALID!/quote').status_code,422)
        self.assertEqual(self.client.get('/api/screen?preset=unknown').status_code,422)
    def test_quote_and_cache(self):
        fixture={'data':[{'symbol':'TEST','price':100,'change_pct':None}], 'provider':'fixture'}
        with patch.object(m,'run',new=AsyncMock(return_value=fixture)) as run:
            a=self.client.get('/api/stock/BBCA/quote').json()
            b=self.client.get('/api/stock/BBCA/quote').json()
            self.assertEqual(a['data'][0]['price'],100)
            self.assertTrue(b['meta']['server_cached'])
            self.assertEqual(run.await_count,1)
    def test_provider_error(self):
        with patch.object(m,'run',new=AsyncMock(side_effect=m.EngineError('Provider gagal'))):
            self.assertEqual(self.client.get('/api/stock/BBCA/quote').status_code,503)
    def test_stale(self):
        key=('stocks','quote','BBCA')
        m.CACHE[key]=(time.monotonic()-1000,'2026-01-01T00:00:00Z',{'data':[{'price':100}]})
        with patch.object(m,'run',new=AsyncMock(side_effect=m.EngineError('Provider gagal'))):
            p=self.client.get('/api/stock/BBCA/quote').json()
            self.assertTrue(p['meta']['server_stale'])
    def test_auth(self):
        with patch.object(m,'USER','tester'),patch.object(m,'PASSWORD','secret'):
            self.assertEqual(self.client.get('/').status_code,401)
            self.assertEqual(self.client.get('/api/health').status_code,200)
            token=base64.b64encode(b'tester:secret').decode()
            self.assertEqual(self.client.get('/',headers={'Authorization':'Basic '+token}).status_code,200)
    def test_ownership_disabled(self):
        with patch.dict('os.environ',{'ENABLE_OWNERSHIP':'false'}):
            self.assertEqual(self.client.get('/api/stock/BBCA/ownership').status_code,503)
    def test_routes(self):
        with patch.object(m,'run',new=AsyncMock(return_value={'data':{}})):
            for path in ['/api/market','/api/market-foreign','/api/stock/BBCA/technical','/api/stock/BBCA/fundamental','/api/stock/BBCA/foreign','/api/stock/BBCA/broker','/api/stock/BBCA/bandar','/api/stock/BBCA/news','/api/stock/BBCA/actions','/api/stock/BBCA/history','/api/screen?preset=accumulation']:
                self.assertEqual(self.client.get(path).status_code,200,path)

class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_kills_process(self):
        proc=AsyncMock();proc.returncode=None
        proc.kill=lambda:None
        proc.communicate.side_effect=[asyncio.TimeoutError(),(b'',b'')]
        with patch.object(asyncio,'create_subprocess_exec',return_value=proc):
            with self.assertRaises(m.EngineError): await m.run(['stocks','quote','BBCA'])
    async def test_missing_binary(self):
        with patch.object(asyncio,'create_subprocess_exec',side_effect=FileNotFoundError()):
            with self.assertRaises(m.EngineError): await m.run(['version'])

if __name__=='__main__': unittest.main()
