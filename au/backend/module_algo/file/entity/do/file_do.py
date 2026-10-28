from sqlalchemy import Column, DateTime, String, Float, Integer
from config.database import Base


class File(Base):
    """
    文件表
    """

    __tablename__ = 'file'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment='文件唯一标识')
    name = Column(String, nullable=True, comment='文件名')
    path = Column(String, nullable=True, comment='文件路径')
    type = Column(String, nullable=True, comment='文件类型')
    size = Column(Float, nullable=True, comment='文件大小')
    root = Column(Integer, primary_key=True, nullable=False, comment='父文件ID, 用于文件夹结构')
    upload_time = Column(DateTime, nullable=True, comment='上传时间')
    dept = Column(Integer, nullable=True, comment='所属小组ID')



