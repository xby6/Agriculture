from fastapi import APIRouter, Depends, Form, Request, UploadFile
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_algo.container.service.container_service import ContainerService
from module_algo.container.entity.vo.container_vo import DeleteContainerModel, ContainerModel, ContainerPageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
from datetime import datetime
import httpx


containerController = APIRouter(prefix='/container/container', dependencies=[Depends(LoginService.get_current_user)])


@containerController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('container:container:list'))]
)
async def get_container_container_list(
    request: Request,
container_page_query: ContainerPageQueryModel = Depends(ContainerPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    dept_id = current_user.user.dept_id
    # 获取分页数据
    container_page_query_result = await ContainerService.get_container_list_services(query_db, container_page_query, is_page=True, dept_id=dept_id)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=container_page_query_result)


@containerController.post('', dependencies=[Depends(CheckUserInterfaceAuth('container:container:add'))])
@ValidateFields(validate_model='add_container')
@Log(title='容器', business_type=BusinessType.INSERT)
async def add_container_container(
    request: Request,
    add_container: ContainerModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    dept_id = current_user.user.dept_id
    add_container.dept = dept_id
    add_container_result = await ContainerService.add_container_services(query_db, add_container)
    logger.info(add_container_result.message)

    return ResponseUtil.success(msg=add_container_result.message)


@containerController.put('', dependencies=[Depends(CheckUserInterfaceAuth('container:container:edit'))])
@ValidateFields(validate_model='edit_container')
@Log(title='容器', business_type=BusinessType.UPDATE)
async def edit_container_container(
    request: Request,
    edit_container: ContainerModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    edit_container_result = await ContainerService.edit_container_services(query_db, edit_container)
    logger.info(edit_container_result.message)

    return ResponseUtil.success(msg=edit_container_result.message)


@containerController.delete('/{ids}', dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))])
@Log(title='容器', business_type=BusinessType.DELETE)
async def delete_container_container(request: Request, ids: str, query_db: AsyncSession = Depends(get_db)):
    delete_container = DeleteContainerModel(ids=ids)
    delete_container_result = await ContainerService.delete_container_services(query_db, delete_container)
    logger.info(delete_container_result.message)

    return ResponseUtil.success(msg=delete_container_result.message)


@containerController.get(
    '/{id}', response_model=ContainerModel, dependencies=[Depends(CheckUserInterfaceAuth('container:container:query'))]
)
async def query_detail_container_container(request: Request, id: int, query_db: AsyncSession = Depends(get_db)):
    container_detail_result = await ContainerService.container_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=container_detail_result)


@containerController.post(
    "/algorithm/create",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def create_algorithm(
    file: UploadFile = Form(...),
    algo_name: str = Form(...),
    args: str = Form(...),
    args_intro: str = Form(...),
    intro: str = Form(...),
    container_id: int = Form(...),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user) # current_user is used for logging context
):
    """
    创建新算法并转发请求到指定的容器服务
    """
    dept_id = current_user.user.dept_id

    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")


    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{container.url}/create",
                files={"file": (file.filename, await file.read(), file.content_type)},
                data={
                    "algo_name": algo_name,
                    "args": args,
                    "args_intro": args_intro,
                    "intro": intro
                }
            )
            response.raise_for_status()  # 检查HTTP响应状态码

            logger.info(f'算法创建成功: {algo_name}')
            return ResponseUtil.success(msg="算法创建成功")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.warning(f'算法已存在: {algo_name}')
                return ResponseUtil.failure(msg="算法已存在")
            logger.error(f'服务器错误: {str(e)}')
            return ResponseUtil.failure(msg=f"服务器错误: {str(e)}")
        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.post(
    "/algorithm/delete",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def delete_algorithm(
    algo_name: str = Form(...),
    container_id: int = Form(...),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    删除指定算法并转发请求到指定的容器服务
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{container.url}/delete",
                data={"algo_name": algo_name}
            )
            response.raise_for_status()

            logger.info(f'算法删除成功: {algo_name}')
            return ResponseUtil.success(msg="算法删除成功")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f'算法不存在: {algo_name}')
                return ResponseUtil.failure(msg="算法不存在")
            logger.error(f'服务器错误: {str(e)}')
            return ResponseUtil.failure(msg=f"服务器错误: {str(e)}")
        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.get(
    "/running-tasks/{container_id}",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def get_running_tasks(
    container_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    获取指定容器中运行中的任务列表
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{container.url}/running-tasks")
            response.raise_for_status()

            running_tasks = response.json()

            logger.info(f'获取容器 {container_id} 运行中的任务成功')
            return ResponseUtil.success(data={"running_tasks": running_tasks})

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404: # 容器服务侧返回404可能意味着没有该资源
            logger.warning(f'容器服务中获取运行任务失败，可能是资源不存在: {container_id}')
            # 这里的失败原因，取决于容器服务对404的定义，可以更明确
            return ResponseUtil.failure(msg="容器服务内部错误或资源NotFound")
        logger.error(f'获取运行中的任务失败: {str(e)}')
        return ResponseUtil.failure(msg=f"获取运行中的任务失败: {str(e)}")
    except Exception as e:
        logger.error(f'请求失败: {str(e)}')
        return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.get(
    "/logs/{container_id}",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def get_logs(
    container_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    获取指定容器的日志
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{container.url}/logs")
            response.raise_for_status()

            logs = response.text

            logger.info(f'获取容器 {container_id} 日志成功')
            return ResponseUtil.success(data={"logs": logs})

    except Exception as e: # 假设服务器错误或其他httpx错误不会导致404，因此直接捕获Exception
        logger.error(f'获取日志失败: {str(e)}')
        return ResponseUtil.failure(msg=f"获取日志失败: {str(e)}")


@containerController.post(
    "/algorithm/update",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def update_algorithm(
    file: UploadFile = Form(...),
    algo_name: str = Form(...),
    args: str = Form(...),
    args_intro: str = Form(...),
    intro: str = Form(...),
    container_id: int = Form(...),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    更新指定算法并转发请求到指定的容器服务
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{container.url}/update",
                files={"file": (file.filename, await file.read(), file.content_type)},
                data={
                    "algo_name": algo_name,
                    "args": args,
                    "args_intro": args_intro,
                    "intro": intro
                }
            )
            response.raise_for_status()

            logger.info(f'算法更新成功: {algo_name}')
            return ResponseUtil.success(msg="算法更新成功")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f'算法不存在: {algo_name}')
                return ResponseUtil.failure(msg="算法不存在")
            logger.error(f'服务器错误: {str(e)}')
            return ResponseUtil.failure(msg=f"服务器错误: {str(e)}")
        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.get(
    "/algorithm/list",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def list_algorithms(
    container_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    列出指定容器中的所有算法
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{container.url}/list")
            response.raise_for_status()

            algorithms = response.json()

            logger.info(f'获取容器 {container_id} 算法列表成功')
            return ResponseUtil.success(data=algorithms)

        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


# 模型管理中转API
@containerController.post(
    "/model/create",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def create_model(
    file: UploadFile = Form(...),
    model_name: str = Form(...),
    intro: str = Form(...),
    container_id: int = Form(...),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    创建新模型并转发请求到指定的容器服务
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{container.url}/create_model",
                files={"file": (file.filename, await file.read(), file.content_type)},
                data={
                    "model_name": model_name,
                    "intro": intro
                }
            )
            response.raise_for_status()

            logger.info(f'模型创建成功: {model_name}')
            return ResponseUtil.success(msg="模型创建成功")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.warning(f'模型已存在: {model_name}')
                return ResponseUtil.failure(msg="模型已存在")
            logger.error(f'服务器错误: {str(e)}')
            return ResponseUtil.failure(msg=f"服务器错误: {str(e)}")
        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.post(
    "/model/delete",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def delete_model(
    model_name: str = Form(...),
    container_id: int = Form(...),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    删除指定模型并转发请求到指定的容器服务
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{container.url}/delete_model",
                data={"model_name": model_name}
            )
            response.raise_for_status()

            logger.info(f'模型删除成功: {model_name}')
            return ResponseUtil.success(msg="模型删除成功")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f'模型不存在: {model_name}')
                return ResponseUtil.failure(msg="模型不存在")
            logger.error(f'服务器错误: {str(e)}')
            return ResponseUtil.failure(msg=f"服务器错误: {str(e)}")
        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


@containerController.get(
    "/model/list",
    dependencies=[Depends(CheckUserInterfaceAuth('container:container:remove'))]
)
async def list_models(
    container_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    列出指定容器中的所有模型
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    container = await ContainerService.container_detail_services(query_db, container_id)
    if not container:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container_id}')
        return ResponseUtil.failure(msg="容器不存在")

    # 转发请求到容器服务
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{container.url}/model_list")
            response.raise_for_status()

            models = response.json()

            logger.info(f'获取容器 {container_id} 模型列表成功')
            return ResponseUtil.success(data=models)

        except Exception as e:
            logger.error(f'请求失败: {str(e)}')
            return ResponseUtil.failure(msg=f"请求失败: {str(e)}")


