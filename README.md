# Log Search MCP Server

一个基于 MCP (Model Context Protocol) 的日志搜索服务器，为 AI 助手提供跨多台应用服务器的日志搜索能力。该服务器通过 SSH 和 grep 命令实现对远程服务器日志文件的搜索。

## 功能特性

- **多服务器管理**: 配置和管理多个应用服务器
- **SSH 日志搜索**: 通过 SSH 使用 grep 命令搜索日志
- **时间范围过滤**: 支持时间范围过滤（如 "1h", "30m", "2d"）
- **模式匹配**: 高级 grep 模式匹配能力
- **安全认证**: 支持密钥认证和密码认证
- **错误处理**: 健壮的错误处理和超时管理
- **MCP 协议**: 标准的 MCP 接口，便于 AI 助手集成
- **自定义日志路径**: 支持自定义日志文件路径
- **并发搜索**: 支持多服务器并发搜索

## 安装

### 前置要求

- Python 3.12 或更高版本
- 对目标服务器的 SSH 访问权限
- 适当的文件读取权限

### 从源码安装

```bash
# 克隆仓库
git clone <repository-url>
cd log-search-mcp

# 安装依赖
pip install -e .

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 使用 uv 安装（推荐）

```bash
# 使用 uv 包管理器
uv sync

# 或直接安装
uv run log-search-mcp --help
```

## 配置

创建配置文件 `log_search_config.toml`：

```toml
# Log Search MCP Server Configuration
# 日志搜索 MCP 服务器配置

# Default settings for log search operations
# 日志搜索操作的默认设置
default_timeout = 30  # seconds
max_results = 100     # maximum results per search

# Server configurations
# 服务器配置
[servers]

# Example server configuration
# 示例服务器配置
[servers.cls-sit]
hostname = "127.0.0.1"
port = 22
username = "user"
password = "passwd"  # 如果使用密码认证，取消注释并设置
# private_key_path = "/path/to/private/key"  # 如果使用密钥认证，取消注释并设置路径
app_name = "cls"
timeout = 45
log_paths = "/opt/logs/cls/cls-all.log,/opt/logs/cls/cls-bee.log"

[servers.webapp-prod]
hostname = "webapp-prod.example.com"
port = 22
username = "deploy"
private_key_path = "/path/to/private/key"
app_name = "webapp"
timeout = 30
# log_paths = "/opt/logs/webapp/webapp.log"  # 可选：自定义日志路径

[servers.api-staging]
hostname = "api-staging.example.com"
port = 22
username = "deploy"
private_key_path = "/path/to/private/key"
app_name = "api"
timeout = 30
```

### 配置选项

- **hostname**: 服务器主机名或 IP 地址
- **port**: SSH 端口（默认：22）
- **username**: SSH 用户名
- **private_key_path**: 私钥文件路径（推荐使用）
- **password**: SSH 密码（仅在无法使用密钥认证时使用）
- **app_name**: 应用名称，用于默认日志文件路径
- **timeout**: SSH 连接超时时间（秒）
- **log_paths**: 自定义日志文件路径（可选，逗号分隔）

## 使用

### 运行服务器

#### 直接运行 MCP 服务器

```bash
# 运行 MCP 服务器
python main.py

# 或使用 uv
uv run log-search-mcp

# 指定配置文件路径
python main.py --config custom_logs_config.toml
```

#### 使用 MCP Inspector 调试

```bash
# 使用 MCP Inspector 运行服务器（用于调试）
npx @modelcontextprotocol/inspector uv --directory . run log-search-mcp

# 如果 Inspector 需要传递参数给 MCP 服务器，使用 -- 分隔符
npx @modelcontextprotocol/inspector uv --directory . run log-search-mcp -- --config ./log_search_config.toml
```

#### 在 Claude Desktop 中配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "log-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/log-search-mcp",
        "run",
        "log-search-mcp",
        "--config",
        "/path/to/log_search_config.toml"
      ]
    }
  }
}
```

### MCP 工具使用

服务器提供一个工具：`search_logs`

#### 参数

- **server_name**: 要搜索的服务器名称（使用 "all" 搜索所有服务器）
- **pattern**: 在日志中搜索的 grep 模式
- **time_range** (可选): 时间范围过滤器（如 "1h", "30m", "2d", "2024-01-01 to 2024-01-02"）
- **max_results** (可选): 每个服务器返回的最大结果数

#### 示例

```json
{
  "server_name": "cls-sit",
  "pattern": "ERROR",
  "time_range": "1h",
  "max_results": 50
}
```

```json
{
  "server_name": "all",
  "pattern": "database.*timeout",
  "time_range": "30m"
}
```

```json
{
  "server_name": "webapp-prod",
  "pattern": "404|500",
  "time_range": "2h"
}
```

### 日志文件路径

服务器在每个服务器上搜索以下日志文件路径（如果未指定自定义路径）：
- `/opt/logs/{app_name}/{app_name}.log`
- `/opt/logs/{app_name}/{app_name}.bee.log`

如果配置了 `log_paths`，则使用自定义路径。

## 开发

### 项目结构

```
log_search_mcp/
├── config/          # 配置管理
├── models/          # 数据模型 (Pydantic)
├── tools/           # MCP 工具实现
├── utils/           # 工具函数
└── server.py        # 主 MCP 服务器
```

### 测试

```bash
# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=log_mcp

# 运行特定测试文件
pytest tests/test_config.py

# 运行 MCP 服务器测试
python test_mcp.py
```

### 代码质量

```bash
# 格式化代码
black log_search_mcp/ tests/

# 排序导入
isort log_search_mcp/ tests/

# 类型检查
mypy log_search_mcp/
```

### 手动测试

```bash
# 运行手动测试脚本
python test_mcp.py
```

## API 参考

### LogSearchTool

提供日志搜索功能的主要工具类。

#### 方法

- `search_logs(server_name, pattern, time_range=None, max_results=None)`: 在特定服务器上搜索日志
- `search_all_logs(pattern, time_range=None, max_results=None)`: 在所有服务器上搜索日志
- `get_search_tool()`: 获取 MCP 工具定义

### ConfigManager

管理服务器配置的加载和持久化。

#### 方法

- `load_config()`: 从 TOML 文件加载配置
- `save_config()`: 保存配置到 TOML 文件
- `add_server(server_config)`: 添加新的服务器配置
- `remove_server(server_name)`: 移除服务器配置
- `update_server(server_config)`: 更新服务器配置
- `list_servers()`: 列出所有配置的服务器
- `get_server(server_name)`: 获取特定服务器配置

### SSHConnectionManager

管理到远程服务器的 SSH 连接。

#### 方法

- `connect(server_config)`: 建立 SSH 连接
- `execute_command(server_config, command, timeout=None)`: 在服务器上执行命令
- `close_connection(server_name)`: 关闭特定连接
- `close_all()`: 关闭所有连接
- `get_connection_status()`: 获取连接状态

## 安全考虑

- **私钥**: 安全存储私钥并设置适当的权限
- **密码**: 尽可能使用基于密钥的认证
- **配置**: 保护配置文件安全，避免提交敏感数据
- **网络安全**: 确保 SSH 连接使用安全协议

## 故障排除

### 常见问题

1. **连接超时**: 检查网络连接和防火墙设置
2. **认证失败**: 验证 SSH 密钥和权限
3. **日志文件访问**: 确保 SSH 用户有读取日志文件的权限
4. **配置错误**: 验证 TOML 语法和文件路径

### 调试模式

启用调试日志以进行详细故障排除：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献

1. 遵循 OpenSpec 工作流程进行更改
2. 为新功能编写测试
3. 维护代码质量标准
4. 相应更新文档

## 许可证

[添加适当的许可证信息]

## 支持

如有问题和疑问：
- 在仓库中创建 issue
- 查看故障排除部分
- 查看配置示例

## 相关项目

- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) - 模型上下文协议
- [asyncssh](https://github.com/ronf/asyncssh) - 异步 SSH 库
- [Pydantic](https://docs.pydantic.dev/) - 数据验证库