from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from module_algo.statistics.service.statistics_service import StatisticsService
from utils.response_util import ResponseUtil
from config.get_db import get_db


statisticsController = APIRouter(prefix="/statistics", tags=["统计管理"])


@statisticsController.get("/all", summary="获取所有统计数据")
async def get_all_statistics(db: AsyncSession = Depends(get_db)):
    """获取所有模块的统计数据"""
    try:
        statistics = await StatisticsService.get_all_statistics_services(db)
        return ResponseUtil.success(data=statistics, msg="获取所有统计数据成功")
    except Exception as e:
        return ResponseUtil.failure(msg=f"获取统计数据失败: {str(e)}")


@statisticsController.get("/agriculture/overview", summary="获取农业平台总览数据")
async def get_agriculture_overview(db: AsyncSession = Depends(get_db)):
    """获取农业平台大屏、数据采集和模型服务总览。"""
    try:
        overview = await StatisticsService.get_agriculture_overview_services(db)
        return ResponseUtil.success(data=overview, msg="获取农业平台总览数据成功")
    except Exception as e:
        return ResponseUtil.failure(msg=f"获取农业平台总览数据失败: {str(e)}")
