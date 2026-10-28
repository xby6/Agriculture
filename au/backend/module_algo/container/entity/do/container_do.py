from sqlalchemy import Column, String, DateTime, Integer
from config.database import Base


class Container(Base):
    """
    容器表
    """

    __tablename__ = 'container'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment='容器唯一标识')
    name = Column(String, nullable=False, comment='容器名称')
    url = Column(String, nullable=False, comment='容器URL')
    type = Column(String, nullable=True, comment='容器类型')
    create_time = Column(DateTime, nullable=True, comment='创建时间')
    dept = Column(Integer, nullable=True, comment='所属部门ID')



