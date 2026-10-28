from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_algo.container.dao.container_dao import ContainerDao
from module_algo.container.entity.vo.container_vo import DeleteContainerModel, ContainerModel, ContainerPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from datetime import datetime


class ContainerService:
    """
    容器模块服务层
    """

    @classmethod
    async def get_container_list_services(
        cls, query_db: AsyncSession, query_object: ContainerPageQueryModel, is_page: bool = False, dept_id: int = None
    ):
        """
        获取容器列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :param dept_id: 部门ID
        :return: 容器列表信息对象
        """
        if dept_id:
            query_object.dept = dept_id
        container_list_result = await ContainerDao.get_container_list(query_db, query_object, is_page)

        return container_list_result


    @classmethod
    async def add_container_services(cls, query_db: AsyncSession, page_object: ContainerModel):
        """
        新增容器信息service

        :param query_db: orm对象
        :param page_object: 新增容器对象
        :return: 新增容器校验结果
        """
        try:
            page_object.create_time = datetime.now()
            await ContainerDao.add_container_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_container_services(cls, query_db: AsyncSession, page_object: ContainerModel):
        """
        编辑容器信息service

        :param query_db: orm对象
        :param page_object: 编辑容器对象
        :return: 编辑容器校验结果
        """
        edit_container = page_object.model_dump(exclude_unset=True, exclude={'create_time', 'dept'})
        container_info = await cls.container_detail_services(query_db, page_object.id)
        if container_info.id:
            try:
                await ContainerDao.edit_container_dao(query_db, edit_container)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='容器不存在')

    @classmethod
    async def delete_container_services(cls, query_db: AsyncSession, page_object: DeleteContainerModel):
        """
        删除容器信息service

        :param query_db: orm对象
        :param page_object: 删除容器对象
        :return: 删除容器校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await ContainerDao.delete_container_dao(query_db, ContainerModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入容器唯一标识为空')

    @classmethod
    async def container_detail_services(cls, query_db: AsyncSession, id: int):
        """
        获取容器详细信息service

        :param query_db: orm对象
        :param id: 容器唯一标识
        :return: 容器唯一标识对应的信息
        """
        container = await ContainerDao.get_container_detail_by_id(query_db, id=id)
        if container:
            result = ContainerModel(**CamelCaseUtil.transform_result(container))
        else:
            result = ContainerModel(**dict())

        return result


