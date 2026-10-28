# 水稻病害智能监测与预测平台

包含病害图像检测、变量施药处方图、环境监测及农业物联网接入功能。

## 项目结构

- `au/frontend`：Vue 3、Element Plus、Vite 前端。
- `au/backend`：Python 后端、PostgreSQL、Redis，含数据库初始化和迁移 SQL。
- `au_algo`：Pyramid-YOLOv8、Ro-YOLOv8-PKI 和变量施药处方图算法服务。
- `au_iot_gateway`：0531yun 农业物联网接入网关。

## 本地部署

1. 将 `au/backend/.env.dev.example` 复制为 `.env.dev`，填写本地数据库、Redis 和随机 JWT 密钥。生产环境使用 `.env.prod.example`。
2. 根据 [应用部署说明](au/README.md) 初始化数据库并启动前后端。
3. 根据 [算法服务说明](au_algo/README.md) 安装算法依赖并启动服务。
4. 如需物联网数据，按照 [网关说明](au_iot_gateway/README.md) 配置并启动网关。内部 API Key 需要在后端和网关保持一致。

## 模型与数据

仓库仅提供源码和配置模板，模型权重、数据集、上传影像、运行结果、临时压缩包和汇报材料不随源码上传。

模型文件需要自行准备，并按 `au_algo/model_config.yaml` 配置放置在 `au_algo/model/`。变量施药运行时需要的模型还需按相关脚本配置放置在 `au_algo/algo/variable_prescription_runtime/heatmap/exported/`。

请勿提交真实账号、密码、API Key 或生产环境配置。

## 前端验证

```bash
cd au/frontend
npm install
npm test
npm run build:prod
```

首次 GitHub 导入采用当前工作区的源码快照；本地旧历史中的大型影像和配置凭据未包含在此仓库中。
