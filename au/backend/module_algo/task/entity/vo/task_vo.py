from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query




class TaskModel(BaseModel):
    """
    任务表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(default=None, description='任务唯一标识')
    name: Optional[str] = Field(default=None, description='任务名称')
    container: Optional[int] = Field(default=None, description='执行容器ID')
    algo: Optional[str] = Field(default=None, description='算法名称')
    args: Optional[str] = Field(default=None, description='任务参数')
    remark: Optional[str] = Field(default=None, description='备注信息')
    state: Optional[str] = Field(default=None, description='任务状态')
    result: Optional[int] = Field(default=None, description='任务结果文件ID')
    init_time: Optional[datetime] = Field(default=None, description='任务初始化时间')
    end_time: Optional[datetime] = Field(default=None, description='任务结束时间')
    dept: Optional[int] = Field(default=None, description='所属部门ID')




class TaskQueryModel(TaskModel):
    """
    任务不分页查询模型
    """
    pass


@as_query
class TaskPageQueryModel(TaskQueryModel):
    """
    任务分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    name: Optional[str] = Field(default=None, description='任务名称')
    container: Optional[int] = Field(default=None, description='执行容器ID')
    algo: Optional[str] = Field(default=None, description='算法名称')
    state: Optional[str] = Field(default=None, description='任务状态')
    remark: Optional[str] = Field(default=None, description='备注信息')
    dept: Optional[int] = Field(default=None, description='所属部门ID')


class DeleteTaskModel(BaseModel):
    """
    删除任务模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的任务唯一标识')
