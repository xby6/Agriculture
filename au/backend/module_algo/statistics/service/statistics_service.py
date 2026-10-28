import asyncio
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.dept_do import SysDept
from module_algo.container.entity.do.container_do import Container
from module_algo.file.entity.do.file_do import File
from module_algo.node.entity.do.node_do import NodeInfo
from module_algo.statistics.dao.statistics_dao import StatisticsDao
from module_algo.task.entity.do.task_do import Task
from utils.log_util import logger


class StatisticsService:
    """统计服务。"""

    @staticmethod
    async def get_all_statistics_services(db: AsyncSession):
        """获取所有模块的统计数据。"""
        try:
            logger.info("开始获取所有模块的统计数据")
            statistics = await StatisticsDao.get_all_statistics(db)
            logger.info("成功获取所有模块的统计数据")
            return statistics
        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            raise e

    @staticmethod
    async def get_agriculture_overview_services(db: AsyncSession):
        """获取农业平台大屏和业务中心的真实总览数据。"""
        today_start = datetime.combine(datetime.now().date(), time.min)
        seven_days_ago = today_start - timedelta(days=6)
        online_statuses = {'0', 'online', 'running', 'success', 'normal', 'healthy', '正常', '在线', '健康'}

        base_count = (await db.execute(
            select(func.count(SysDept.dept_id)).where(
                SysDept.parent_id != 0,
                SysDept.del_flag == '0',
                SysDept.status == '0',
            )
        )).scalar() or 0

        base_rows = (await db.execute(
            select(SysDept.dept_id, SysDept.dept_name).where(
                SysDept.parent_id != 0,
                SysDept.del_flag == '0',
                SysDept.status == '0',
            ).order_by(SysDept.order_num, SysDept.dept_id)
        )).all()

        field_count = (await db.execute(select(func.count(NodeInfo.id)))).scalar() or 0
        node_status_rows = (await db.execute(
            select(NodeInfo.status, func.count(NodeInfo.id)).group_by(NodeInfo.status)
        )).all()
        online_count = sum(
            count for status, count in node_status_rows
            if str(status or '').strip().lower() in online_statuses
        )
        device_online_rate = round(online_count / field_count * 100, 1) if field_count else None

        file_rows = (await db.execute(
            select(File)
            .order_by(File.upload_time.desc(), File.id.desc())
        )).scalars().all()
        file_count = len(file_rows)
        file_asset_types = StatisticsService._build_file_asset_types(file_rows)
        latest_file_rows = file_rows[:8]

        model_count = (await db.execute(select(func.count(Container.id)))).scalar() or 0
        container_rows = (await db.execute(
            select(Container).order_by(Container.id)
        )).scalars().all()
        compute_platform = await StatisticsService._get_compute_platform_status(container_rows)
        task_count = (await db.execute(select(func.count(Task.id)))).scalar() or 0
        today_task_count = (await db.execute(
            select(func.count(Task.id)).where(Task.init_time >= today_start)
        )).scalar() or 0
        task_state_rows = (await db.execute(
            select(Task.state, func.count(Task.id)).group_by(Task.state)
        )).all()
        task_date_rows = (await db.execute(
            select(func.date(Task.init_time), func.count(Task.id))
            .where(Task.init_time >= seven_days_ago)
            .group_by(func.date(Task.init_time))
            .order_by(func.date(Task.init_time))
        )).all()

        latest_task_rows = (await db.execute(
            select(Task)
            .order_by(Task.init_time.desc(), Task.id.desc())
            .limit(8)
        )).scalars().all()

        node_rows = (await db.execute(
            select(NodeInfo, File.dept)
            .outerjoin(File, NodeInfo.dir == File.id)
            .order_by(NodeInfo.id)
            .limit(80)
        )).all()
        ndvi_summary = await StatisticsService._get_remote_sensing_index_summary(db)
        disease_summary = await StatisticsService._get_rice_disease_detection_summary(db, file_rows)

        data_sources = [
            {'source': '基地组织', 'table': 'sys_dept', 'count': base_count, 'status': '已接入' if base_count else '暂无数据'},
            {'source': '地块/设备节点', 'table': 'node_info', 'count': field_count, 'status': '已接入' if field_count else '暂无数据'},
            {'source': '农业数据资产', 'table': 'file', 'count': file_count, 'status': '已接入' if file_count else '暂无数据'},
            {'source': '模型服务', 'table': 'container', 'count': model_count, 'status': '已接入' if model_count else '暂无数据'},
            {'source': '模型任务', 'table': 'task', 'count': task_count, 'status': '已接入' if task_count else '暂无数据'},
            {'source': '环境传感器', 'table': None, 'count': 0, 'status': '未接入真实数据表'},
            {'source': '病害调查', 'table': None, 'count': 0, 'status': '未接入真实数据表'},
            {'source': '遥感指数', 'table': None, 'count': 0, 'status': '未接入真实数据表'},
        ]

        if ndvi_summary['count']:
            for item in data_sources:
                source_text = str(item.get('source') or '')
                if '遥感' in source_text or '閬ユ劅' in source_text:
                    item['table'] = 'file'
                    item['count'] = ndvi_summary['count']
                    item['status'] = '已接入'
                    break

        if disease_summary.get('sample_count') or disease_summary.get('detection_target_count'):
            for item in data_sources:
                source_text = str(item.get('source') or '')
                if '病害' in source_text or '鐥呭' in source_text:
                    item['table'] = 'task/file'
                    item['count'] = disease_summary.get('sample_count') or disease_summary.get('detection_target_count') or 0
                    item['status'] = '已接入'
                    break

        return {
            'overview': {
                'base_count': base_count,
                'field_count': field_count,
                'planting_area_mu': None,
                'device_online_rate': device_online_rate,
                'today_model_tasks': today_task_count,
                'data_asset_count': file_count,
                'model_service_count': model_count,
            },
            'bases': [{'id': dept_id, 'name': dept_name} for dept_id, dept_name in base_rows],
            'field_nodes': [
                {
                    'id': node.id,
                    'name': node.name,
                    'status': node.status,
                    'longitude': node.longitude,
                    'latitude': node.latitude,
                    'dept_id': dept_id,
                }
                for node, dept_id in node_rows
            ],
            'environment': None,
            'disease': disease_summary,
            'charts': {
                'node_status': compute_platform['status_counts'],
                'compute_platform': compute_platform,
                'file_type': file_asset_types,
                'task_state': [{'name': str(state or '未标记'), 'value': count} for state, count in task_state_rows],
                'task_by_date': [{'date': str(date), 'count': count} for date, count in task_date_rows],
                'environment_history': [],
                'disease_prediction': [],
                'ndvi_trend': ndvi_summary['trend'],
            },
            'latest_tasks': [
                {
                    'id': task.id,
                    'name': task.name,
                    'algo': task.algo,
                    'state': task.state,
                    'init_time': task.init_time,
                    'end_time': task.end_time,
                }
                for task in latest_task_rows
            ],
            'latest_files': [
                StatisticsService._serialize_latest_file(file)
                for file in latest_file_rows
            ],
            'data_sources': data_sources,
            'warnings': [
                item for item in data_sources
                if item['status'] in {'暂无数据', '未接入真实数据表'}
            ],
            'updated_at': datetime.now(),
        }

    @staticmethod
    def _build_file_asset_types(file_rows):
        file_by_id = {file.id: file for file in file_rows}
        folder_counters = Counter()
        suffix_counters = Counter()

        for file in file_rows:
            type_text = str(file.type or '').strip().lower()
            if type_text == 'dir':
                continue

            folder = StatisticsService._nearest_folder(file, file_by_id)
            if folder:
                label = StatisticsService._compact_asset_label(folder.name, '未命名文件夹')
                folder_counters[label] += 1
                continue

            suffix = StatisticsService._file_suffix(file)
            suffix_counters[f'{suffix.upper()}文件' if suffix else '无后缀文件'] += 1

        counters = folder_counters + suffix_counters

        return [
            {'name': name, 'value': value}
            for name, value in counters.most_common(8)
        ]

    @staticmethod
    def _nearest_folder(file, file_by_id):
        root = getattr(file, 'root', None)
        visited = set()
        while root is not None and root not in visited:
            visited.add(root)
            parent = file_by_id.get(root)
            if not parent:
                return None
            if str(parent.type or '').strip().lower() == 'dir':
                return parent
            root = getattr(parent, 'root', None)
        return None

    @staticmethod
    def _serialize_latest_file(file):
        type_text = str(file.type or '').strip().lower()
        is_dir = type_text == 'dir'
        suffix = StatisticsService._file_suffix(file)
        return {
            'id': file.id,
            'name': file.name or '未命名数据',
            'type': '目录' if is_dir else (suffix.upper() if suffix else '文件'),
            'size': file.size,
            'upload_time': file.upload_time,
            'category': '数据目录' if is_dir else '数据文件',
        }

    @staticmethod
    def _compact_asset_label(value, fallback):
        label = str(value or '').strip() or fallback
        return label if len(label) <= 10 else f'{label[:10]}...'

    @staticmethod
    def _file_suffix(file):
        for value in (file.name, file.path, file.type):
            suffix = Path(str(value or '')).suffix.lower().lstrip('.')
            if suffix:
                return suffix

        type_text = str(file.type or '').strip().lower().lstrip('.')
        if type_text and type_text != 'dir':
            return type_text
        return ''

    @staticmethod
    async def _get_rice_disease_detection_summary(db: AsyncSession, file_rows):
        """Aggregate real Pyramid-YOLO disease detection task outputs for dashboard cards."""
        empty_summary = {
            'current_di': None,
            'forecast_di_7d': None,
            'risk_level': None,
            'main_disease': None,
            'suggestion': None,
            'sample_count': None,
            'detection_target_count': None,
            'abnormal_plot_count': None,
            'today_alert_count': None,
            'high_risk_count': None,
            'medium_risk_count': None,
            'low_risk_count': None,
            'normal_risk_count': None,
            'risk_distribution': [],
            'max_confidence': None,
            'latest_task_id': None,
            'latest_detection_time': None,
        }

        task_rows = (await db.execute(
            select(Task)
            .where(
                Task.result.isnot(None),
                Task.result > 0,
                (
                    Task.remark.ilike('%水稻病害检测页面提交%') |
                    Task.algo.ilike('%RiceDisease%') |
                    Task.algo.ilike('%PyramidYOLO%') |
                    Task.algo.ilike('%Pyramid-YOLO%')
                ),
            )
            .order_by(Task.end_time.desc(), Task.init_time.desc(), Task.id.desc())
            .limit(50)
        )).scalars().all()

        if not task_rows:
            return empty_summary

        files_by_root = defaultdict(list)
        for file in file_rows:
            files_by_root[getattr(file, 'root', None)].append(file)

        records = []
        for task in task_rows:
            result_files = StatisticsService._collect_child_files(task.result, files_by_root)
            summary_file = next((file for file in result_files if str(file.name or '').lower() == 'summary.json'), None)
            detections_file = next((file for file in result_files if str(file.name or '').lower() == 'detections.json'), None)
            summary = StatisticsService._read_json_payload(summary_file) or {}
            if not isinstance(summary, dict):
                summary = {}
            detections_payload = StatisticsService._read_json_payload(detections_file)
            detections = StatisticsService._normalize_detections(detections_payload)
            if not summary and not detections:
                continue

            input_images = StatisticsService._to_int(summary.get('input_images'))
            if input_images is None:
                input_images = StatisticsService._count_result_images(result_files)
            total_detections = StatisticsService._to_int(summary.get('total_detections'))
            if total_detections is None:
                total_detections = len(detections)

            max_confidence = StatisticsService._max_detection_confidence(summary, detections)
            disease_name = StatisticsService._main_detection_class(detections) or summary.get('disease_type') or 'disease'
            risk_key, risk_label = StatisticsService._classify_detection_risk(total_detections, max_confidence)

            records.append({
                'task_id': task.id,
                'task_name': task.name,
                'time': task.end_time or task.init_time,
                'input_images': input_images or 0,
                'total_detections': total_detections or 0,
                'max_confidence': max_confidence,
                'disease_name': disease_name,
                'risk_key': risk_key,
                'risk_label': risk_label,
            })

        if not records:
            return empty_summary

        latest = records[0]
        risk_counts = Counter(record['risk_key'] for record in records)
        today = datetime.now().date()
        today_alert_count = sum(
            1 for record in records
            if record['risk_key'] in {'high', 'medium'} and record['time'] and record['time'].date() == today
        )
        risk_labels = {'high': '高风险', 'medium': '中风险', 'low': '低风险', 'normal': '正常'}
        confidence_percent = None
        if latest['max_confidence'] is not None:
            confidence_percent = round(latest['max_confidence'] * 100, 1)

        return {
            'current_di': None,
            'forecast_di_7d': None,
            'risk_level': latest['risk_label'],
            'main_disease': latest['disease_name'],
            'suggestion': StatisticsService._disease_suggestion(latest['risk_key']),
            'sample_count': latest['input_images'],
            'image_count': latest['input_images'],
            'detection_target_count': latest['total_detections'],
            'total_detections': latest['total_detections'],
            'abnormal_plot_count': latest['total_detections'],
            'today_alert_count': today_alert_count,
            'high_risk_count': risk_counts.get('high', 0),
            'medium_risk_count': risk_counts.get('medium', 0),
            'low_risk_count': risk_counts.get('low', 0),
            'normal_risk_count': risk_counts.get('normal', 0),
            'risk_distribution': [
                {'key': key, 'name': risk_labels[key], 'value': risk_counts.get(key, 0)}
                for key in ('high', 'medium', 'low', 'normal')
            ],
            'future_risk': latest['risk_label'],
            'max_confidence': confidence_percent,
            'latest_task_id': latest['task_id'],
            'latest_detection_time': latest['time'],
        }

    @staticmethod
    def _collect_child_files(root_id, files_by_root):
        collected = []
        visited = set()
        stack = [root_id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for child in files_by_root.get(current, []):
                collected.append(child)
                if str(child.type or '').strip().lower() == 'dir':
                    stack.append(child.id)
        return collected

    @staticmethod
    def _read_json_payload(file):
        if not file or not getattr(file, 'path', None):
            return None
        file_path = StatisticsService._resolve_upload_path(Path(str(file.path)))
        if not file_path.exists() or not file_path.is_file():
            return None
        try:
            return json.loads(file_path.read_text(encoding='utf-8-sig'))
        except Exception as exc:
            logger.warning(f"Failed to read disease result json {file_path}: {exc}")
            return None

    @staticmethod
    def _normalize_detections(payload):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ('detections', 'items', 'results'):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []

    @staticmethod
    def _count_result_images(files):
        image_suffixes = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        return sum(
            1 for file in files
            if Path(str(file.name or file.path or '')).suffix.lower() in image_suffixes
        )

    @staticmethod
    def _to_int(value):
        try:
            if value is None or value == '':
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value):
        try:
            if value is None or value == '':
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _max_detection_confidence(summary, detections):
        values = []
        images = summary.get('images') if isinstance(summary, dict) else []
        if isinstance(images, list):
            for image in images:
                value = StatisticsService._to_float(image.get('max_confidence') if isinstance(image, dict) else None)
                if value is not None:
                    values.append(value)
        for item in detections:
            if not isinstance(item, dict):
                continue
            value = StatisticsService._to_float(
                item.get('confidence') or item.get('conf') or item.get('score') or item.get('probability')
            )
            if value is not None:
                values.append(value)
        if not values:
            return None
        max_value = max(values)
        return max_value / 100 if max_value > 1 else max_value

    @staticmethod
    def _main_detection_class(detections):
        names = []
        for item in detections:
            if not isinstance(item, dict):
                continue
            name = item.get('class_name') or item.get('class') or item.get('label') or item.get('name')
            if name:
                names.append(str(name))
        if not names:
            return None
        return Counter(names).most_common(1)[0][0]

    @staticmethod
    def _classify_detection_risk(total_detections, max_confidence):
        total = total_detections or 0
        confidence = max_confidence or 0
        if total >= 20 or confidence >= 0.75:
            return 'high', '高风险'
        if total >= 8 or confidence >= 0.55:
            return 'medium', '中风险'
        if total > 0:
            return 'low', '低风险'
        return 'normal', '正常'

    @staticmethod
    def _disease_suggestion(risk_key):
        suggestions = {
            'high': '检测目标较多，建议尽快开展重点巡田和复核。',
            'medium': '检测到中等病害风险，建议加强近24小时巡查。',
            'low': '检测到少量疑似病斑，建议持续观察。',
            'normal': '暂未检测到明显病害目标。',
        }
        return suggestions.get(risk_key, suggestions['normal'])

    @staticmethod
    async def _get_compute_platform_status(container_rows):
        empty_status = {
            'total': 0,
            'running': 0,
            'abnormal': 0,
            'offline': 0,
            'unconfigured': 0,
            'running_tasks': 0,
            'status_counts': [],
            'services': [],
        }
        if not container_rows:
            return empty_status

        async def probe(client, container):
            base_url = str(getattr(container, 'url', '') or '').strip().rstrip('/')
            service = {
                'id': container.id,
                'name': container.name,
                'url': base_url,
                'type': container.type,
                'status': '未配置',
                'status_key': 'unconfigured',
                'running_tasks': 0,
            }
            if not base_url:
                return service
            try:
                response = await client.get(f'{base_url}/running-tasks')
                if 200 <= response.status_code < 400:
                    payload = response.json()
                    tasks = payload.get('running_tasks') if isinstance(payload, dict) else []
                    service['status'] = '运行中'
                    service['status_key'] = 'running'
                    service['running_tasks'] = len(tasks) if isinstance(tasks, list) else 0
                    return service
                service['status'] = '异常'
                service['status_key'] = 'abnormal'
                return service
            except httpx.ConnectError:
                service['status'] = '离线'
                service['status_key'] = 'offline'
                return service
            except httpx.TimeoutException:
                service['status'] = '离线'
                service['status_key'] = 'offline'
                return service
            except httpx.HTTPError:
                service['status'] = '异常'
                service['status_key'] = 'abnormal'
                return service

        timeout = httpx.Timeout(1.5, connect=0.6)
        async with httpx.AsyncClient(timeout=timeout) as client:
            probe_results = await asyncio.gather(
                *(probe(client, container) for container in container_rows),
                return_exceptions=True,
            )

        services = []
        for index, result in enumerate(probe_results):
            if isinstance(result, dict):
                services.append(result)
                continue
            container = container_rows[index]
            services.append({
                'id': container.id,
                'name': container.name,
                'url': str(getattr(container, 'url', '') or '').strip(),
                'type': container.type,
                'status': '异常',
                'status_key': 'abnormal',
                'running_tasks': 0,
            })

        status_names = {
            'running': '运行中',
            'abnormal': '异常',
            'offline': '离线',
            'unconfigured': '未配置',
        }
        status_counter = Counter(service['status_key'] for service in services)
        status_counts = [
            {'key': key, 'name': status_names[key], 'value': status_counter.get(key, 0)}
            for key in ('running', 'abnormal', 'offline', 'unconfigured')
            if status_counter.get(key, 0)
        ]
        return {
            'total': len(services),
            'running': status_counter.get('running', 0),
            'abnormal': status_counter.get('abnormal', 0),
            'offline': status_counter.get('offline', 0),
            'unconfigured': status_counter.get('unconfigured', 0),
            'running_tasks': sum(service.get('running_tasks') or 0 for service in services),
            'status_counts': status_counts,
            'services': services,
        }

    @staticmethod
    async def _get_remote_sensing_index_summary(db: AsyncSession):
        """Parse uploaded spectral CSV files and aggregate NDVI/MDVI values by date."""
        file_rows = (await db.execute(
            select(File.name, File.path, File.upload_time)
            .where(File.path.isnot(None))
            .order_by(File.upload_time.desc(), File.id.desc())
        )).all()

        candidates = []
        seen_paths = set()
        for name, path, upload_time in file_rows:
            file_path = StatisticsService._resolve_upload_path(Path(str(path or '')))
            suffix = file_path.suffix.lower() or Path(str(name or '')).suffix.lower()
            if suffix != '.csv':
                continue
            path_key = str(file_path)
            if path_key in seen_paths:
                continue
            candidates.append((file_path, name or file_path.name, upload_time))
            seen_paths.add(path_key)

        upload_dirs = [Path('upload_file'), Path(__file__).resolve().parents[3] / 'upload_file']
        for upload_dir in upload_dirs:
            if not upload_dir.exists():
                continue
            for file_path in sorted(upload_dir.glob('*.csv'), key=lambda item: item.stat().st_mtime, reverse=True):
                path_key = str(file_path)
                if path_key in seen_paths:
                    continue
                candidates.append((file_path, file_path.name, datetime.fromtimestamp(file_path.stat().st_mtime)))
                seen_paths.add(path_key)

        best_summary = {'trend': [], 'count': 0}
        for file_path, name, upload_time in candidates:
            summary = StatisticsService._parse_spectral_csv(file_path, name, upload_time)
            if len(summary['trend']) > len(best_summary['trend']):
                best_summary = summary

        return best_summary

    @staticmethod
    def _resolve_upload_path(file_path: Path):
        if file_path.exists():
            return file_path

        backend_root = Path(__file__).resolve().parents[3]
        backend_relative_path = backend_root / file_path
        if backend_relative_path.exists():
            return backend_relative_path

        return file_path

    @staticmethod
    def _parse_spectral_csv(file_path: Path, name: str, upload_time):
        if not file_path.exists() or not file_path.is_file():
            return {'trend': [], 'count': 0}

        try:
            with file_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
                reader = csv.DictReader(csv_file)
                fieldnames = [str(field or '').strip() for field in (reader.fieldnames or [])]
                normalized_fields = {field.lower(): field for field in fieldnames}
                value_field = normalized_fields.get('mdvi') or normalized_fields.get('ndvi')
                date_field = (
                    normalized_fields.get('day') or
                    normalized_fields.get('date') or
                    normalized_fields.get('time') or
                    normalized_fields.get('采样日期')
                )
                if not value_field or not date_field:
                    return {'trend': [], 'count': 0}

                values_by_date = defaultdict(list)
                for row in reader:
                    date_label = StatisticsService._format_spectral_date(row.get(date_field), upload_time)
                    raw_value = row.get(value_field)
                    try:
                        value = float(raw_value)
                    except (TypeError, ValueError):
                        continue
                    if -1 <= value <= 1:
                        values_by_date[date_label].append(value)

            trend = [
                {
                    'date': date_label,
                    'value': round(sum(values) / len(values), 4),
                    'count': len(values),
                    'source': name,
                }
                for date_label, values in sorted(values_by_date.items())
                if values
            ]
            return {'trend': trend, 'count': sum(item['count'] for item in trend)}
        except Exception as exc:
            logger.warning(f"Failed to parse spectral CSV {file_path}: {exc}")
            return {'trend': [], 'count': 0}

    @staticmethod
    def _format_spectral_date(raw_value, fallback_time):
        text = str(raw_value or '').strip()
        for fmt in ('%Y%m%d', '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'):
            try:
                return datetime.strptime(text[:10], fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        if fallback_time:
            return fallback_time.strftime('%Y-%m-%d') if hasattr(fallback_time, 'strftime') else str(fallback_time)
        return text or 'unknown'
