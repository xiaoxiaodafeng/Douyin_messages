# 抖音私信收发信息

## 部署命令

### 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 安装 Node 依赖

```bash
npm install
```

### 安装 Playwright Chrome

```bash
playwright install chrome
```

### 复制环境文件

```bash
copy .env.example .env
```

---

## 可用指令

### 1. 发送私信

发送一条文本私信。

```bash
python -m send_dm send "测试私信收发功能"
```

### 2. 简写发送

不写 `send`，直接发送文本。

```bash
python -m send_dm "测试私信收发功能"
```

### 3. 按 sec_uid 发送

指定目标 `sec_uid` 发送私信。

```bash
python -m send_dm send "你好" --sec-uid "MS4wLjABAAAA..."
```

### 4. 按抖音号发送

输入抖音号，自动解析后发送。

```bash
python -m send_dm "测试私信收发功能" --douyin-id 379250456
```

### 5. 接收私信

持续监听私信消息。

```bash
python -m send_dm recv
```

### 6. 自动回复

监听新私信，并调用大模型自动回复。

```bash
python -m send_dm autoreply
```

### 7. 指定模型参数启动自动回复

```bash
python -m send_dm autoreply --model deepseek-v4-flash --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 8. 指定 env / profile

指定环境文件或浏览器资料目录。

```bash
python -m send_dm recv --env ".env" --profile "E:\.pw-douyin-profile"
python -m send_dm autoreply --env ".env" --profile "E:\.pw-douyin-profile"
python -m send_dm send "你好" --env ".env" --profile "E:\.pw-douyin-profile"
```

### 9. 查看帮助

```bash
python -m send_dm send --help
python -m send_dm recv --help
python -m send_dm autoreply --help
```

### 10. 运行测试

```bash
python -m unittest tests.test_cli_resolution -v
```
