from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from module_admin.service.login_service import LoginService
from module_algo.agri_iot.entity.vo.agri_iot_vo import (
    AgriHistorySyncModel,
    AgriRealtimeSyncModel,
    AgriTelemetryBatchModel,
)
from module_algo.agri_iot.service.agri_iot_service import AgriIotService
from utils.response_util import ResponseUtil


agriIotController = APIRouter(prefix='/agri')


@agriIotController.post('/iot/telemetry')
async def receive_iot_telemetry(
    request: Request,
    telemetry: AgriTelemetryBatchModel,
    x_api_key: str = Header(default=''),
    query_db: AsyncSession = Depends(get_db),
):
    if not AgriIotService.verify_api_key(x_api_key):
        return ResponseUtil.forbidden(msg='X-API-Key鉴权失败')

    result = await AgriIotService.receive_telemetry(query_db, getattr(request.app.state, 'redis', None), telemetry)
    return ResponseUtil.success(data=result)


@agriIotController.post('/iot/sync/realtime', dependencies=[Depends(LoginService.get_current_user)])
async def sync_iot_realtime(sync_body: AgriRealtimeSyncModel):
    result = await AgriIotService.sync_realtime(sync_body.device_addrs)
    return ResponseUtil.success(data=result)


@agriIotController.post('/iot/sync/history', dependencies=[Depends(LoginService.get_current_user)])
async def sync_iot_history(sync_body: AgriHistorySyncModel):
    result = await AgriIotService.sync_history(sync_body)
    return ResponseUtil.success(data=result)


@agriIotController.get('/devices')
async def list_agri_devices(
    base_id: Optional[str] = Query(default=None, alias='baseId'),
    plot_id: Optional[str] = Query(default=None, alias='plotId'),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    query_db: AsyncSession = Depends(get_db),
):
    result = await AgriIotService.get_devices(query_db, base_id, plot_id, status, keyword)
    return ResponseUtil.success(data=result)


@agriIotController.get('/environment/latest')
async def get_environment_latest(
    base_id: Optional[str] = Query(default=None, alias='baseId'),
    plot_id: Optional[str] = Query(default=None, alias='plotId'),
    device_id: Optional[int] = Query(default=None, alias='deviceId'),
    query_db: AsyncSession = Depends(get_db),
):
    result = await AgriIotService.get_latest_environment(query_db, base_id, plot_id, device_id)
    return ResponseUtil.success(data=result)


@agriIotController.get('/environment/history')
async def get_environment_history(
    base_id: Optional[str] = Query(default=None, alias='baseId'),
    plot_id: Optional[str] = Query(default=None, alias='plotId'),
    device_id: Optional[int] = Query(default=None, alias='deviceId'),
    metric_codes: Optional[str] = Query(default=None, alias='metricCodes'),
    start_time: Optional[datetime] = Query(default=None, alias='startTime'),
    end_time: Optional[datetime] = Query(default=None, alias='endTime'),
    query_db: AsyncSession = Depends(get_db),
):
    code_list = [item.strip() for item in metric_codes.split(',')] if metric_codes else None
    result = await AgriIotService.get_environment_history(
        query_db,
        base_id=base_id,
        plot_id=plot_id,
        device_id=device_id,
        metric_codes=code_list,
        start_time=start_time,
        end_time=end_time,
    )
    return ResponseUtil.success(data=result)


@agriIotController.get('/environment/alerts')
async def get_environment_alerts(
    base_id: Optional[str] = Query(default=None, alias='baseId'),
    plot_id: Optional[str] = Query(default=None, alias='plotId'),
    device_id: Optional[int] = Query(default=None, alias='deviceId'),
    status: Optional[str] = None,
    start_time: Optional[datetime] = Query(default=None, alias='startTime'),
    end_time: Optional[datetime] = Query(default=None, alias='endTime'),
    query_db: AsyncSession = Depends(get_db),
):
    result = await AgriIotService.get_environment_alerts(
        query_db, base_id, plot_id, device_id, status, start_time, end_time
    )
    return ResponseUtil.success(data=result)


@agriIotController.get('/iot/sync/logs', dependencies=[Depends(LoginService.get_current_user)])
async def list_iot_sync_logs(
    sync_type: Optional[str] = Query(default=None, alias='syncType'),
    limit: int = Query(default=50, ge=1, le=200),
    query_db: AsyncSession = Depends(get_db),
):
    result = await AgriIotService.get_sync_logs(query_db, sync_type, limit)
    return ResponseUtil.success(data=result)
