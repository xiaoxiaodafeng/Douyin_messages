# Douyin_messages

抖音私信收发与自动回复工具。

支持：
- 私信发送
- 私信实时接收
- 纯数字抖音号转 uid 后发送
- 基于大模型的自动回复

---

## 1. 项目结构

```text
send_dm/
├─ send_dm/                 # 主代码
├─ tests/                   # 测试
├─ .env.example             # 环境变量示例
├─ requirements.txt         # Python 依赖
├─ package.json             # Node 依赖
└─ 操作指令.md               # 常用命令速查
```

---

## 2. 运行环境

- Python 3.10+
- Node.js 18+
- Google Chrome
- Windows

---

## 3. 部署步骤

### 3.1 克隆项目

```bash
git clone https://github.com/xiaoxiaodafeng/Douyin_messages.git
cd Douyin_messages
```

### 3.2 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3.3 安装 Node 依赖

```bash
npm install
```

### 3.4 安装 Playwright Chrome 通道

```bash
playwright install chrome
```

### 3.5 配置环境变量

复制示例文件：

```bash
copy .env.example .env
```

然后编辑 `.env`，至少填写：

```env
DY_COOKIES=''
DY_LIVE_COOKIES=''

ALIYUN_MAAS_API_KEY=''
ALIYUN_MAAS_WORKSPACE_ID='5074654'
ALIYUN_MAAS_MODEL='deepseek-v4-flash'
ALIYUN_MAAS_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
ALIYUN_MAAS_SYSTEM_PROMPT='你是一个抖音私信自动回复助手，请结合当前会话上下文，用自然、简洁、礼貌的中文直接回复对方。'
ALIYUN_MAAS_TIMEOUT='60'
```

### 3.6 准备 Chrome Profile

项目默认读取的浏览器目录：

```text
..\ .pw-douyin-profile
```

也就是仓库同级目录下的：

```text
.pw-douyin-profile
```

这个 profile 里需要能读到抖音登录态相关的 localStorage，尤其是：

- `security-sdk/s_sdk_crypt_sdk`
- `security-sdk/s_sdk_server_cert_key`

如果不用默认目录，运行命令时可显式指定：

```bash
python -m send_dm recv --profile "你的profile目录"
```

---

## 4. 启动前检查

建议先检查 3 件事：

1. `.env` 里已经有 `DY_COOKIES`
2. Chrome Profile 存在且能读取 `security-sdk`
3. 已安装 `npm install` 和 `playwright install chrome`

---

## 5. 执行命令

先进入项目目录：

```bash
cd E:\DY\send_dm
```

如果你部署在克隆目录下，就进入你的项目目录，例如：

```bash
cd E:\Douyin_messages
```

### 5.1 发送私信

#### 发给默认目标

```bash
python -m send_dm send "测试私信收发功能"
```

#### 简写发送

```bash
python -m send_dm "测试私信收发功能"
```

#### 指定 sec_uid

```bash
python -m send_dm send "你好" --sec-uid "MS4wLjABAAAA..."
```

#### 按抖音号发送

```bash
python -m send_dm "测试私信收发功能" --douyin-id 379250456
```

#### 纯数字抖音号简写发送

```bash
python -m send_dm 379250456 "测试私信收发功能"
```

### 5.2 接收私信

```bash
python -m send_dm recv
```

如果要指定环境文件或 profile：

```bash
python -m send_dm recv --env ".env" --profile "E:\.pw-douyin-profile"
```

### 5.3 自动回复

```bash
python -m send_dm autoreply
```

指定模型参数：

```bash
python -m send_dm autoreply --model deepseek-v4-flash --base-url https://dashscope.aliyuncs.com/compatible-mode/v1
```

指定 profile / env：

```bash
python -m send_dm autoreply --env ".env" --profile "E:\.pw-douyin-profile"
```

### 5.4 查看帮助

```bash
python -m send_dm send --help
python -m send_dm recv --help
python -m send_dm autoreply --help
```

---

## 6. 常见使用场景

### 场景 1：手动发一条私信

```bash
python -m send_dm 379250456 "你好，这是测试消息"
```

### 场景 2：只监听收信

```bash
python -m send_dm recv
```

### 场景 3：开启自动回复

```bash
python -m send_dm autoreply
```

---

## 7. 参数说明

### send

- `--sec-uid`：直接指定 sec_uid
- `--douyin-id`：指定纯数字抖音号
- `--profile`：指定 Chrome Profile 目录
- `--env`：指定环境文件

### recv

- `--profile`：指定 Chrome Profile 目录
- `--env`：指定环境文件

### autoreply

- `--profile`：指定 Chrome Profile 目录
- `--env`：指定环境文件
- `--api-key`：覆盖 `.env` 中的大模型 API Key
- `--base-url`：覆盖模型接口地址
- `--workspace-id`：覆盖 workspace id
- `--model`：覆盖模型名
- `--system-prompt`：覆盖系统提示词
- `--max-context-messages`：设置上下文保留条数

---

## 8. 运行逻辑简述

### 发送私信

1. 读取 `.env` 中的 `DY_COOKIES`
2. 从 Chrome Profile 读取 `security-sdk`
3. 解析目标 uid
4. 创建会话
5. 发送文本消息

### 接收私信

1. 读取 `.env`
2. 建立 WebSocket 长连接
3. 解外层推送 protobuf
4. 解 IM 响应 protobuf
5. 解析消息内容

### 自动回复

1. 监听新私信
2. 只处理文本消息
3. 调用大模型生成回复
4. 走原私信发送链路回发

---

## 9. 故障排查

### 1）提示缺少 `DY_COOKIES`

检查：
- `.env` 是否存在
- `.env` 是否填写了 `DY_COOKIES`
- 是否通过 `--env` 指向了正确文件

### 2）提示浏览器目录不存在

检查：
- 默认 `.pw-douyin-profile` 是否存在
- 或者是否传了正确的 `--profile`

### 3）提示没有读取到 `security-sdk`

检查当前 profile 是否真的是已登录抖音的 Chrome 资料目录，并且 localStorage 中有：

- `security-sdk/s_sdk_crypt_sdk`
- `security-sdk/s_sdk_server_cert_key`

### 4）自动回复模型报错

检查：
- `ALIYUN_MAAS_API_KEY`
- `ALIYUN_MAAS_MODEL`
- `ALIYUN_MAAS_BASE_URL`

当前推荐：

```env
ALIYUN_MAAS_MODEL='deepseek-v4-flash'
ALIYUN_MAAS_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
```

---

## 10. 测试

执行现有测试：

```bash
python -m unittest tests.test_cli_resolution -v
```

---

## 11. 补充

- 常用命令速查：`操作指令.md`
- `.env` 不应提交到仓库
- `docs/` 为本地说明文档目录，不参与仓库上传
