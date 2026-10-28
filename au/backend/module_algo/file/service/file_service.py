from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_algo.file.dao.file_dao import FileDao
from module_algo.file.entity.vo.file_vo import DeleteFileModel, FileModel, FilePageQueryModel
from module_algo.file.entity.do.file_do import File

from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from fastapi import UploadFile

import uuid
from pathlib import Path
import os
from datetime import datetime

class FileService:
    """
    文件模块服务层
    """

    @classmethod
    async def get_file_list_services(
        cls, query_db: AsyncSession, query_object: FilePageQueryModel, is_page: bool = False):
        """
        获取文件列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 文件列表信息对象
        """
        await cls._repair_physical_directory_records(query_db, query_object.root, query_object.dept)
        file_list_result = await FileDao.get_file_list(query_db, query_object, is_page)

        return file_list_result


    @classmethod
    async def add_file_services(cls, query_db: AsyncSession, page_object: FileModel, file: UploadFile):
        """
        新增文件信息service

        :param query_db: orm对象
        :param page_object: 新增文件对象
        :return: 新增文件校验结果
        """
        try:

            upload_dir = Path(f"upload_file")
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = None
            file_size = None

            if page_object.type != "dir":

                # 生成随机文件名
                random_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"

                # 保存文件到指定目录
                file_path = upload_dir / random_filename
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                file_size = file.size
            page_object.name = file.filename if page_object.name is None else page_object.name
            page_object.path = str(file_path)
            page_object.size = file_size
            page_object.upload_time = datetime.now()
            page_object.type = os.path.splitext(file.filename)[1] if page_object.type is None else page_object.type
            
            saved_file = await FileDao.add_file_dao(query_db, page_object)
            saved_file_id = saved_file.id
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功', result=saved_file_id)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_file_services(cls, query_db: AsyncSession, page_object: FileModel):
        """
        编辑文件信息service

        :param query_db: orm对象
        :param page_object: 编辑文件对象
        :return: 编辑文件校验结果
        """
        edit_file = page_object.model_dump(exclude_unset=True, exclude={'size', 'upload_time', 'dept', 'path'})
        file_info = await FileDao.get_file_detail_by_id(query_db, id=page_object.id)
        if file_info.id:
            try:
                await FileDao.edit_file_dao(query_db, edit_file)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='文件不存在')

    @classmethod
    async def delete_file_services(cls, query_db: AsyncSession, page_object: DeleteFileModel):
        """
        删除文件信息service

        :param query_db: orm对象
        :param page_object: 删除文件对象
        :return: 删除文件校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    id = int(id)
                    file_info = await FileDao.get_file_detail_by_id(query_db, id=id)
                    if file_info.type == "dir":
                        file_list = await FileDao.get_file_detail_by_root(query_db, id)
                        if file_list:
                            raise ServiceException(message='文件夹下存在文件，不能删除')
                    else:
                        file_path = Path(file_info.path)
                        if file_path.exists():
                            os.remove(file_path)
                        else:
                            raise ServiceException(message='文件不存在')
                    await FileDao.delete_file_dao(query_db, FileModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入文件唯一标识为空')

    @classmethod
    async def file_detail_services(cls, query_db: AsyncSession, id: int, dept_id: int):
        """
        获取文件详细信息service

        :param query_db: orm对象
        :param id: 文件唯一标识
        :return: 文件唯一标识对应的信息
        """
        result = None
        file = await FileDao.get_file_detail_by_id(query_db, id=id)
        if not file:
            return None
        if file.dept != dept_id:
            return None
        if file:
            if file.type == "dir" or (file.path and Path(file.path).exists() and Path(file.path).is_dir()):
                await cls._repair_physical_directory_records(query_db, file.id, dept_id)
                import zipfile
                import io
                import os
                zip_buffer = io.BytesIO()
                stack = [(file.id, "")]
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    while stack:
                        current_id, current_rel_path = stack.pop()
                        current_file = await FileDao.get_file_detail_by_id(query_db,current_id)

                        if current_file.type == "dir" or (current_file.path and Path(current_file.path).exists() and Path(current_file.path).is_dir()):
                            # 获取该目录下的所有文件和子目录
                            children = await FileDao.get_file_detail_by_root(query_db,current_id) # 修改为使用 id

                            for child in children:
                                # 构建子项的相对路径
                                child_rel_path = os.path.join(current_rel_path, child.name)

                                if child.type == "dir" or (child.path and Path(child.path).exists() and Path(child.path).is_dir()):
                                    # 如果是目录，压入栈中继续处理
                                    stack.append((child.id, child_rel_path))
                                else:
                                    # 如果是文件，添加到zip中
                                    try:
                                        file_path = Path(child.path)
                                        if file_path.exists():
                                            # 在zip中创建目录结构
                                            arcname = child_rel_path.replace(os.sep, '/')
                                            zip_file.write(file_path, arcname)
                                    except Exception as e:
                                        print(f"压缩文件时错误: {str(e)}")
                                        continue
                        else:
                            # 处理文件（理论上不应该进入这里，因为栈中只压入目录）
                            try:
                                file_path = Path(current_file.path)
                                if file_path.exists():
                                    arcname = current_rel_path.replace(os.sep, '/')
                                    zip_file.write(file_path, arcname)
                            except Exception as e:
                                continue
                zip_buffer.seek(0)
                dirname = file.name.encode("utf8")
                filename = f"{dirname}.zip"
                from fastapi.responses import StreamingResponse
                return StreamingResponse(
                    content=zip_buffer,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "Content-Length": str(zip_buffer.getbuffer().nbytes)
                    }
                )
            else:
                from fastapi.responses import FileResponse
                path = Path(file.path)
                if not path.exists():
                    raise ServiceException(message=f'文件路径{path}不存在')
                result = FileResponse(path=path, filename=file.name)
        else:
            result = None

        return result

    @classmethod
    async def _repair_physical_directory_records(cls, query_db: AsyncSession, root_id: int | None, dept_id: int | None):
        if not root_id:
            return

        changed = False

        def detect_file_type(path: Path) -> str:
            if path.is_dir():
                return "dir"
            suffix = path.suffix.lower()
            return suffix[1:] if suffix else "unknown"

        async def sync_directory(record: File):
            nonlocal changed
            record_path = Path(record.path) if record.path else None
            if not record_path or not record_path.exists() or not record_path.is_dir():
                return

            if record.type != "dir" or record.size:
                record.type = "dir"
                record.size = None
                changed = True

            existing_children = await FileDao.get_file_detail_by_root(query_db, record.id)
            existing_by_name = {child.name: child for child in existing_children}
            for child_path in sorted(record_path.iterdir(), key=lambda item: item.name.lower()):
                child_record = existing_by_name.get(child_path.name)
                child_type = detect_file_type(child_path)
                if child_record is None:
                    child_record = File(
                        name=child_path.name,
                        path=str(child_path),
                        root=record.id,
                        type=child_type,
                        upload_time=datetime.now(),
                        dept=dept_id or record.dept,
                        size=None if child_path.is_dir() else child_path.stat().st_size,
                    )
                    query_db.add(child_record)
                    await query_db.flush()
                    changed = True
                else:
                    if child_record.type != child_type:
                        child_record.type = child_type
                        changed = True
                    expected_size = None if child_path.is_dir() else child_path.stat().st_size
                    if child_record.size != expected_size:
                        child_record.size = expected_size
                        changed = True
                    if not child_record.path:
                        child_record.path = str(child_path)
                        changed = True

                if child_path.is_dir():
                    await sync_directory(child_record)

        rows = await FileDao.get_file_detail_by_root(query_db, root_id)
        for row in rows:
            await sync_directory(row)

        if changed:
            await query_db.commit()

    @classmethod
    async def file_info_detail_services(cls, query_db: AsyncSession, id: int):
        """
        获取文件详细信息service

        :param query_db: orm对象
        :param id: 文件唯一标识
        :return: 文件唯一标识对应的信息
        """
        file = await FileDao.get_file_detail_by_id(query_db, id=id)
        if file:
            result = FileModel(**CamelCaseUtil.transform_result(file))
        else:
            result = FileModel(**dict())

        return result

    @classmethod
    async def unzip_file_services(cls, query_db: AsyncSession, id: int, dept_id: int):
        """
        解压文件service

        :param query_db: orm对象
        :param id: 文件唯一标识
        :return: 解压文件校验结果
        """
        try:
            file = await FileDao.get_file_detail_by_id(query_db, id)
            if file is None:
                raise ServiceException(message='文件不存在')
            if file.type != '.zip':
                raise ServiceException(message='只能解压zip文件')
            if file.dept != dept_id:
                raise ServiceException(message='您没有权限解压该文件')
            name = file.name.replace(".zip", "")
            zip_path = Path(file.path)
            result_dir = zip_path.parent / uuid.uuid4().hex
            result_dir.mkdir(parents=True, exist_ok=True)
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(result_dir)

                dir_path = result_dir

                # 创建目录记录
                dir_record = File(
                    name=name,
                    root=file.root,
                    type="dir",
                    upload_time=datetime.now(),
                    dept = dept_id,
                )
                query_db.add(dir_record)
                await query_db.commit()
                await query_db.refresh(dir_record)

                def get_file_type(filepath: Path) -> str:
                    if filepath.is_dir():
                        return "dir"
                    suffix = filepath.suffix
                    if suffix:
                        return "." + suffix[1:].lower()
                    if os.access(filepath, os.X_OK):
                        return "executable"
                    return "unknown"



                # 递归处理解压的文件和目录
                async def process_directory(current_dir: Path, parent_id: int):
                    """递归处理目录结构"""
                    for item in current_dir.iterdir():
                            
                        item_type = get_file_type(item)
                        
                        # 创建文件/目录记录
                        item_record = File(
                            name=item.name,
                            path=str(item) if item_type != "dir" else None,
                            root=parent_id,  # 使用父级ID作为root
                            type=item_type,
                            upload_time=datetime.now(),
                            dept=dept_id,
                            size=item.stat().st_size if item.is_file() else None
                        )
                        query_db.add(item_record)
                        await query_db.commit()
                        await query_db.refresh(item_record)
                        
                        # 如果是目录，递归处理
                        if item_record.type == "dir":
                            await process_directory(item, item_record.id)
                
                # 开始处理解压的目录
                await process_directory(result_dir, dir_record.id)

            return CrudResponseModel(is_success=True, message='解压成功')

        except Exception as e:
            await query_db.rollback()
            raise e
