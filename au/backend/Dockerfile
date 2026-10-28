# 使用官方 Python 运行环境作为基础镜像
FROM python:3.12

# 设置工作目录
WORKDIR /app

# 将依赖信息复制到容器中
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录下的所有文件复制到容器的工作目录
COPY . .

# 暴露端口，FastAPI 默认端口是 8000
EXPOSE 9099

# 容器启动时运行的命令
CMD ["python", "app.py", "--env=dev"]
