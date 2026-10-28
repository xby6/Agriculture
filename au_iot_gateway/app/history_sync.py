from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

from app.backend_client import BackendClient
from app.client import Cloud0531Client
from app.config import GatewaySettings, get_settings
from app.normalizer import build_telemetry_batch, normalize_history_response

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class HistorySyncService:
    def __init__(
        self,
        settings: Optional[GatewaySettings] = None,
        cloud_client: Optional[Cloud0531Client] = None,
        backend_client: Optional[BackendClient] = None,
    ):
        self.settings = settings or get_settings()
        self.cloud_client = cloud_client or Cloud0531Client(self.settings)
        self.backend_client = backend_client or BackendClient(self.settings)

    async def close(self) -> None:
        await self.cloud_client.close()
        await self.backend_client.close()

    async def sync_history(
        self,
        device_addr: str,
        start_time: str | datetime,
        end_time: str | datetime,
        node_id: str | int = -1,
    ) -> Dict[str, Any]:
        started = _parse_datetime(start_time)
        ended = _parse_datetime(end_time)
        segments = split_by_day(started, ended)
        totals = {
            'syncType': 'history',
            'deviceAddr': device_addr,
            'segments': len(segments),
            'totalCount': 0,
            'successCount': 0,
            'duplicateCount': 0,
            'failedCount': 0,
            'details': [],
        }

        for segment_start, segment_end in segments:
            start_text = segment_start.strftime(TIME_FORMAT)
            end_text = segment_end.strftime(TIME_FORMAT)
            response = await self.cloud_client.history_list(device_addr, node_id, start_text, end_text)
            records = normalize_history_response(response)
            payload = build_telemetry_batch(
                'history',
                records,
                device_addr=device_addr,
                start_time=start_text,
                end_time=end_text,
            )
            backend_result = await self.backend_client.post_telemetry(payload)
            data = backend_result.get('data') or backend_result
            totals['totalCount'] += int(data.get('totalCount') or 0)
            totals['successCount'] += int(data.get('successCount') or 0)
            totals['duplicateCount'] += int(data.get('duplicateCount') or 0)
            totals['failedCount'] += int(data.get('failedCount') or 0)
            totals['details'].append({'startTime': start_text, 'endTime': end_text, 'result': data})
        return totals


def split_by_day(start_time: datetime, end_time: datetime) -> List[tuple[datetime, datetime]]:
    if end_time < start_time:
        raise ValueError('endTime must be greater than or equal to startTime')
    segments = []
    cursor = start_time
    while cursor <= end_time:
        day_end = datetime.combine(cursor.date(), time.max).replace(tzinfo=cursor.tzinfo)
        segment_end = min(day_end, end_time)
        segments.append((cursor, segment_end))
        cursor = segment_end + timedelta(microseconds=1)
    return segments


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    try:
        return datetime.strptime(text, TIME_FORMAT)
    except ValueError:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
