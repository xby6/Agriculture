from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_algo.task.entity.do.task_do import Task
from module_algo.task.entity.vo.task_vo import TaskModel, TaskPageQueryModel
from utils.page_util import PageUtil


class TaskDao:
    """
    任务模块数据库操作层
    """

    @classmethod
    async def get_task_detail_by_id(cls, db: AsyncSession, id: int):
        """
        根据任务唯一标识获取任务详细信息

        :param db: orm对象
        :param id: 任务唯一标识
        :return: 任务信息对象
        """
        task_info = (
            (
                await db.execute(
                    select(Task)
                    .where(
                        Task.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return task_info


    @classmethod
    async def get_task_list(cls, db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取任务列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 任务列表信息对象
        """
        query = (
            select(Task)
            .where(
                Task.name.like(f'%{query_object.name}%') if query_object.name else True,
                Task.container == query_object.container if query_object.container else True,
                Task.algo == query_object.algo if query_object.algo else True,
                Task.remark.like(f'%{query_object.remark}%') if query_object.remark else True,
                Task.state == query_object.state if query_object.state else True,
            )
            .order_by(Task.id)
            .distinct()
        )
        task_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return task_list

    @classmethod
    async def add_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        新增任务数据库操作

        :param db: orm对象
        :param task: 任务对象
        :return:
        """
        task_data = task.model_dump(exclude={'id', 'state', 'end_time'})
        if task_data.get('result') is None:
            task_data['result'] = 0
        db_task = Task(**task_data)
        db.add(db_task)
        await db.flush()

        return db_task

    @classmethod
    async def edit_task_dao(cls, db: AsyncSession, task: dict):
        """
        编辑任务数据库操作

        :param db: orm对象
        :param task: 需要更新的任务字典
        :return:
        """
        await db.execute(update(Task), [task])

    @classmethod
    async def delete_task_dao(cls, db: AsyncSession, task: TaskModel):
        """
        删除任务数据库操作

        :param db: orm对象
        :param task: 任务对象
        :return:
        """
        await db.execute(delete(Task).where(Task.id.in_([task.id])).where(Task.dept == task.dept))
