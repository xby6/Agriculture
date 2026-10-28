from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_algo.node.entity.do.node_do import NodeInfo
from module_algo.node.entity.vo.node_vo import NodeModel, NodePageQueryModel
from utils.page_util import PageUtil


class NodeDao:
    """
    节点模块数据库操作层
    """

    @classmethod
    async def get_node_detail_by_id(cls, db: AsyncSession, id: int):
        """
        根据ID获取节点详细信息

        :param db: orm对象
        :param id: ID
        :return: 节点信息对象
        """
        node_info = (
            (
                await db.execute(
                    select(NodeInfo)
                    .where(
                        NodeInfo.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return node_info

    @classmethod
    async def get_node_detail_by_info(cls, db: AsyncSession, node: NodeModel):
        """
        根据节点参数获取节点信息

        :param db: orm对象
        :param node: 节点参数对象
        :return: 节点信息对象
        """
        # 如果节点ID为None，直接返回None，避免查询ID为NULL的记录
        if node.id is None:
            return None
            
        node_info = (
            (
                await db.execute(
                    select(NodeInfo).where(
                        NodeInfo.id == node.id,
                    )
                )
            )
            .scalars()
            .first()
        )

        return node_info

    @classmethod
    async def get_node_list(cls, db: AsyncSession, query_object: NodePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取节点列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 节点列表信息对象
        """
        query = (
            select(NodeInfo)
            .where(
                NodeInfo.name.like(f'%{query_object.name}%') if query_object.name else True,
                NodeInfo.status == query_object.status if query_object.status else True,
            )
            .order_by(NodeInfo.id)
            .distinct()
        )
        node_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return node_list

    @classmethod
    async def add_node_dao(cls, db: AsyncSession, node: NodeModel):
        """
        新增节点数据库操作

        :param db: orm对象
        :param node: 节点对象
        :return:
        """
        db_node = NodeInfo(**node.model_dump())
        if db_node.status is None:
            db_node.status = '健康'
        db.add(db_node)
        await db.flush()

        return db_node

    @classmethod
    async def edit_node_dao(cls, db: AsyncSession, node: dict):
        """
        编辑节点数据库操作

        :param db: orm对象
        :param node: 需要更新的节点字典
        :return:
        """
        await db.execute(update(NodeInfo), [node])

    @classmethod
    async def delete_node_dao(cls, db: AsyncSession, node: NodeModel):
        """
        删除节点数据库操作

        :param db: orm对象
        :param node: 节点对象
        :return:
        """
        await db.execute(delete(NodeInfo).where(NodeInfo.id.in_([node.id])))

