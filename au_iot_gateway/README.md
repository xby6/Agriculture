# 0531yun农业物联网接入网关

用于将 0531yun 云平台 3.0 的设备实时与历史数据标准化后推送到后台管理系统。

## 配置

复制 `.env.example` 为 `.env`，填入真实账号、密码、groupId 和内部 API Key。

## 启动

```bash
cd au_iot_gateway
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9101
```

## 手动同步

```bash
curl -X POST http://127.0.0.1:9101/sync/realtime ^
  -H "Content-Type: application/json" ^
  -d "{\"deviceAddrs\":[]}"
```

```bash
curl -X POST http://127.0.0.1:9101/sync/history ^
  -H "Content-Type: application/json" ^
  -d "{\"deviceAddr\":\"设备地址\",\"nodeId\":-1,\"startTime\":\"2026-07-01 00:00:00\",\"endTime\":\"2026-07-02 23:59:59\"}"
```
