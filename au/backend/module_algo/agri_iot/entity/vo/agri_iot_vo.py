from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from utils.common_util import CamelCaseUtil


class AgriMetricModel(BaseModel):
    """
    标准化指标数据
    """

    model_config = ConfigDict(alias_generator=CamelCaseUtil.snake_to_camel, populate_by_name=True)

    node_id: Optional[Union[str, int]] = None
    register_id: Optional[Union[str, int]] = None
    factor_id: Optional[Union[str, int]] = None
    factor_name: Optional[str] = None
    metric_code: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    alarm_level: Optional[int] = None
    alarm_info: Optional[str] = None
    quality_flag: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class AgriTelemetryRecordModel(BaseModel):
    """
    标准化设备遥测数据
    """

    model_config = ConfigDict(alias_generator=CamelCaseUtil.snake_to_camel, populate_by_name=True)

    vendor_name: str = '0531yun'
    device_addr: str
    device_name: Optional[str] = None
    device_code: Optional[str] = None
    group_id: Optional[Union[str, int]] = None
    base_id: Optional[Union[str, int]] = None
    plot_id: Optional[Union[str, int]] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    device_status: Optional[str] = None
    save_data_interval: Optional[int] = None
    offline_interval: Optional[int] = None
    observed_at: Optional[Union[datetime, str, int, float]] = None
    metrics: List[AgriMetricModel] = Field(default_factory=list)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class AgriTelemetryBatchModel(BaseModel):
    """
    标准化遥测批次
    """

    model_config = ConfigDict(alias_generator=CamelCaseUtil.snake_to_camel, populate_by_name=True)

    sync_type: str = 'realtime'
    device_addr: Optional[str] = None
    start_time: Optional[Union[datetime, str, int, float]] = None
    end_time: Optional[Union[datetime, str, int, float]] = None
    records: List[AgriTelemetryRecordModel] = Field(default_factory=list)


class AgriRealtimeSyncModel(BaseModel):
    """
    实时同步触发参数
    """

    model_config = ConfigDict(alias_generator=CamelCaseUtil.snake_to_camel, populate_by_name=True)

    device_addrs: Optional[List[str]] = None


class AgriHistorySyncModel(BaseModel):
    """
    历史同步触发参数
    """

    model_config = ConfigDict(alias_generator=CamelCaseUtil.snake_to_camel, populate_by_name=True)

    device_addr: str
    node_id: Union[str, int] = -1
    start_time: Union[datetime, str]
    end_time: Union[datetime, str]
