# AR 路由器巡检工具

基于 Flask + Ollama 的华为 AR 系列路由器智能巡检工具，通过 SSH 采集路由器运行数据，使用 AI 模型进行自动化分析和健康评估。

## 功能特性

- 🚀 **自动数据采集**: 通过 SSH 自动执行巡检命令
- 🤖 **AI 智能分析**: 使用 Ollama 本地大模型进行智能分析
- 📊 **健康评分**: 自动生成设备健康评分（0-100）
- 🔍 **风险检测**: 自动识别潜在风险和异常
- 💡 **优化建议**: 基于分析结果提供优化建议
- 📱 **实时反馈**: 通过 Server-Sent Events 实时展示巡检进度

## 支持的巡检指标

| 命令 | 说明 |
|------|------|
| `display version` | 设备版本信息 |
| `display cpu-usage` | CPU 使用率 |
| `display memory` | 内存使用情况 |
| `display interface brief` | 接口状态概览 |
| `display ip routing-table` | 路由表信息 |
| `display logbuffer \| include ERROR` | 错误日志 |

## 技术栈

- **Python**: 3.11+
- **Flask**: 2.3.3
- **Paramiko**: SSH 客户端
- **Ollama**: 本地大模型服务
- **DeepSeek-R1**: AI 分析模型

## 快速开始

### 环境要求

1. 安装 [Ollama](https://ollama.com/)
2. 下载 AI 模型：
   ```bash
   ollama pull deepseek-r1:7b
   ```

### 使用 Docker（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd ar-inspect

# 构建镜像
docker build -t ar-inspect:1.0 .

# 运行容器
docker-compose up -d
```

### 手动运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export ROUTER_HOST=192.168.1.1
export ROUTER_USER=admin
export ROUTER_PASS=password
export OLLAMA_URL=http://localhost:11434/api/generate

# 启动服务
python -m src.app
```

### 访问服务

打开浏览器访问: http://localhost:5000

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ROUTER_HOST` | 192.168.1.1 | 路由器 IP 地址 |
| `ROUTER_PORT` | 22 | SSH 端口 |
| `ROUTER_USER` | python | SSH 用户名 |
| `ROUTER_PASS` | Huawei@123 | SSH 密码 |
| `OLLAMA_URL` | http://ollama:11434/api/generate | Ollama API 地址 |

## 项目结构

```
ar-inspect/
├── src/
│   ├── __init__.py
│   ├── app.py          # Flask 应用入口
│   ├── collector.py    # SSH 数据采集模块
│   ├── inspect_tool.py # AI 分析模块
│   └── templates/
│       └── index.html  # 前端页面
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 安全注意事项

1. 建议使用 SSH 密钥认证代替密码认证
2. 在生产环境中使用 Docker Secrets 管理敏感配置
3. 限制服务访问权限，仅允许内网访问
4. 定期更新依赖包以修复安全漏洞

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！

## 致谢

- [Flask](https://flask.palletsprojects.com/)
- [Paramiko](https://www.paramiko.org/)
- [Ollama](https://ollama.com/)
- [DeepSeek](https://www.deepseek.com/)