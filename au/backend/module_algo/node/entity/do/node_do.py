from sqlalchemy import Integer, String, DateTime, Float, Column
from config.database import Base


class NodeInfo(Base):
    """
    节点表
    """

    __tablename__ = 'node_info'

    id = Column(Integer, primary_key=True, comment='ID')
    name = Column(String, nullable=True, comment='节点名')
    longitude = Column(Float, nullable=True, comment='经度')
    latitude = Column(Float, nullable=True, comment='纬度')
    create_time = Column(DateTime, nullable=True, comment='创建时间')
    status = Column(String, nullable=True, comment='状态')
    dir = Column(Integer, nullable=True, comment='关联文件夹ID')



