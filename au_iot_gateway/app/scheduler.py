import asyncio
import logging
from typing import List, Optional

from app.backend_client import BackendClient
from app.client import Cloud0531Client
from app.config import GatewaySettings, get_settings
from app.normalizer import build_telemetry_batch, normalize_realtime_response

logger = logging.getLogger(__name__)


class RealtimeSyncService:
    def __init__(
        self,
        settings: Optional[GatewaySettings] = None,
        cloud_client: Optional[Cloud0531Client] = None,
        backend_client: Optional[BackendClient] = None,
    ):
        self.settings = settings or get_settings()
        self.cloud_client = cloud_client or Cloud0531Client(self.settings)
        self.backend_client = backend_client or BackendClient(self.settings)
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.cloud_client.close()
        await self.backend_client.close()

    async def sync_once(self, device_addrs: Optional[List[str]] = None):
        if device_addrs:
            response = await self.cloud_client.get_realtime_data_by_device_addr(device_addrs)
        else:
            if not self.settings.cloud_0531_group_id:
                raise ValueError('CLOUD_0531_GROUP_ID is required for realtime group sync')
            response = await self.cloud_client.get_realtime_data(self.settings.cloud_0531_group_id)
        records = normalize_realtime_response(response)
        payload = build_telemetry_batch('realtime', records)
        return await self.backend_client.post_telemetry(payload)

    async def _run_loop(self) -> None:
        while not self._stopped.is_set():
            try:
                result = await self.sync_once()
                logger.info('realtime sync finished: %s', result)
            except Exception as exc:
                logger.exception('realtime sync failed, next round will continue: %s', exc)
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.settings.cloud_0531_poll_seconds)
            except asyncio.TimeoutError:
                continue
