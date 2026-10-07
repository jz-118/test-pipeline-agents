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

## 当前演示范围：Jenkins 流水线

当前 `Jenkinsfile` 暂时不启动多 Agent，只演示以下闭环：

```text
GitHub push -> Jenkins 拉取代码 -> 创建虚拟环境 -> 安装项目 -> pytest -> JUnit 报告
```

### Linux 节点前置检查

Jenkins 执行节点需要 Java、Git、Python 3 和 Python venv。先在节点上确认：

```bash
java -version
git --version
python3 --version
python3 -m venv --help
```

执行 Jenkins 服务的用户还需要拥有 workspace 的写权限，并能访问 PyPI 和 GitHub。

### 创建 Jenkins Pipeline Job

1. 在 Jenkins 首页点击 `New Item`。
2. 输入 `test-pipeline-agents`，选择 `Pipeline`。
3. 在 Pipeline 区域将 Definition 设为 `Pipeline script from SCM`。
4. SCM 选择 `Git`。
5. Repository URL 填写 `https://github.com/jz-118/test-pipeline-agents.git`。
6. Branch Specifier 填写 `*/main`。
7. Script Path 保持 `Jenkinsfile`。
8. 保存后点击 `Build Now` 完成首次构建。

仓库目前是公开仓库，拉取代码不需要 GitHub Credentials。流水线每两分钟轮询一次 GitHub；发现新提交后会自动触发构建。

### 演示成功、失败和恢复

先触发一次正常构建：

```bash
git commit --allow-empty -m "Trigger green pipeline"
git push
```

随后可临时把 `tests/test_smoke.py` 中的某个期望值改错并推送，展示 Jenkins 的红色构建和失败用例。例如把 `"alice"` 改成 `"wrong"`：

```bash
git add tests/test_smoke.py
git commit -m "Demo failing test"
git push
```

最后把期望值恢复为 `"alice"` 并再次推送：

```bash
git add tests/test_smoke.py
git commit -m "Fix failing test"
git push
```

这三次构建分别展示：自动触发并通过、测试阻断错误、修复后恢复绿色。

### 本地验证流水线测试

Linux/macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest tests -q
```

Windows PowerShell：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest tests -q
```

## 后续接回 Agent

流水线稳定后，再将 Agent 作为独立 stage 接入。生产环境应将火山引擎 API Key 放在 Jenkins Credentials 或虚拟机秘密管理器中，而不是提交 `.env`。
