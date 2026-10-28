# 部署

## 病害检测记录

在“水稻病害检测”页面，可以按关键词（任务编号、病害、基地等）、病害类型和日期范围组合筛选已完成的图像检测记录。日期范围包含开始和结束当天，重置会清除筛选条件并回到第一页。

“导出筛选结果”下载 CSV 文件，包含全部匹配记录，不限于当前表格页；文件使用带 BOM 的 UTF-8 编码，可直接在 Excel 中打开。“查看结果”可查看历史任务的检测指标和标注图片，点击图片可以放大。

记录沿用现有任务和文件接口，逐页读取当前账号可访问的检测任务，无需数据库迁移。刷新或部分结果读取失败时，页面会提示当前记录和导出范围；可点击“刷新记录”重试。

前端验证：进入 `frontend` 后运行 `npm test` 和 `npm run build:prod`。

## 后端

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境
# 在.env.dev文件中配置以下关键参数：
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_NAME=...
# REDIS_HOST=localhost
# REDIS_PORT=6379

# 运行sql文件

# 1. 创建数据库
createdb -U postgres app

# 2. 导入SQL文件
psql -U postgres -d app -f sql/init.sql


# 运行后端
python app.py --env=dev
```

- 或者使用docker启动

```bash
docker build -t app .

docker save app -o app.tar

docker load -i app.tar

docker run -d -p 9099:9099 -v $(pwd)/backend:/app app
```

## 前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
yarn install

# 配置环境
# frontend\vite.config.js

# 运行前端
yarn dev

# 打包前端
yarn build:prod
```
