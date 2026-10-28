from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.user_do import SysUserPost
from module_admin.entity.vo.post_vo import PostModel, PostPageQueryModel
from utils.page_util import PageUtil


class PostDao:
    """
    职责管理模块数据库操作层
    """

    @classmethod
    async def get_post_by_id(cls, db: AsyncSession, post_id: int):
        """
        根据职责id获取在用职责详细信息

        :param db: orm对象
        :param post_id: 职责id
        :return: 在用职责信息对象
        """
        post_info = (
            (await db.execute(select(SysPost).where(SysPost.post_id == post_id, SysPost.status == '0')))
            .scalars()
            .first()
        )

        return post_info

    @classmethod
    async def get_post_detail_by_id(cls, db: AsyncSession, post_id: int):
        """
        根据职责id获取职责详细信息

        :param db: orm对象
        :param post_id: 职责id
        :return: 职责信息对象
        """
        post_info = (await db.execute(select(SysPost).where(SysPost.post_id == post_id))).scalars().first()

        return post_info

    @classmethod
    async def get_post_detail_by_info(cls, db: AsyncSession, post: PostModel):
        """
        根据职责参数获取职责信息

        :param db: orm对象
        :param post: 职责参数对象
        :return: 职责信息对象
        """
        post_info = (
            (
                await db.execute(
                    select(SysPost).where(
                        SysPost.post_name == post.post_name if post.post_name else True,
                        SysPost.post_code == post.post_code if post.post_code else True,
                        SysPost.post_sort == post.post_sort if post.post_sort else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return post_info

    @classmethod
    async def get_post_list(cls, db: AsyncSession, query_object: PostPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取职责列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 职责列表信息对象
        """
        query = (
            select(SysPost)
            .where(
                SysPost.post_code.like(f'%{query_object.post_code}%') if query_object.post_code else True,
                SysPost.post_name.like(f'%{query_object.post_name}%') if query_object.post_name else True,
                SysPost.status == query_object.status if query_object.status else True,
            )
            .order_by(SysPost.post_sort)
            .distinct()
        )
        post_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return post_list

    @classmethod
    async def add_post_dao(cls, db: AsyncSession, post: PostModel):
        """
        新增职责数据库操作

        :param db: orm对象
        :param post: 职责对象
        :return:
        """
        db_post = SysPost(**post.model_dump())
        db.add(db_post)
        await db.flush()

        return db_post

    @classmethod
    async def edit_post_dao(cls, db: AsyncSession, post: dict):
        """
        编辑职责数据库操作

        :param db: orm对象
        :param post: 需要更新的职责字典
        :return:
        """
        await db.execute(update(SysPost), [post])

    @classmethod
    async def delete_post_dao(cls, db: AsyncSession, post: PostModel):
        """
        删除职责数据库操作

        :param db: orm对象
        :param post: 职责对象
        :return:
        """
        await db.execute(delete(SysPost).where(SysPost.post_id.in_([post.post_id])))

    @classmethod
    async def count_user_post_dao(cls, db: AsyncSession, post_id: int):
        """
        根据职责id查询职责关联的用户数量

        :param db: orm对象
        :param post_id: 职责id
        :return: 职责关联的用户数量
        """
        user_post_count = (
            await db.execute(select(func.count('*')).select_from(SysUserPost).where(SysUserPost.post_id == post_id))
        ).scalar()

        return user_post_count
