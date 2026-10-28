from sqlalchemy import bindparam, func, or_, select, update  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import immutabledict
from typing import List
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.role_do import SysRoleDept  # noqa: F401
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.dept_vo import DeptModel


class DeptDao:
    """
    小组管理模块数据库操作层
    """

    @classmethod
    async def get_dept_by_id(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id获取在用小组信息

        :param db: orm对象
        :param dept_id: 小组id
        :return: 在用小组信息对象
        """
        dept_info = (await db.execute(select(SysDept).where(SysDept.dept_id == dept_id))).scalars().first()

        return dept_info

    @classmethod
    async def get_dept_detail_by_id(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id获取小组详细信息

        :param db: orm对象
        :param dept_id: 小组id
        :return: 小组信息对象
        """
        dept_info = (
            (await db.execute(select(SysDept).where(SysDept.dept_id == dept_id, SysDept.del_flag == '0')))
            .scalars()
            .first()
        )

        return dept_info

    @classmethod
    async def get_dept_detail_by_info(cls, db: AsyncSession, dept: DeptModel):
        """
        根据小组参数获取小组信息

        :param db: orm对象
        :param dept: 小组参数对象
        :return: 小组信息对象
        """
        dept_info = (
            (
                await db.execute(
                    select(SysDept).where(
                        SysDept.parent_id == dept.parent_id if dept.parent_id else True,
                        SysDept.dept_name == dept.dept_name if dept.dept_name else True,
                    )
                )
            )
            .scalars()
            .first()
        )

        return dept_info

    @classmethod
    async def get_dept_info_for_edit_option(cls, db: AsyncSession, dept_info: DeptModel, data_scope_sql: str):
        """
        获取小组编辑对应的在用小组列表信息

        :param db: orm对象
        :param dept_info: 小组对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 小组列表信息
        """
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.dept_id != dept_info.dept_id,
                        ~SysDept.dept_id.in_(
                            select(SysDept.dept_id).where(func.find_in_set(dept_info.dept_id, SysDept.ancestors))
                        ),
                        SysDept.del_flag == '0',
                        SysDept.status == '0',
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def get_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id查询当前小组的子小组列表信息

        :param db: orm对象
        :param dept_id: 小组id
        :return: 子小组信息列表
        """
        dept_result = (
            (await db.execute(select(SysDept).where(func.find_in_set(dept_id, SysDept.ancestors)))).scalars().all()
        )

        return dept_result

    @classmethod
    async def get_dept_list_for_tree(cls, db: AsyncSession, dept_info: DeptModel, data_scope_sql: str):
        """
        获取所有在用小组列表信息

        :param db: orm对象
        :param dept_info: 小组对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 在用小组列表信息
        """
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.status == '0',
                        SysDept.del_flag == '0',
                        SysDept.dept_name.like(f'%{dept_info.dept_name}%') if dept_info.dept_name else True,
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def get_dept_list(cls, db: AsyncSession, page_object: DeptModel, data_scope_sql: str):
        """
        根据查询参数获取小组列表信息

        :param db: orm对象
        :param page_object: 不分页查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :return: 小组列表信息对象
        """
        dept_result = (
            (
                await db.execute(
                    select(SysDept)
                    .where(
                        SysDept.del_flag == '0',
                        SysDept.dept_id == page_object.dept_id if page_object.dept_id is not None else True,
                        SysDept.status == page_object.status if page_object.status else True,
                        SysDept.dept_name.like(f'%{page_object.dept_name}%') if page_object.dept_name else True,
                        eval(data_scope_sql),
                    )
                    .order_by(SysDept.order_num)
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        return dept_result

    @classmethod
    async def add_dept_dao(cls, db: AsyncSession, dept: DeptModel):
        """
        新增小组数据库操作

        :param db: orm对象
        :param dept: 小组对象
        :return: 新增校验结果
        """
        db_dept = SysDept(**dept.model_dump())
        db.add(db_dept)
        await db.flush()

        return db_dept

    @classmethod
    async def edit_dept_dao(cls, db: AsyncSession, dept: dict):
        """
        编辑小组数据库操作

        :param db: orm对象
        :param dept: 需要更新的小组字典
        :return: 编辑校验结果
        """
        await db.execute(update(SysDept), [dept])

    @classmethod
    async def update_dept_children_dao(cls, db: AsyncSession, update_dept: List):
        """
        更新子小组信息

        :param db: orm对象
        :param update_dept: 需要更新的小组列表
        :return:
        """
        await db.execute(
            update(SysDept)
            .where(SysDept.dept_id == bindparam('dept_id'))
            .values(
                {
                    'dept_id': bindparam('dept_id'),
                    'ancestors': bindparam('ancestors'),
                }
            ),
            update_dept,
            execution_options=immutabledict({'synchronize_session': None}),
        )

    @classmethod
    async def update_dept_status_normal_dao(cls, db: AsyncSession, dept_id_list: List):
        """
        批量更新小组状态为正常

        :param db: orm对象
        :param dept_id_list: 小组id列表
        :return:
        """
        await db.execute(update(SysDept).where(SysDept.dept_id.in_(dept_id_list)).values(status='0'))

    @classmethod
    async def delete_dept_dao(cls, db: AsyncSession, dept: DeptModel):
        """
        删除小组数据库操作

        :param db: orm对象
        :param dept: 小组对象
        :return:
        """
        await db.execute(
            update(SysDept)
            .where(SysDept.dept_id == dept.dept_id)
            .values(del_flag='2', update_by=dept.update_by, update_time=dept.update_time)
        )

    @classmethod
    async def count_normal_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id查询查询所有子小组（正常状态）的数量

        :param db: orm对象
        :param dept_id: 小组id
        :return: 所有子小组（正常状态）的数量
        """
        normal_children_dept_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(SysDept)
                .where(SysDept.status == '0', SysDept.del_flag == '0', func.find_in_set(dept_id, SysDept.ancestors))
            )
        ).scalar()

        return normal_children_dept_count

    @classmethod
    async def count_children_dept_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id查询查询所有子小组（所有状态）的数量

        :param db: orm对象
        :param dept_id: 小组id
        :return: 所有子小组（所有状态）的数量
        """
        children_dept_count = (
            await db.execute(
                select(func.count('*'))
                .select_from(SysDept)
                .where(SysDept.del_flag == '0', SysDept.parent_id == dept_id)
                .limit(1)
            )
        ).scalar()

        return children_dept_count

    @classmethod
    async def count_dept_user_dao(cls, db: AsyncSession, dept_id: int):
        """
        根据小组id查询查询小组下的用户数量

        :param db: orm对象
        :param dept_id: 小组id
        :return: 小组下的用户数量
        """
        dept_user_count = (
            await db.execute(
                select(func.count('*')).select_from(SysUser).where(SysUser.dept_id == dept_id, SysUser.del_flag == '0')
            )
        ).scalar()

        return dept_user_count
