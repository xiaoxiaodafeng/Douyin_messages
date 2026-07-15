# send_dm

抖音私信收发与自动回复工具。

## 目录
```bash
cd E:\DY\send_dm
```

## 环境配置
项目默认读取：
- `E:\DY\send_dm\.env`

关键配置：
- `DY_COOKIES`
- `ALIYUN_MAAS_API_KEY`
- `ALIYUN_MAAS_MODEL=deepseek-v4-flash`
- `ALIYUN_MAAS_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`

## 发送私信

### 默认目标
```bash
python -m send_dm send "测试私信收发功能"
```

### 简写
```bash
python -m send_dm "测试私信收发功能"
```

### 指定 sec_uid
```bash
python -m send_dm send "你好" --sec-uid "MS4wLjABAAAA..."
```

### 指定抖音号
```bash
python -m send_dm "测试私信收发功能" --douyin-id 379250456
```

### 纯数字抖音号简写
```bash
python -m send_dm 379250456 "测试私信收发功能"
```

## 接收私信
```bash
python -m send_dm recv
```

## 自动回复
```bash
python -m send_dm autoreply
```

指定模型参数：
```bash
python -m send_dm autoreply --model deepseek-v4-flash --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 常用帮助
```bash
python -m send_dm send --help
python -m send_dm recv --help
python -m send_dm autoreply --help
```

## 说明
- 支持纯数字抖音号转 uid 后发送私信
- `recv` 用于持续监听收信
- `autoreply` 用于监听并自动调用模型回复
- 详细命令可见 `操作指令.md`
