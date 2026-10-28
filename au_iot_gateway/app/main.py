import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from app.config import get_settings
from app.history_sync import HistorySyncService
from app.scheduler import RealtimeSyncService

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')


class RealtimeSyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    deviceAddrs: Optional[List[str]] = None


class HistorySyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    deviceAddr: str
    nodeId: str | int = -1
    startTime: str
    endTime: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    realtime_service = RealtimeSyncService(settings)
    app.state.realtime_service = realtime_service
    realtime_service.start()
    yield
    await realtime_service.stop()


app = FastAPI(title='0531yun农业物联网接入网关', version='1.0.0', lifespan=lifespan)


@app.get('/health')
async def health():
    settings = get_settings()
    return {
        'status': 'ok',
        'cloudBaseUrl': settings.cloud_0531_base_url,
        'pollSeconds': settings.cloud_0531_poll_seconds,
        'groupConfigured': bool(settings.cloud_0531_group_id),
        'backendUrl': settings.agri_backend_url,
    }


@app.post('/sync/realtime')
async def sync_realtime(body: RealtimeSyncRequest):
    return await app.state.realtime_service.sync_once(body.deviceAddrs)


@app.post('/sync/history')
async def sync_history(body: HistorySyncRequest):
    service = HistorySyncService(get_settings())
    try:
        return await service.sync_history(body.deviceAddr, body.startTime, body.endTime, body.nodeId)
    finally:
        await service.close()
