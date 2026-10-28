from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_algo.node.dao.node_dao import NodeDao
from module_algo.node.entity.vo.node_vo import DeleteNodeModel, NodeModel, NodePageQueryModel
from module_algo.file.entity.do.file_do import File
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from datetime import datetime


class NodeService:
    """
    节点模块服务层
    """

    @classmethod
    async def get_node_list_services(
        cls, query_db: AsyncSession, query_object: NodePageQueryModel, is_page: bool = False
    ):
        """
        获取节点列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 节点列表信息对象
        """
        node_list_result = await NodeDao.get_node_list(query_db, query_object, is_page)

        return node_list_result

    @classmethod
    async def check_id_unique_services(cls, query_db: AsyncSession, page_object: NodeModel):
        """
        检查ID是否唯一service

        :param query_db: orm对象
        :param page_object: 节点对象
        :return: 校验结果
        """
        # 如果节点ID为None，直接返回唯一，因为这是新增操作
        if page_object.id is None:
            return CommonConstant.UNIQUE
            
        id = -1 if page_object.id is None else page_object.id
        node = await NodeDao.get_node_detail_by_info(query_db, NodeModel(id=page_object.id))
        if node and node.id != id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE


    @classmethod
    async def add_node_services(cls, query_db: AsyncSession, page_object: NodeModel, dept_id: int):
        """
        新增节点信息service

        :param query_db: orm对象
        :param page_object: 新增节点对象
        :return: 新增节点校验结果
        """
        if not await cls.check_id_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增节点{page_object.id}失败，ID已存在')
        try:
            # 创建关联的文件夹
            dir_record = File(
                name=page_object.name,  # 使用节点名作为文件夹名
                root=0,  # 根目录
                type="dir",  # 文件夹类型
                upload_time=datetime.now(),
                dept=dept_id,  # 使用当前用户的部门ID
            )
            query_db.add(dir_record)
            await query_db.flush()  # 获取文件夹ID
            
            # 将文件夹ID赋值给节点的dir字段
            page_object.dir = dir_record.id
            
            # 新增节点
            await NodeDao.add_node_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_node_services(cls, query_db: AsyncSession, page_object: NodeModel):
        """
        编辑节点信息service

        :param query_db: orm对象
        :param page_object: 编辑节点对象
        :return: 编辑节点校验结果
        """
        edit_node = page_object.model_dump(exclude_unset=True, exclude={'create_time', 'status'})
        node_info = await cls.node_detail_services(query_db, page_object.id)
        # 检查节点是否存在，需要明确检查node_info是否为None
        if node_info is not None:
            if not await cls.check_id_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改节点{page_object.id}失败，ID已存在')
            try:
                await NodeDao.edit_node_dao(query_db, edit_node)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='节点不存在')

    @classmethod
    async def delete_node_services(cls, query_db: AsyncSession, page_object: DeleteNodeModel):
        """
        删除节点信息service

        :param query_db: orm对象
        :param page_object: 删除节点对象
        :return: 删除节点校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await NodeDao.delete_node_dao(query_db, NodeModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入ID为空')

    @classmethod
    async def node_detail_services(cls, query_db: AsyncSession, id: int):
        """
        获取节点详细信息service

        :param query_db: orm对象
        :param id: ID
        :return: ID对应的信息
        """
        node = await NodeDao.get_node_detail_by_id(query_db, id=id)
        if node:
            result = NodeModel(**CamelCaseUtil.transform_result(node))
        else:
            # 返回None而不是创建空对象，避免在序列化时出错
            result = None

        return result

    @staticmethod
    async def export_node_list_services(node_list: List):
        """
        导出节点信息service

        :param node_list: 节点信息列表
        :return: 节点信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'id': 'ID',
            'name': '节点名',
            'longitude': '经度',
            'latitude': '纬度',
            'createTime': '创建时间',
            'status': '状态',
            'dir': '关联文件夹ID',
        }
        binary_data = ExcelUtil.export_list2excel(node_list, mapping_dict)

        return binary_data
