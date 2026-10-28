from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime, timedelta
from module_algo.task.entity.do.task_do import Task
from module_algo.file.entity.do.file_do import File
from module_algo.container.entity.do.container_do import Container
from module_algo.node.entity.do.node_do import NodeInfo

class StatisticsDao:
    """统计数据访问对象"""
    
    @staticmethod
    async def get_task_statistics(db: AsyncSession) -> dict:
        try:
            total_tasks = (await db.execute(select(func.count(Task.id)))).scalar()
            
            # 确保按状态分组
            task_status_stats = (await db.execute(
                select(
                    Task.state, # 确保这里是 state 字段
                    func.count(Task.id).label('count')
                ).group_by(Task.state)
            )).all()
            
            # 简单的日期统计 (最近7天)
            seven_days_ago = datetime.now() - timedelta(days=7)
            # 注意: SQLite 和 MySQL 对日期的处理不同，这里假设是标准日期时间格式
            task_date_stats = (await db.execute(
                select(
                    func.date(Task.init_time).label('date'),
                    func.count(Task.id).label('count')
                ).filter(
                    Task.init_time >= seven_days_ago
                ).group_by(
                    func.date(Task.init_time)
                )
            )).all()
            
            return {
                'total': total_tasks,
                # 将结果转为 {status: 'running', count: 10} 格式
                'by_status': [{'status': str(item[0]), 'count': item[1]} for item in task_status_stats],
                'by_date': [{'date': str(item[0]), 'count': item[1]} for item in task_date_stats]
            }
        except Exception as e:
            print(f"Task Stats Error: {e}") # 建议加上日志
            return {'total': 0, 'by_status': [], 'by_date': []}
    
    @staticmethod
    async def get_file_statistics(db: AsyncSession) -> dict:
        try:
            total_files = (await db.execute(select(func.count(File.id)))).scalar()
            
            file_type_stats = (await db.execute(
                select(
                    File.type,
                    func.count(File.id).label('count')
                ).group_by(File.type)
            )).all()
            
            # 如果有 root 字段处理逻辑
            file_root_stats = (await db.execute(
                select(
                    File.root,
                    func.count(File.id).label('count')
                ).group_by(File.root)
            )).all()
            
            return {
                'total': total_files,
                'by_type': [{'type': str(item[0]), 'count': item[1]} for item in file_type_stats],
                'by_root': [{'root': str(item[0]), 'count': item[1]} for item in file_root_stats]
            }
        except Exception as e:
            return {'total': 0, 'by_type': [], 'by_root': []}
    
    @staticmethod
    async def get_container_statistics(db: AsyncSession) -> dict:
        try:
            total_containers = (await db.execute(select(func.count(Container.id)))).scalar()
            
            # Container模型没有status字段，所以我们按type分组
            container_type_stats = (await db.execute(
                select(
                    Container.type, 
                    func.count(Container.id).label('count')
                ).group_by(Container.type)
            )).all()
            
            # 模拟status统计，因为Container模型没有status字段
            # 这里我们假设所有容器都是running状态
            container_status_stats = [{'status': 'running', 'count': total_containers}]
            
            return {
                'total': total_containers,
                # 返回by_status和by_type给前端匹配
                'by_status': container_status_stats,
                'by_type': [{'type': str(item[0]), 'count': item[1]} for item in container_type_stats]
            }
        except Exception as e:
            # 如果报错说明可能没有相关字段，做个容错
            print(f"Container Stats Error: {e}")
            return {'total': 0, 'by_status': [], 'by_type': []}
    
    @staticmethod
    async def get_node_statistics(db: AsyncSession) -> dict:
        try:
            total_nodes = (await db.execute(select(func.count(NodeInfo.id)))).scalar()
            
            # 统计状态
            node_status_stats = (await db.execute(
                select(
                    NodeInfo.status,
                    func.count(NodeInfo.id).label('count')
                ).group_by(NodeInfo.status)
            )).all()
            
            # NodeInfo模型没有type字段，所以我们使用status作为type
            # 前端 expects: master, worker, storage. 
            # 如果DB里没有这些值，前端就会显示 0。
            
            return {
                'total': total_nodes,
                'by_status': [{'status': str(item[0]), 'count': item[1]} for item in node_status_stats],
                # 暂时将 status 作为 type 返回，或者您需要在代码里做映射
                'by_type': [{'type': str(item[0]), 'count': item[1]} for item in node_status_stats]
            }
        except Exception as e:
            return {'total': 0, 'by_status': [], 'by_type': []}

    @staticmethod
    async def get_all_statistics(db: AsyncSession) -> dict:
        return {
            'tasks': await StatisticsDao.get_task_statistics(db),
            'files': await StatisticsDao.get_file_statistics(db),
            'containers': await StatisticsDao.get_container_statistics(db),
            'nodes': await StatisticsDao.get_node_statistics(db)
        }
