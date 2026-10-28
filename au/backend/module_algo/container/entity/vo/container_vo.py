from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query




class ContainerModel(BaseModel):
    """
    容器表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(default=None, description='容器唯一标识')
    name: Optional[str] = Field(default=None, description='容器名称')
    url: Optional[str] = Field(default=None, description='容器URL')
    type: Optional[str] = Field(default=None, description='容器类型')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    dept: Optional[int] = Field(default=None, description='所属部门ID')

    @NotBlank(field_name='name', message='容器名称不能为空')
    def get_name(self):
        return self.name

    @NotBlank(field_name='url', message='容器URL不能为空')
    def get_url(self):
        return self.url


    def validate_fields(self):
        self.get_name()
        self.get_url()




class ContainerQueryModel(ContainerModel):
    """
    容器不分页查询模型
    """
    pass


@as_query
class ContainerPageQueryModel(ContainerQueryModel):
    """
    容器分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    name: Optional[str] = Field(default=None, description='容器名称')
    type: Optional[str] = Field(default=None, description='容器类型')
    dept: Optional[int] = Field(default=None, description='所属部门ID')


class DeleteContainerModel(BaseModel):
    """
    删除容器模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的容器唯一标识')
