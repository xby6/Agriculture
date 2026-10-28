import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


def parse_number(*values: Any) -> tuple[Optional[float], str]:
    for value in values:
        if value is None or value == '':
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value), 'normal'
        match = re.search(r'-?\d+(?:\.\d+)?', str(value).replace(',', '').strip())
        if match:
            return float(match.group(0)), 'normal'
    return None, 'invalid'


def parse_observed_at(value: Any) -> str:
    if value is None or value == '':
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        dt = datetime.fromtimestamp(timestamp, timezone.utc)
    else:
        text = str(value).strip()
        if re.fullmatch(r'\d+(\.\d+)?', text):
            timestamp = float(text)
            timestamp = timestamp / 1000 if timestamp > 10_000_000_000 else timestamp
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
        else:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def get_lng(item: Dict[str, Any]) -> Optional[float]:
    value = item.get('lng')
    if value is None:
        value = item.get('Lng')
    parsed, flag = parse_number(value)
    return parsed if flag == 'normal' else None


def get_lat(item: Dict[str, Any]) -> Optional[float]:
    parsed, flag = parse_number(item.get('lat'), item.get('Lat'))
    return parsed if flag == 'normal' else None


def normalize_realtime_response(response: Dict[str, Any], base_id: Optional[str] = None, plot_id: Optional[str] = None):
    records = []
    for item in _as_list(response.get('data')):
        records.append(normalize_realtime_item(item, base_id=base_id, plot_id=plot_id))
    return records


def normalize_realtime_item(item: Dict[str, Any], base_id: Optional[str] = None, plot_id: Optional[str] = None):
    record = {
        'vendorName': '0531yun',
        'deviceAddr': str(item.get('deviceAddr') or ''),
        'deviceName': item.get('deviceName'),
        'deviceCode': item.get('deviceCode'),
        'groupId': item.get('groupId'),
        'baseId': base_id,
        'plotId': plot_id,
        'longitude': get_lng(item),
        'latitude': get_lat(item),
        'deviceStatus': item.get('deviceStatus'),
        'saveDataInterval': _to_int(item.get('savedatainterval') or item.get('saveDataInterval')),
        'offlineInterval': _to_int(item.get('offlineinterval') or item.get('offlineInterval')),
        'observedAt': parse_observed_at(item.get('timeStamp') or item.get('recordTime') or item.get('recordTimeStr')),
        'metrics': [],
        'rawPayload': item,
    }
    for node in _as_list(item.get('dataItem')):
        node_id = node.get('nodeId')
        for register in _as_list(node.get('registerItem')):
            value, quality_flag = parse_number(register.get('value'), register.get('data'))
            record['metrics'].append(
                {
                    'nodeId': node_id,
                    'registerId': register.get('registerId'),
                    'factorName': register.get('registerName'),
                    'metricCode': register.get('metricCode'),
                    'value': value,
                    'unit': register.get('unit'),
                    'alarmLevel': _to_int(register.get('alarmLevel')),
                    'alarmInfo': register.get('alarmInfo'),
                    'qualityFlag': quality_flag,
                    'rawPayload': register,
                }
            )
    return record


def normalize_history_response(
    response: Dict[str, Any],
    base_id: Optional[str] = None,
    plot_id: Optional[str] = None,
):
    records = []
    for item in _as_list(response.get('data')):
        records.append(normalize_history_item(item, base_id=base_id, plot_id=plot_id))
    return records


def normalize_history_item(item: Dict[str, Any], base_id: Optional[str] = None, plot_id: Optional[str] = None):
    observed_at = parse_observed_at(item.get('recordTime') or item.get('recordTimeStr'))
    record = {
        'vendorName': '0531yun',
        'deviceAddr': str(item.get('deviceAddr') or ''),
        'baseId': base_id,
        'plotId': plot_id,
        'longitude': get_lng(item),
        'latitude': get_lat(item),
        'deviceStatus': item.get('deviceStatus'),
        'observedAt': observed_at,
        'metrics': [],
        'rawPayload': item,
    }
    for metric in _as_list(item.get('data')):
        value, quality_flag = parse_number(metric.get('value'), metric.get('text'))
        record['metrics'].append(
            {
                'nodeId': item.get('nodeId'),
                'registerId': metric.get('registerId'),
                'factorName': metric.get('registerName'),
                'metricCode': metric.get('metricCode'),
                'value': value,
                'unit': metric.get('unit'),
                'alarmLevel': _to_int(metric.get('alarmLevel')),
                'alarmInfo': metric.get('alarmInfo'),
                'qualityFlag': quality_flag,
                'rawPayload': metric,
            }
        )
    return record


def build_telemetry_batch(
    sync_type: str,
    records: Iterable[Dict[str, Any]],
    device_addr: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    return {
        'syncType': sync_type,
        'deviceAddr': device_addr,
        'startTime': start_time,
        'endTime': end_time,
        'records': [record for record in records if record.get('deviceAddr')],
    }


def _as_list(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ('list', 'rows', 'records', 'data'):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [value]
    return []


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
