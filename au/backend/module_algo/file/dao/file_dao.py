from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from module_algo.file.entity.do.file_do import File
from module_algo.file.entity.vo.file_vo import FileModel, FilePageQueryModel
from utils.page_util import PageUtil


class FileDao:
    """
    文件模块数据库操作层
    """

    @classmethod
    async def get_file_detail_by_id(cls, db: AsyncSession, id: int):
        """
        根据文件唯一标识获取文件详细信息

        :param db: orm对象
        :param id: 文件唯一标识
        :return: 文件信息对象
        """
        file_info = (
            (
                await db.execute(
                    select(File)
                    .where(
                        File.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return file_info

    @classmethod
    async def get_file_detail_by_root(cls, db: AsyncSession, root: int):
        """
        根据文件root获取文件详细信息

        :param db: orm对象
        :param root: 文件root
        :return: 文件信息对象
        """
        file_info = (
            (
                await db.execute(
                    select(File)
                    .where(
                        File.root == root
                    )
                )
            )
            .scalars()
            .all()
        )

        return file_info

    @classmethod
    async def get_file_list(cls, db: AsyncSession, query_object: FilePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取文件列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 文件列表信息对象
        """
        query = (
            select(File)
            .where(
                File.name.like(f'%{query_object.name}%') if query_object.name else True,
                File.type == query_object.type if query_object.type else True,
                File.root == query_object.root if query_object.root else True,
                File.dept == query_object.dept if query_object.dept else True,
            )
            .order_by(File.id)
            .distinct()
        )
        file_list = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

        return file_list

    @classmethod
    async def add_file_dao(cls, db: AsyncSession, file: FileModel):
        """
        新增文件数据库操作

        :param db: orm对象
        :param file: 文件对象
        :return:
        """
        db_file = File(**file.model_dump())
        db.add(db_file)
        await db.flush()

        return db_file

    @classmethod
    async def edit_file_dao(cls, db: AsyncSession, file: dict):
        """
        编辑文件数据库操作

        :param db: orm对象
        :param file: 需要更新的文件字典
        :return:
        """
        await db.execute(update(File), [file])

    @classmethod
    async def delete_file_dao(cls, db: AsyncSession, file: FileModel):
        """
        删除文件数据库操作

        :param db: orm对象
        :param file: 文件对象
        :return:
        """
        await db.execute(delete(File).where(File.id.in_([file.id])))

