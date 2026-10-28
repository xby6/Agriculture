from sqlalchemy import Column, String, DateTime, Integer
from config.database import Base


class Task(Base):
    """
    任务表
    """

    __tablename__ = 'task'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment='任务唯一标识')
    name = Column(String, nullable=False, comment='任务名称')
    container = Column(Integer, nullable=False, comment='执行容器ID')
    algo = Column(String, nullable=False, comment='算法名称')
    args = Column(String, nullable=False, comment='任务参数')
    remark = Column(String, nullable=True, comment='备注信息')
    state = Column(String, nullable=True, comment='任务状态')
    result = Column(Integer, nullable=True, comment='任务结果文件ID')
    init_time = Column(DateTime, nullable=True, comment='任务初始化时间')
    end_time = Column(DateTime, nullable=True, comment='任务结束时间')
    dept = Column(Integer, nullable=True, comment='所属部门ID')



