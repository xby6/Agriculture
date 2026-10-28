import asyncio
import shutil
import sys
import os
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log')
    ]
)

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BaseModel.model_config["protected_namespaces"] = ()


from core.algorithm_executor import result_listener
from core.process_manager import ProcessManager

from api.algorithm_routes import algorithm_routes
from api.model_routes import model_routes
from api.execution_routes import execution_routes

def create_app():

    # 延迟初始化管理器
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pm = ProcessManager()
        pm.initialize()
        app.state.pm = pm

        asyncio.create_task(result_listener(pm))
        yield

        # 清理所有临时文件
        async with pm.lock:
            for task_id, (p, temp_dir, _) in pm.task_map.items():
                if p.is_alive():
                    p.terminate()
                shutil.rmtree(temp_dir, ignore_errors=True)
        pm.shutdown()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"]
    )

    
    # 注册路由
    app.include_router(algorithm_routes)
    app.include_router(model_routes)
    app.include_router(execution_routes)
    
    return app

if __name__ == '__main__':

    import uvicorn
    from multiprocessing import freeze_support

    freeze_support()
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
