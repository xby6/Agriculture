from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query
from fastapi import Form




class FileModel(BaseModel):
    """
    文件表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(default=None, description='文件唯一标识')
    name: Optional[str] = Field(default=None, description='文件名')
    path: Optional[str] = Field(default=None, description='文件')
    type: Optional[str] = Field(default=None, description='文件类型')
    size: Optional[float] = Field(default=None, description='文件大小')
    root: Optional[int] = Field(default=None, description='父文件ID, 用于文件夹结构')
    upload_time: Optional[datetime] = Field(default=None, description='上传时间')
    dept: Optional[int] = Field(default=None, description='所属小组ID')

    @classmethod
    def as_form(cls, name: str|None = Form(...), type: str|None = Form(...), root: int = Form(...)):
        return cls(name=name, path=None, type=type, size=None, root=root, dept=None)




class FileQueryModel(FileModel):
    """
    文件不分页查询模型
    """
    pass


@as_query
class FilePageQueryModel(FileQueryModel):
    """
    文件分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    name: Optional[str] = Field(default=None, description='文件名')
    type: Optional[str] = Field(default=None, description='文件类型')
    root: Optional[int] = Field(default=None, description='父文件ID, 用于文件夹结构')
    dept: Optional[int] = Field(default=None, description='所属小组ID')


class DeleteFileModel(BaseModel):
    """
    删除文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的文件唯一标识')
