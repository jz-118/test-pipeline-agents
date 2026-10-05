# Test Pipeline Agents

一个受控的 Python 命令行多 Agent 测试维护工具，面向 Jenkins + Git 工作流。Agent 的实际写权限只覆盖 `tests/`，并由确定性编排器控制超时、最大往返次数和审查结果。

## Agent 分工

- Context Agent：压缩项目测试上下文，只输出事实摘要。
- Executor Agent：读取当前测试内容，根据自然语言请求修改 `tests/` 下脚本。
- Review Agent：无状态、只读，审查 diff 和测试结果。

工具层和 diff gate 会再次验证权限，系统提示词不是唯一安全边界。

## 本地运行

```bash
cp .env.example .env
# 编辑 .env，填写 VOLCENGINE_API_KEY 和 VOLCENGINE_MODEL
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pipeline-agent run "给登录接口增加无效 token 测试"
```

没有 API Key 时可验证仓库和 CLI：

```bash
pipeline-agent run --dry-run
```

## Linux 虚拟机演示

```bash
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# 写入火山引擎配置
pipeline-agent run --base-ref HEAD~1 --head-ref HEAD
```

Jenkins 使用仓库根目录的 `Jenkinsfile`。生产环境应将 API Key 放在 Jenkins Credentials 或虚拟机秘密管理器中，而不是提交 `.env`。
