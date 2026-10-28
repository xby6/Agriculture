from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_algo.container.entity.do.container_do import Container
from module_algo.container.entity.vo.container_vo import ContainerModel, ContainerPageQueryModel
from utils.page_util import PageUtil


class ContainerDao:
    """
    容器模块数据库操作层
    """

    @classmethod
    async def get_container_detail_by_id(cls, db: AsyncSession, id: int):
        """
        根据容器唯一标识获取容器详细信息

        :param db: orm对象
        :param id: 容器唯一标识
        :return: 容器信息对象
        """
        container_info = (
            (
                await db.execute(
                    select(Container)
                    .where(
                        Container.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return container_info


    @classmethod
    async def get_container_list(cls, db: AsyncSession, query_object: ContainerPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取容器列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 容器列表信息对象
        """
        query = (
            select(Container)
            .where(
                Container.name.like(f'%{query_object.name}%') if query_object.name else True,
                Container.type == query_object.type if query_object.type else True,
                Container.dept == query_object.dept if query_object.dept else True,
            )
            .order_by(Container.id)
            .distinct()
        )
        container_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return container_list

    @classmethod
    async def add_container_dao(cls, db: AsyncSession, container: ContainerModel):
        """
        新增容器数据库操作

        :param db: orm对象
        :param container: 容器对象
        :return:
        """
        db_container = Container(**container.model_dump(exclude={'id'}))
        db.add(db_container)
        await db.flush()

        return db_container

    @classmethod
    async def edit_container_dao(cls, db: AsyncSession, container: dict):
        """
        编辑容器数据库操作

        :param db: orm对象
        :param container: 需要更新的容器字典
        :return:
        """
        await db.execute(update(Container), [container])

    @classmethod
    async def delete_container_dao(cls, db: AsyncSession, container: ContainerModel):
        """
        删除容器数据库操作

        :param db: orm对象
        :param container: 容器对象
        :return:
        """
        await db.execute(delete(Container).where(Container.id.in_([container.id])))

