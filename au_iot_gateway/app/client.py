import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from app.config import GatewaySettings, get_settings

logger = logging.getLogger(__name__)


SUCCESS_CODES = {0, 1000}
AUTH_FAILED_CODE = 1004


class CloudApiError(RuntimeError):
    pass


def is_success_code(code: Any) -> bool:
    try:
        return int(code) in SUCCESS_CODES
    except (TypeError, ValueError):
        return False


class Cloud0531Client:
    def __init__(
        self,
        settings: Optional[GatewaySettings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings or get_settings()
        self._client = http_client
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def token_expiration(self) -> Optional[datetime]:
        return self._token_expiration

    async def get_token(self, force_refresh: bool = False) -> str:
        if not force_refresh and self._token and self._token_expiration:
            if datetime.now(timezone.utc) + timedelta(seconds=60) < self._token_expiration:
                return self._token

        data = await self._raw_get(
            '/api/getToken',
            params={
                'loginName': self.settings.cloud_0531_login_name,
                'password': self.settings.cloud_0531_password,
            },
            headers=None,
        )
        if not is_success_code(data.get('code')):
            raise CloudApiError(f"0531yun token failed: code={data.get('code')} msg={data.get('msg')}")

        token_data = data.get('data') or {}
        token = token_data.get('token')
        if not token:
            raise CloudApiError('0531yun token response missing data.token')

        self._token = token
        self._token_expiration = self._parse_expiration(token_data.get('expiration'))
        logger.info('0531yun token refreshed, expires_at=%s', self._token_expiration.isoformat())
        return token

    async def request(self, path: str, params: Optional[Dict[str, Any]] = None, retry_auth: bool = True) -> Dict[str, Any]:
        token = await self.get_token()
        data = await self._raw_get(path, params=params, headers={'authorization': token})
        code = data.get('code')
        if self._is_auth_failed(code) and retry_auth:
            logger.warning('0531yun auth expired, refreshing token once')
            token = await self.get_token(force_refresh=True)
            data = await self._raw_get(path, params=params, headers={'authorization': token})
            code = data.get('code')
        if not is_success_code(code):
            raise CloudApiError(f"0531yun request failed: path={path} code={code} msg={data.get('msg')}")
        return data

    async def get_group_list(self) -> Dict[str, Any]:
        return await self.request('/api/device/getGroupList')

    async def get_device_list(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        params = {'groupId': group_id} if group_id else {}
        return await self.request('/api/device/getDeviceList', params=params)

    async def get_realtime_data(self, group_id: str) -> Dict[str, Any]:
        return await self.request('/api/data/getRealTimeData', params={'groupId': group_id})

    async def get_realtime_data_by_device_addr(self, device_addrs: list[str]) -> Dict[str, Any]:
        return await self.request(
            '/api/data/getRealTimeDataByDeviceAddr',
            params={'deviceAddrs': ','.join(device_addrs)},
        )

    async def history_list(self, device_addr: str, node_id: str | int, start_time: str, end_time: str) -> Dict[str, Any]:
        return await self.request(
            '/api/data/historyList',
            params={
                'deviceAddr': device_addr,
                'nodeId': node_id,
                'startTime': start_time,
                'endTime': end_time,
            },
        )

    async def _raw_get(
        self,
        path: str,
        params: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        client = self._client or httpx.AsyncClient(
            base_url=self.settings.cloud_0531_base_url,
            timeout=self.settings.cloud_0531_timeout_seconds,
        )
        try:
            response = await client.get(path, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        finally:
            if self._client is None:
                await client.aclose()

    @staticmethod
    def _parse_expiration(value: Any) -> datetime:
        if not value:
            return datetime.now(timezone.utc) + timedelta(hours=1)
        if isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(timestamp, timezone.utc)
        text = str(value).strip()
        if text.isdigit():
            timestamp = int(text)
            timestamp = timestamp / 1000 if timestamp > 10_000_000_000 else timestamp
            return datetime.fromtimestamp(timestamp, timezone.utc)
        return datetime.fromisoformat(text.replace('Z', '+00:00'))

    @staticmethod
    def _is_auth_failed(code: Any) -> bool:
        try:
            return int(code) == AUTH_FAILED_CODE
        except (TypeError, ValueError):
            return False
