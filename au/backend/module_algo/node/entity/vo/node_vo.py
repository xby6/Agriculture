from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query




class NodeModel(BaseModel):
    """
    节点表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(default=None, description='ID')
    name: Optional[str] = Field(default=None, description='节点名')
    longitude: Optional[float] = Field(default=None, description='经度')
    latitude: Optional[float] = Field(default=None, description='纬度')
    create_time: Optional[datetime] = Field(default_factory=datetime.now, description='创建时间')
    status: Optional[str] = Field(default='健康', description='状态')
    dir: Optional[int] = Field(default=None, description='关联文件夹ID')





class NodeQueryModel(BaseModel):
    """
    节点不分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(default=None, description='ID')
    name: Optional[str] = Field(default=None, description='节点名')
    longitude: Optional[float] = Field(default=None, description='经度')
    latitude: Optional[float] = Field(default=None, description='纬度')
    status: Optional[str] = Field(default=None, description='状态')
    dir: Optional[int] = Field(default=None, description='关联文件夹ID')


@as_query
class NodePageQueryModel(NodeQueryModel):
    """
    节点分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteNodeModel(BaseModel):
    """
    删除节点模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的ID')
