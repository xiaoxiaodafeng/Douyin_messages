# 抖音私信收发信息

## 进入目录

```bash
cd E:\DY\send_dm
```

## 部署

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

## 执行命令

### 发送私信

```bash
python -m send_dm send "测试私信收发功能"
python -m send_dm "测试私信收发功能"
python -m send_dm send "你好" --sec-uid "MS4wLjABAAAA..."
python -m send_dm "测试私信收发功能" --douyin-id 379250456
python -m send_dm 379250456 "测试私信收发功能"
```

### 接收私信

```bash
python -m send_dm recv
```

### 自动回复

```bash
python -m send_dm autoreply
python -m send_dm autoreply --model deepseek-v4-flash --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 指定 env / profile

```bash
python -m send_dm recv --env ".env" --profile "E:\.pw-douyin-profile"
python -m send_dm autoreply --env ".env" --profile "E:\.pw-douyin-profile"
python -m send_dm send "你好" --env ".env" --profile "E:\.pw-douyin-profile"
```

### 查看帮助

```bash
python -m send_dm send --help
python -m send_dm recv --help
python -m send_dm autoreply --help
```

### 运行测试

```bash
python -m unittest tests.test_cli_resolution -v
```
