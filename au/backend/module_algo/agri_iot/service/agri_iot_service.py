import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional

import httpx
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.env import AgriIotConfig
from module_algo.agri_iot.entity.do.agri_iot_do import (
    AgriDevice,
    AgriMetricMapping,
    AgriSensorObservation,
    AgriSyncLog,
)
from module_algo.agri_iot.entity.vo.agri_iot_vo import (
    AgriHistorySyncModel,
    AgriTelemetryBatchModel,
)


STANDARD_METRIC_CODES = {
    'air_temperature',
    'relative_humidity',
    'soil_temperature',
    'soil_moisture',
    'illuminance',
    'co2_concentration',
    'battery_level',
    'rainfall',
    'wind_speed',
    'wind_direction',
    'air_pressure',
}

DEFAULT_0531_NODE_REGISTER_MAPPING = {
    ('1', '1'): 'air_temperature',
    ('1', '2'): 'relative_humidity',
    ('2', '5'): 'illuminance',
    ('3', '1'): 'soil_temperature',
    ('3', '2'): 'soil_moisture',
    ('4', '2'): 'co2_concentration',
    ('5', '1'): 'battery_level',
}


class AgriIotService:
    """
    农业物联网接入服务
    """

    @classmethod
    def verify_api_key(cls, api_key: str) -> bool:
        return bool(AgriIotConfig.agri_internal_api_key) and api_key == AgriIotConfig.agri_internal_api_key

    @classmethod
    async def receive_telemetry(
        cls,
        query_db: AsyncSession,
        redis_client: Any,
        telemetry: AgriTelemetryBatchModel,
    ) -> Dict[str, Any]:
        started_at = datetime.now(timezone.utc)
        total_count = sum(len(record.metrics) for record in telemetry.records)
        success_count = 0
        duplicate_count = 0
        failed_count = 0
        device_snapshots: Dict[int, Dict[str, Any]] = {}
        seen_points = set()

        try:
            for record in telemetry.records:
                observed_at = cls._normalize_datetime(record.observed_at) or started_at
                device = await cls._upsert_device(query_db, record, observed_at)
                await query_db.flush()

                snapshot = {
                    'deviceId': device.id,
                    'deviceAddr': device.vendor_device_addr,
                    'deviceName': device.device_name,
                    'deviceStatus': device.device_status,
                    'observedAt': cls._iso(observed_at),
                    'alarmLevel': 0,
                    'metrics': {},
                }

                for metric in record.metrics:
                    node_id = cls._to_text(metric.node_id) or '0'
                    register_id = cls._to_text(metric.register_id) or cls._to_text(metric.factor_id) or '0'
                    try:
                        mapping = await cls._get_mapping(query_db, record.device_addr, node_id, register_id)
                        metric_code = cls._resolve_metric_code(
                            mapping,
                            metric.metric_code,
                            record.vendor_name,
                            node_id,
                            register_id,
                        )
                        quality_flag = metric.quality_flag or 'normal'
                        value = cls._to_decimal(metric.value)
                        if mapping and value is not None:
                            value = cls._apply_mapping_value(value, mapping)
                        if not metric_code:
                            metric_code = 'unmapped'
                            quality_flag = 'unmapped'
                        elif metric_code not in STANDARD_METRIC_CODES and not mapping:
                            quality_flag = 'unmapped'
                        if value is None and quality_flag != 'unmapped':
                            quality_flag = 'invalid'

                        exists_stmt = select(AgriSensorObservation.id).where(
                            and_(
                                AgriSensorObservation.device_id == device.id,
                                AgriSensorObservation.node_id == node_id,
                                AgriSensorObservation.register_id == register_id,
                                AgriSensorObservation.observed_at == observed_at,
                            )
                        )
                        exists_id = (await query_db.execute(exists_stmt)).scalar_one_or_none()
                        point_key = (device.id, node_id, register_id, observed_at.isoformat())
                        if exists_id or point_key in seen_points:
                            duplicate_count += 1
                            continue
                        seen_points.add(point_key)

                        observation = AgriSensorObservation(
                            device_id=device.id,
                            plot_id=device.plot_id,
                            node_id=node_id,
                            register_id=register_id,
                            metric_code=metric_code,
                            metric_value=value,
                            metric_unit=(mapping.standard_unit if mapping and mapping.standard_unit else metric.unit),
                            alarm_level=metric.alarm_level,
                            alarm_info=metric.alarm_info,
                            observed_at=observed_at,
                            quality_flag=quality_flag,
                            raw_payload=metric.raw_payload or {},
                        )
                        query_db.add(observation)
                        success_count += 1

                        alarm_level = metric.alarm_level or 0
                        if alarm_level != 0:
                            snapshot['alarmLevel'] = alarm_level
                        snapshot['metrics'][metric_code] = {
                            'value': cls._float_or_none(value),
                            'unit': observation.metric_unit,
                            'nodeId': node_id,
                            'registerId': register_id,
                            'factorName': metric.factor_name,
                            'alarmLevel': alarm_level,
                            'alarmInfo': metric.alarm_info,
                            'qualityFlag': quality_flag,
                            'observedAt': cls._iso(observed_at),
                        }
                    except Exception:
                        failed_count += 1

                device_snapshots[device.id] = snapshot

            status = 'success' if failed_count == 0 else 'partial'
            sync_log = AgriSyncLog(
                sync_type=telemetry.sync_type,
                device_addr=telemetry.device_addr,
                start_time=cls._normalize_datetime(telemetry.start_time),
                end_time=cls._normalize_datetime(telemetry.end_time),
                status=status,
                total_count=total_count,
                success_count=success_count,
                duplicate_count=duplicate_count,
                failed_count=failed_count,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
            query_db.add(sync_log)
            await query_db.commit()

            await cls._write_latest_snapshots(redis_client, device_snapshots.values())

            return {
                'syncType': telemetry.sync_type,
                'totalCount': total_count,
                'successCount': success_count,
                'duplicateCount': duplicate_count,
                'failedCount': failed_count,
                'deviceCount': len(device_snapshots),
            }
        except Exception as exc:
            await query_db.rollback()
            failed_log = AgriSyncLog(
                sync_type=telemetry.sync_type,
                device_addr=telemetry.device_addr,
                start_time=cls._normalize_datetime(telemetry.start_time),
                end_time=cls._normalize_datetime(telemetry.end_time),
                status='failed',
                total_count=total_count,
                success_count=success_count,
                duplicate_count=duplicate_count,
                failed_count=max(failed_count, total_count - success_count - duplicate_count),
                error_message=str(exc)[:1000],
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
            query_db.add(failed_log)
            await query_db.commit()
            raise

    @classmethod
    async def get_devices(
        cls,
        query_db: AsyncSession,
        base_id: Optional[str] = None,
        plot_id: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(AgriDevice)
        conditions = []
        if base_id:
            conditions.append(AgriDevice.base_id == base_id)
        if plot_id:
            conditions.append(AgriDevice.plot_id == plot_id)
        if status:
            conditions.append(AgriDevice.device_status == status)
        if keyword:
            keyword_expr = f'%{keyword}%'
            conditions.append(
                (AgriDevice.device_name.like(keyword_expr)) | (AgriDevice.vendor_device_addr.like(keyword_expr))
            )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(desc(AgriDevice.last_seen_at), AgriDevice.id)
        devices = (await query_db.execute(stmt)).scalars().all()
        return [cls._device_to_dict(device) for device in devices]

    @classmethod
    async def get_latest_environment(
        cls,
        query_db: AsyncSession,
        base_id: Optional[str] = None,
        plot_id: Optional[str] = None,
        device_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(AgriSensorObservation, AgriDevice)
            .join(AgriDevice, AgriSensorObservation.device_id == AgriDevice.id)
            .order_by(desc(AgriSensorObservation.observed_at), desc(AgriSensorObservation.id))
            .limit(3000)
        )
        conditions = []
        if base_id:
            conditions.append(AgriDevice.base_id == base_id)
        if plot_id:
            conditions.append(AgriDevice.plot_id == plot_id)
        if device_id:
            conditions.append(AgriDevice.id == device_id)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        rows = (await query_db.execute(stmt)).all()
        latest_by_device: Dict[int, Dict[str, Any]] = {}
        for observation, device in rows:
            item = latest_by_device.setdefault(
                device.id,
                {
                    **cls._device_to_dict(device),
                    'observedAt': cls._iso(device.last_seen_at),
                    'metrics': {},
                },
            )
            if observation.metric_code not in item['metrics']:
                item['metrics'][observation.metric_code] = cls._observation_to_metric(observation)
                if not item.get('observedAt') or observation.observed_at > device.last_seen_at:
                    item['observedAt'] = cls._iso(observation.observed_at)

        return list(latest_by_device.values())

    @classmethod
    async def get_environment_history(
        cls,
        query_db: AsyncSession,
        base_id: Optional[str] = None,
        plot_id: Optional[str] = None,
        device_id: Optional[int] = None,
        metric_codes: Optional[Iterable[str]] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(AgriSensorObservation, AgriDevice).join(
            AgriDevice, AgriSensorObservation.device_id == AgriDevice.id
        )
        conditions = []
        if base_id:
            conditions.append(AgriDevice.base_id == base_id)
        if plot_id:
            conditions.append(AgriDevice.plot_id == plot_id)
        if device_id:
            conditions.append(AgriDevice.id == device_id)
        metric_code_list = [item for item in (metric_codes or []) if item]
        if metric_code_list:
            conditions.append(AgriSensorObservation.metric_code.in_(metric_code_list))
        normalized_start = cls._normalize_datetime(start_time)
        normalized_end = cls._normalize_datetime(end_time)
        if normalized_start:
            conditions.append(AgriSensorObservation.observed_at >= normalized_start)
        if normalized_end:
            conditions.append(AgriSensorObservation.observed_at <= normalized_end)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(AgriSensorObservation.observed_at.asc()).limit(20000)
        rows = (await query_db.execute(stmt)).all()
        return [
            {
                'deviceId': device.id,
                'deviceAddr': device.vendor_device_addr,
                'deviceName': device.device_name,
                'baseId': device.base_id,
                'plotId': observation.plot_id,
                **cls._observation_to_metric(observation),
            }
            for observation, device in rows
        ]

    @classmethod
    async def get_environment_alerts(
        cls,
        query_db: AsyncSession,
        base_id: Optional[str] = None,
        plot_id: Optional[str] = None,
        device_id: Optional[int] = None,
        status: Optional[str] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
    ) -> Dict[str, Any]:
        latest_list = await cls.get_latest_environment(query_db, base_id, plot_id, device_id)
        device_alerts = []
        environment_alerts = []
        now = datetime.now(timezone.utc)

        for item in latest_list:
            metrics = item.get('metrics') or {}
            observed_at = cls._normalize_datetime(item.get('observedAt'))
            device_name = item.get('deviceName') or item.get('deviceAddr')
            base_alert = {
                'deviceId': item.get('deviceId'),
                'deviceAddr': item.get('deviceAddr'),
                'deviceName': device_name,
                'baseId': item.get('baseId'),
                'plotId': item.get('plotId'),
                'observedAt': item.get('observedAt'),
            }

            if item.get('deviceStatus') == 'offline':
                device_alerts.append(
                    {
                        **base_alert,
                        'type': 'device',
                        'status': 'offline',
                        'level': 'high',
                        'title': '设备离线',
                        'content': f'{device_name} 当前处于离线状态。',
                    }
                )
            if observed_at and now - observed_at > timedelta(minutes=AgriIotConfig.agri_iot_stale_minutes):
                device_alerts.append(
                    {
                        **base_alert,
                        'type': 'device',
                        'status': 'warning',
                        'level': 'medium',
                        'title': '数据长时间未更新',
                        'content': f'{device_name} 超过 {AgriIotConfig.agri_iot_stale_minutes} 分钟未更新。',
                    }
                )
            battery_value = cls._metric_value(metrics.get('battery_level'))
            if battery_value is not None and battery_value < AgriIotConfig.agri_iot_low_battery_percent:
                device_alerts.append(
                    {
                        **base_alert,
                        'type': 'device',
                        'status': 'warning',
                        'level': 'medium',
                        'title': '设备低电量',
                        'content': f'{device_name} 电量 {battery_value:g}%，请安排维护。',
                    }
                )

            for metric_code, metric in metrics.items():
                alarm_level = metric.get('alarmLevel')
                if alarm_level not in (None, 0):
                    device_alerts.append(
                        {
                            **base_alert,
                            'type': 'device',
                            'status': 'alarm',
                            'level': 'high',
                            'title': '传感器报警',
                            'content': metric.get('alarmInfo') or f'{metric_code} 报警等级 {alarm_level}',
                        }
                    )

            humidity = cls._metric_value(metrics.get('relative_humidity'))
            if humidity is not None and humidity >= AgriIotConfig.agri_iot_high_humidity_percent:
                environment_alerts.append(
                    {
                        **base_alert,
                        'type': 'environment',
                        'status': 'warning',
                        'level': 'medium',
                        'title': '连续高湿风险',
                        'content': f'相对湿度 {humidity:g}%，达到病害适生预警阈值。',
                    }
                )

            air_temp = cls._metric_value(metrics.get('air_temperature'))
            if air_temp is not None and (
                air_temp < AgriIotConfig.agri_iot_air_temp_min_c
                or air_temp > AgriIotConfig.agri_iot_air_temp_max_c
            ):
                environment_alerts.append(
                    {
                        **base_alert,
                        'type': 'environment',
                        'status': 'warning',
                        'level': 'medium',
                        'title': '空气温度异常',
                        'content': f'空气温度 {air_temp:g}℃，超出配置阈值。',
                    }
                )

            soil_moisture = cls._metric_value(metrics.get('soil_moisture'))
            if soil_moisture is not None and (
                soil_moisture < AgriIotConfig.agri_iot_soil_moisture_min_percent
                or soil_moisture > AgriIotConfig.agri_iot_soil_moisture_max_percent
            ):
                environment_alerts.append(
                    {
                        **base_alert,
                        'type': 'environment',
                        'status': 'warning',
                        'level': 'medium',
                        'title': '土壤水分异常',
                        'content': f'土壤水分 {soil_moisture:g}%，请结合地块情况处理。',
                    }
                )

            co2_value = cls._metric_value(metrics.get('co2_concentration'))
            if co2_value is not None and co2_value > AgriIotConfig.agri_iot_co2_max_ppm:
                environment_alerts.append(
                    {
                        **base_alert,
                        'type': 'environment',
                        'status': 'warning',
                        'level': 'medium',
                        'title': 'CO2 浓度异常',
                        'content': f'CO2 浓度 {co2_value:g} ppm，超过配置阈值。',
                    }
                )

        if status:
            device_alerts = [item for item in device_alerts if item.get('status') == status]
            environment_alerts = [item for item in environment_alerts if item.get('status') == status]

        return {
            'deviceAlerts': device_alerts,
            'environmentAlerts': environment_alerts,
            'total': len(device_alerts) + len(environment_alerts),
        }

    @classmethod
    async def get_sync_logs(cls, query_db: AsyncSession, sync_type: Optional[str] = None, limit: int = 50):
        stmt = select(AgriSyncLog)
        if sync_type:
            stmt = stmt.where(AgriSyncLog.sync_type == sync_type)
        stmt = stmt.order_by(desc(AgriSyncLog.started_at)).limit(limit)
        logs = (await query_db.execute(stmt)).scalars().all()
        return [
            {
                'id': log.id,
                'syncType': log.sync_type,
                'deviceAddr': log.device_addr,
                'startTime': cls._iso(log.start_time),
                'endTime': cls._iso(log.end_time),
                'status': log.status,
                'totalCount': log.total_count,
                'successCount': log.success_count,
                'duplicateCount': log.duplicate_count,
                'failedCount': log.failed_count,
                'errorMessage': log.error_message,
                'startedAt': cls._iso(log.started_at),
                'finishedAt': cls._iso(log.finished_at),
            }
            for log in logs
        ]

    @classmethod
    async def sync_realtime(cls, device_addrs: Optional[List[str]] = None) -> Dict[str, Any]:
        return await cls._forward_gateway('/sync/realtime', {'deviceAddrs': device_addrs or []})

    @classmethod
    async def sync_history(cls, body: AgriHistorySyncModel) -> Dict[str, Any]:
        return await cls._forward_gateway('/sync/history', body.model_dump(by_alias=True))

    @classmethod
    async def _forward_gateway(cls, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not AgriIotConfig.agri_iot_gateway_url:
            return {
                'status': 'notConfigured',
                'message': '未配置 AGRI_IOT_GATEWAY_URL，后台已提供接口但未触发网关同步。',
            }
        url = f"{AgriIotConfig.agri_iot_gateway_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    @classmethod
    async def _upsert_device(cls, query_db: AsyncSession, record: Any, observed_at: datetime) -> AgriDevice:
        stmt = select(AgriDevice).where(
            and_(
                AgriDevice.vendor_name == record.vendor_name,
                AgriDevice.vendor_device_addr == record.device_addr,
            )
        )
        device = (await query_db.execute(stmt)).scalar_one_or_none()
        if not device:
            device = AgriDevice(vendor_name=record.vendor_name, vendor_device_addr=record.device_addr)
            query_db.add(device)
        device.base_id = cls._to_text(record.base_id) if record.base_id is not None else device.base_id
        device.plot_id = cls._to_text(record.plot_id) if record.plot_id is not None else device.plot_id
        device.device_name = record.device_name or device.device_name
        device.device_code = record.device_code or device.device_code
        device.group_id = cls._to_text(record.group_id) if record.group_id is not None else device.group_id
        device.longitude = record.longitude if record.longitude is not None else device.longitude
        device.latitude = record.latitude if record.latitude is not None else device.latitude
        device.device_status = record.device_status or device.device_status
        device.save_data_interval = record.save_data_interval or device.save_data_interval
        device.offline_interval = record.offline_interval or device.offline_interval
        device.last_seen_at = observed_at
        return device

    @classmethod
    async def _get_mapping(
        cls,
        query_db: AsyncSession,
        device_addr: str,
        node_id: str,
        register_id: str,
    ) -> Optional[AgriMetricMapping]:
        stmt = select(AgriMetricMapping).where(
            and_(
                AgriMetricMapping.vendor_device_addr == device_addr,
                AgriMetricMapping.node_id == node_id,
                AgriMetricMapping.register_id == register_id,
                AgriMetricMapping.enabled.is_(True),
            )
        )
        return (await query_db.execute(stmt)).scalar_one_or_none()

    @classmethod
    def _resolve_metric_code(
        cls,
        mapping: Optional[AgriMetricMapping],
        incoming_metric_code: Optional[str],
        vendor_name: Optional[str] = None,
        node_id: Optional[str] = None,
        register_id: Optional[str] = None,
    ) -> Optional[str]:
        if mapping and mapping.metric_code:
            return mapping.metric_code
        if incoming_metric_code:
            return incoming_metric_code
        if vendor_name == '0531yun':
            return DEFAULT_0531_NODE_REGISTER_MAPPING.get((node_id or '', register_id or ''))
        return None

    @classmethod
    def _apply_mapping_value(cls, value: Decimal, mapping: AgriMetricMapping) -> Decimal:
        coefficient = Decimal(mapping.coefficient) if mapping.coefficient is not None else Decimal('1')
        offset = Decimal(mapping.offset) if mapping.offset is not None else Decimal('0')
        mapped = value * coefficient + offset
        if mapping.digits is not None and mapping.digits >= 0:
            quant = Decimal('1') if mapping.digits == 0 else Decimal(f"1e-{mapping.digits}")
            mapped = mapped.quantize(quant)
        return mapped

    @classmethod
    async def _write_latest_snapshots(cls, redis_client: Any, snapshots: Iterable[Dict[str, Any]]) -> None:
        if not redis_client:
            return
        for snapshot in snapshots:
            key = f"agri:device:{snapshot.get('deviceId')}:latest"
            await redis_client.set(
                key,
                json.dumps(snapshot, ensure_ascii=False, default=str),
                ex=AgriIotConfig.agri_iot_snapshot_ttl_seconds,
            )

    @classmethod
    def _device_to_dict(cls, device: AgriDevice) -> Dict[str, Any]:
        return {
            'deviceId': device.id,
            'baseId': device.base_id,
            'plotId': device.plot_id,
            'vendorName': device.vendor_name,
            'deviceAddr': device.vendor_device_addr,
            'deviceName': device.device_name,
            'deviceCode': device.device_code,
            'groupId': device.group_id,
            'longitude': device.longitude,
            'latitude': device.latitude,
            'deviceStatus': device.device_status,
            'saveDataInterval': device.save_data_interval,
            'offlineInterval': device.offline_interval,
            'lastSeenAt': cls._iso(device.last_seen_at),
            'createdAt': cls._iso(device.created_at),
            'updatedAt': cls._iso(device.updated_at),
        }

    @classmethod
    def _observation_to_metric(cls, observation: AgriSensorObservation) -> Dict[str, Any]:
        return {
            'metricCode': observation.metric_code,
            'value': cls._float_or_none(observation.metric_value),
            'unit': observation.metric_unit,
            'nodeId': observation.node_id,
            'registerId': observation.register_id,
            'factorName': (observation.raw_payload or {}).get('registerName'),
            'alarmLevel': observation.alarm_level,
            'alarmInfo': observation.alarm_info,
            'qualityFlag': observation.quality_flag,
            'observedAt': cls._iso(observation.observed_at),
        }

    @classmethod
    def _normalize_datetime(cls, value: Any) -> Optional[datetime]:
        if value is None or value == '':
            return None
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            result = datetime.fromtimestamp(timestamp, timezone.utc)
        elif isinstance(value, str):
            text_value = value.strip()
            if not text_value:
                return None
            if re.fullmatch(r'\d+(\.\d+)?', text_value):
                timestamp = float(text_value)
                timestamp = timestamp / 1000 if timestamp > 10_000_000_000 else timestamp
                result = datetime.fromtimestamp(timestamp, timezone.utc)
            else:
                result = datetime.fromisoformat(text_value.replace('Z', '+00:00'))
        else:
            return None
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result

    @classmethod
    def _to_decimal(cls, value: Any) -> Optional[Decimal]:
        if value is None or value == '':
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, Decimal):
            return value
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            match = re.search(r'-?\d+(?:\.\d+)?', str(value).replace(',', '').strip())
            if not match:
                return None
            return Decimal(match.group(0))
        except (InvalidOperation, ValueError):
            return None

    @classmethod
    def _metric_value(cls, metric: Optional[Dict[str, Any]]) -> Optional[float]:
        if not metric:
            return None
        value = metric.get('value')
        return float(value) if isinstance(value, (int, float)) else None

    @classmethod
    def _float_or_none(cls, value: Any) -> Optional[float]:
        if value is None:
            return None
        return float(value)

    @classmethod
    def _to_text(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    @classmethod
    def _iso(cls, value: Optional[datetime]) -> Optional[str]:
        if not value:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
