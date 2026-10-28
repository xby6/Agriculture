from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_algo.task.dao.task_dao import TaskDao
from module_algo.task.entity.vo.task_vo import DeleteTaskModel, TaskModel, TaskPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from datetime import datetime


class TaskService:
    """
    任务模块服务层
    """

    @classmethod
    async def get_task_list_services(
        cls, query_db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False, dept_id: int = None
    ):
        """
        获取任务列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 任务列表信息对象
        """
        if dept_id:
            query_object.dept = dept_id
        task_list_result = await TaskDao.get_task_list(query_db, query_object, is_page)

        return task_list_result


    @classmethod
    async def add_task_services(cls, query_db: AsyncSession, page_object: TaskModel):
        """
        新增任务信息service

        :param query_db: orm对象
        :param page_object: 新增任务对象
        :return: 新增任务校验结果
        """
        try:
            page_object.init_time = datetime.now()
            saved_task = await TaskDao.add_task_dao(query_db, page_object)
            saved_task_id = saved_task.id
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功', result=saved_task_id)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_task_services(cls, query_db: AsyncSession, page_object: TaskModel):
        """
        编辑任务信息service

        :param query_db: orm对象
        :param page_object: 编辑任务对象
        :return: 编辑任务校验结果
        """
        edit_task = page_object.model_dump(exclude_unset=True, exclude={'state', 'init_time', 'end_time', 'dept', 'container', 'algo', 'result'})
        task_info = await cls.task_detail_services(query_db, page_object.id)
        if task_info.id and task_info.dept == page_object.dept:
            try:
                await TaskDao.edit_task_dao(query_db, edit_task)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='任务不存在')

    @classmethod
    async def delete_task_services(cls, query_db: AsyncSession, page_object: DeleteTaskModel, dept_id: int):
        """
        删除任务信息service

        :param query_db: orm对象
        :param page_object: 删除任务对象
        :return: 删除任务校验结果
        """
        
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await TaskDao.delete_task_dao(query_db, TaskModel(id=int(id), dept=dept_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入任务唯一标识为空')

    @classmethod
    async def task_detail_services(cls, query_db: AsyncSession, id: int):
        """
        获取任务详细信息service

        :param query_db: orm对象
        :param id: 任务唯一标识
        :return: 任务唯一标识对应的信息
        """
        task = await TaskDao.get_task_detail_by_id(query_db, id=id)
        if task:
            result = TaskModel(**CamelCaseUtil.transform_result(task))
        else:
            result = TaskModel(**dict())

        return result
