from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_algo.node.service.node_service import NodeService
from module_algo.node.entity.vo.node_vo import DeleteNodeModel, NodeModel, NodePageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil


nodeController = APIRouter(prefix='/node/node', dependencies=[Depends(LoginService.get_current_user)])


@nodeController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('node:node:list'))]
)
async def get_node_node_list(
    request: Request,
node_page_query: NodePageQueryModel = Depends(NodePageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
):
    # 获取分页数据
    node_page_query_result = await NodeService.get_node_list_services(query_db, node_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=node_page_query_result)


@nodeController.post('', dependencies=[Depends(CheckUserInterfaceAuth('node:node:add'))])
@ValidateFields(validate_model='add_node')
@Log(title='节点', business_type=BusinessType.INSERT)
async def add_node_node(
    request: Request,
    add_node: NodeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    add_node.create_time = datetime.now()
    dept_id = current_user.user.dept.dept_id
    add_node_result = await NodeService.add_node_services(query_db, add_node, dept_id)
    logger.info(add_node_result.message)

    return ResponseUtil.success(msg=add_node_result.message)


@nodeController.put('', dependencies=[Depends(CheckUserInterfaceAuth('node:node:edit'))])
@ValidateFields(validate_model='edit_node')
@Log(title='节点', business_type=BusinessType.UPDATE)
async def edit_node_node(
    request: Request,
    edit_node: NodeModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_node_result = await NodeService.edit_node_services(query_db, edit_node)
    logger.info(edit_node_result.message)

    return ResponseUtil.success(msg=edit_node_result.message)


@nodeController.delete('/{ids}', dependencies=[Depends(CheckUserInterfaceAuth('node:node:remove'))])
@Log(title='节点', business_type=BusinessType.DELETE)
async def delete_node_node(request: Request, ids: str, query_db: AsyncSession = Depends(get_db)):
    delete_node = DeleteNodeModel(ids=ids)
    delete_node_result = await NodeService.delete_node_services(query_db, delete_node)
    logger.info(delete_node_result.message)

    return ResponseUtil.success(msg=delete_node_result.message)


@nodeController.get(
    '/{id}', response_model=NodeModel, dependencies=[Depends(CheckUserInterfaceAuth('node:node:query'))]
)
async def query_detail_node_node(request: Request, id: int, query_db: AsyncSession = Depends(get_db)):
    node_detail_result = await NodeService.node_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=node_detail_result)


@nodeController.post('/export', dependencies=[Depends(CheckUserInterfaceAuth('node:node:export'))])
@Log(title='节点', business_type=BusinessType.EXPORT)
async def export_node_node_list(
    request: Request,
    node_page_query: NodePageQueryModel = Form(),
    query_db: AsyncSession = Depends(get_db),
):
    # 获取全量数据
    node_query_result = await NodeService.get_node_list_services(query_db, node_page_query, is_page=False)
    node_export_result = await NodeService.export_node_list_services(node_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(node_export_result))
