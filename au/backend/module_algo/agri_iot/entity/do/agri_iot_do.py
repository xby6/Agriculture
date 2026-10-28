from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from config.database import Base


class AgriDevice(Base):
    """
    农业传感设备表
    """

    __tablename__ = 'agri_device'

    id = Column(Integer, primary_key=True, comment='ID')
    base_id = Column(String(64), nullable=True, comment='基地ID')
    plot_id = Column(String(64), nullable=True, comment='地块ID')
    vendor_name = Column(String(64), nullable=False, server_default='0531yun', comment='厂商名称')
    vendor_device_addr = Column(String(128), nullable=False, comment='厂商设备地址')
    device_name = Column(String(255), nullable=True, comment='设备名称')
    device_code = Column(String(128), nullable=True, comment='设备编码')
    group_id = Column(String(128), nullable=True, comment='云平台分组ID')
    longitude = Column(Float, nullable=True, comment='经度')
    latitude = Column(Float, nullable=True, comment='纬度')
    device_status = Column(String(32), nullable=True, comment='设备状态')
    save_data_interval = Column(Integer, nullable=True, comment='保存间隔')
    offline_interval = Column(Integer, nullable=True, comment='离线间隔')
    last_seen_at = Column(DateTime(timezone=True), nullable=True, comment='最后在线时间')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), comment='更新时间'
    )

    __table_args__ = (
        UniqueConstraint('vendor_name', 'vendor_device_addr', name='uk_agri_device_vendor_addr'),
        Index('idx_agri_device_base_plot', 'base_id', 'plot_id'),
    )


class AgriMetricMapping(Base):
    """
    厂商因子与标准指标映射表
    """

    __tablename__ = 'agri_metric_mapping'

    id = Column(Integer, primary_key=True, comment='ID')
    vendor_device_addr = Column(String(128), nullable=False, comment='厂商设备地址')
    node_id = Column(String(64), nullable=False, comment='节点ID')
    register_id = Column(String(64), nullable=False, comment='寄存器ID')
    factor_id = Column(String(128), nullable=True, comment='因子ID')
    factor_name = Column(String(255), nullable=True, comment='因子名称')
    metric_code = Column(String(64), nullable=False, comment='标准指标编码')
    source_unit = Column(String(32), nullable=True, comment='原始单位')
    standard_unit = Column(String(32), nullable=True, comment='标准单位')
    coefficient = Column(Numeric(18, 6), nullable=True, comment='系数')
    offset = Column(Numeric(18, 6), nullable=True, comment='偏移量')
    digits = Column(Integer, nullable=True, comment='保留小数')
    enabled = Column(Boolean, nullable=False, server_default=text('true'), comment='是否启用')

    __table_args__ = (
        UniqueConstraint('vendor_device_addr', 'node_id', 'register_id', name='uk_agri_metric_mapping_device_node_reg'),
    )


class AgriSensorObservation(Base):
    """
    农业传感器观测历史表
    """

    __tablename__ = 'agri_sensor_observation'

    id = Column(Integer, primary_key=True, comment='ID')
    device_id = Column(Integer, ForeignKey('agri_device.id', ondelete='CASCADE'), nullable=False, comment='设备ID')
    plot_id = Column(String(64), nullable=True, comment='地块ID')
    node_id = Column(String(64), nullable=False, comment='节点ID')
    register_id = Column(String(64), nullable=False, comment='寄存器ID')
    metric_code = Column(String(64), nullable=False, comment='标准指标编码')
    metric_value = Column(Numeric(18, 6), nullable=True, comment='指标值')
    metric_unit = Column(String(32), nullable=True, comment='单位')
    alarm_level = Column(Integer, nullable=True, comment='报警等级')
    alarm_info = Column(String(255), nullable=True, comment='报警信息')
    observed_at = Column(DateTime(timezone=True), nullable=False, comment='观测时间')
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment='接收时间')
    quality_flag = Column(String(32), nullable=False, server_default='normal', comment='质量标记')
    raw_payload = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment='原始数据')

    __table_args__ = (
        UniqueConstraint(
            'device_id',
            'node_id',
            'register_id',
            'observed_at',
            name='uk_agri_sensor_observation_unique_point',
        ),
        Index('idx_agri_sensor_device_time', 'device_id', 'observed_at'),
        Index('idx_agri_sensor_plot_time', 'plot_id', 'observed_at'),
        Index('idx_agri_sensor_metric_time', 'metric_code', 'observed_at'),
    )


class AgriSyncLog(Base):
    """
    传感器同步日志表
    """

    __tablename__ = 'agri_sync_log'

    id = Column(Integer, primary_key=True, comment='ID')
    sync_type = Column(String(32), nullable=False, comment='同步类型')
    device_addr = Column(String(128), nullable=True, comment='设备地址')
    start_time = Column(DateTime(timezone=True), nullable=True, comment='补录开始时间')
    end_time = Column(DateTime(timezone=True), nullable=True, comment='补录结束时间')
    status = Column(String(32), nullable=False, server_default='success', comment='状态')
    total_count = Column(Integer, nullable=False, server_default='0', comment='总数')
    success_count = Column(Integer, nullable=False, server_default='0', comment='成功数')
    duplicate_count = Column(Integer, nullable=False, server_default='0', comment='重复数')
    failed_count = Column(Integer, nullable=False, server_default='0', comment='失败数')
    error_message = Column(Text, nullable=True, comment='错误信息')
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment='开始时间')
    finished_at = Column(DateTime(timezone=True), nullable=True, comment='完成时间')

    __table_args__ = (Index('idx_agri_sync_log_type_time', 'sync_type', 'started_at'),)
