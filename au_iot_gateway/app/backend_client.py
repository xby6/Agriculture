from typing import Any, Dict, Optional

import httpx

from app.config import GatewaySettings, get_settings


class BackendClient:
    def __init__(
        self,
        settings: Optional[GatewaySettings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings or get_settings()
        self._client = http_client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def post_telemetry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        client = self._client or httpx.AsyncClient(
            base_url=self.settings.agri_backend_url,
            timeout=self.settings.cloud_0531_timeout_seconds,
        )
        try:
            response = await client.post(
                '/agri/iot/telemetry',
                json=payload,
                headers={'X-API-Key': self.settings.agri_internal_api_key},
            )
            response.raise_for_status()
            data = response.json()
            if data.get('code') != 200 or data.get('success') is False:
                raise RuntimeError(f"backend telemetry failed: code={data.get('code')} msg={data.get('msg')}")
            return data
        finally:
            if self._client is None:
                await client.aclose()
