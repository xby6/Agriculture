from fastapi import APIRouter, Depends, Form, Request, UploadFile
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_algo.file.service.file_service import FileService
from module_algo.file.entity.vo.file_vo import DeleteFileModel, FileModel, FilePageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
import datetime


fileController = APIRouter(prefix='/file/file', dependencies=[Depends(LoginService.get_current_user)])


@fileController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('file:file:list'))]
)
async def get_file_file_list(
    request: Request,
    file_page_query: FilePageQueryModel = Depends(FilePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    file_page_query.dept = current_user.user.dept.dept_id
    # 获取分页数据
    file_page_query_result = await FileService.get_file_list_services(query_db, file_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=file_page_query_result)


@fileController.post('', dependencies=[Depends(CheckUserInterfaceAuth('file:file:add'))])
@ValidateFields(validate_model='add_file')
@Log(title='文件', business_type=BusinessType.INSERT)
async def add_file_file(
    request: Request,
    file: UploadFile = Form(),
    add_file: FileModel = Depends(FileModel.as_form),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    add_file.dept = current_user.user.dept.dept_id
    
    add_file_result = await FileService.add_file_services(query_db, add_file, file)
    logger.info(add_file_result.message)

    return ResponseUtil.success(msg=add_file_result.message, data={'file_id': add_file_result.result})


@fileController.put('', dependencies=[Depends(CheckUserInterfaceAuth('file:file:edit'))])
@ValidateFields(validate_model='edit_file')
@Log(title='文件', business_type=BusinessType.UPDATE)
async def edit_file_file(
    request: Request,
    edit_file: FileModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_file_result = await FileService.edit_file_services(query_db, edit_file)
    logger.info(edit_file_result.message)

    return ResponseUtil.success(msg=edit_file_result.message)


@fileController.delete('/{ids}', dependencies=[Depends(CheckUserInterfaceAuth('file:file:remove'))])
@Log(title='文件', business_type=BusinessType.DELETE)
async def delete_file_file(request: Request, ids: str, query_db: AsyncSession = Depends(get_db)):
    delete_file = DeleteFileModel(ids=ids)
    delete_file_result = await FileService.delete_file_services(query_db, delete_file)
    logger.info(delete_file_result.message)

    return ResponseUtil.success(msg=delete_file_result.message)


@fileController.get(
    '/{id}', response_model=FileModel, dependencies=[Depends(CheckUserInterfaceAuth('file:file:query'))]
)
async def query_detail_file_file(request: Request, id: int, query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    file_detail_result = await FileService.file_detail_services(query_db, id, current_user.user.dept.dept_id)
    if file_detail_result is None:
        return ResponseUtil.failure(msg='文件不存在或您没有权限查看')

    logger.info(f'获取id为{id}的文件成功')
    return file_detail_result

@fileController.post('/unzip', dependencies=[Depends(CheckUserInterfaceAuth('file:file:add'))])
@Log(title='文件', business_type=BusinessType.INSERT)
async def unzip_file_file(
    request: Request,
    id: int = Form(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    
    unzip_file_result = await FileService.unzip_file_services(query_db, id, current_user.user.dept.dept_id)
    logger.info(unzip_file_result.message)

    return ResponseUtil.success(msg=unzip_file_result.message)



@fileController.get(
    '/{id}/info', response_model=FileModel, dependencies=[Depends(CheckUserInterfaceAuth('file:file:query'))]
)
async def query_detail_file_file(request: Request, id: int, query_db: AsyncSession = Depends(get_db)):
    file_info_detail_result = await FileService.file_info_detail_services(query_db, id)
    logger.info(f'获取id为{id}的文件成功')

    return ResponseUtil.success(data=file_info_detail_result)
