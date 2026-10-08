# Test Pipeline Agents

Test Pipeline Agents 是一个面向 Jenkins 和 Git 工作流的 Python 命令行工具。项目将代码提交、测试执行、测试报告和测试维护连接到同一条流水线中，为后续的自然语言测试维护提供基础运行环境。

项目当前包含两部分：

- Jenkins 流水线：在代码提交后创建 Python 环境、安装项目、执行测试并发布 JUnit 报告。
- 测试维护 Agent：分析测试上下文、根据请求修改测试脚本，并对修改结果进行审查。

## 项目结构

```text
.
├── Jenkinsfile                 # Jenkins Pipeline 定义
├── pyproject.toml              # Python 项目和依赖配置
├── requirements.txt            # 基础依赖列表
├── pipeline_agent/
│   ├── agents.py               # Context、Executor、Review Agent
│   ├── cli.py                  # 命令行入口
│   ├── config.py               # 环境变量配置
│   ├── demo_target.py           # 示例业务函数
│   ├── orchestrator.py          # Agent 工作流编排
│   ├── provider.py              # 火山引擎模型接口
│   └── workspace.py             # 测试工作区文件操作
└── tests/
    └── test_smoke.py            # 项目测试
```

## 流水线工作流

Jenkins 使用仓库根目录的 `Jenkinsfile`，每次检测到 `main` 分支的新提交后执行以下步骤：

```text
Git push
  -> Jenkins 拉取代码
  -> 创建 .venv
  -> 安装项目和测试依赖
  -> 执行 pytest
  -> 生成 JUnit XML
  -> Jenkins 发布测试结果
```

流水线包含 `Environment` 和 `Test` 两个阶段，并设置了构建超时和并发构建控制。测试报告保存在 `reports/junit.xml`，Jenkins 可以据此展示测试数量、失败用例和历史趋势。

## 环境要求

开发机或 Jenkins 执行节点需要：

- Python 3.10 或更高版本
- Git
- Python `venv` 模块
- Jenkins Pipeline、JUnit 插件

Jenkins 节点还需要能够访问 GitHub 和 Python 包索引。Linux 节点可以使用以下命令检查环境：

```bash
java -version
git --version
python3 --version
python3 -m venv --help
```

## 本地安装

Linux/macOS：

```bash
git clone https://github.com/jz-118/test-pipeline-agents.git
cd test-pipeline-agents
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
```

Windows PowerShell：

```powershell
git clone https://github.com/jz-118/test-pipeline-agents.git
cd test-pipeline-agents
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

## 运行测试

在已激活虚拟环境的情况下执行：

```bash
python -m pytest tests -q
```

生成 Jenkins 使用的 JUnit 报告：

```bash
mkdir -p reports
python -m pytest tests -q --junitxml=reports/junit.xml
```

当前测试覆盖用户名规范化和空用户名校验，共包含 4 个测试用例。`pipeline_agent/demo_target.py` 提供了用于测试的示例业务函数。

## Jenkins 配置

### 创建 Pipeline Job

1. 打开 Jenkins 首页，选择 `New Item`。
2. 输入 Job 名称，例如 `test-pipeline-agents`。
3. 选择 `Pipeline`，点击确认。
4. 在 Pipeline 配置中，将 Definition 设置为 `Pipeline script from SCM`。
5. SCM 选择 `Git`。
6. Repository URL 填写：

   ```text
   https://github.com/jz-118/test-pipeline-agents.git
   ```

7. Branch Specifier 填写 `*/main`。
8. Script Path 填写 `Jenkinsfile`。
9. 保存 Job 并执行构建。

仓库为公开仓库时，拉取代码不需要配置 GitHub 凭据。Jenkinsfile 使用 `pollSCM('H/2 * * * *')` 检查新提交，检测到 `main` 分支变化后自动开始构建。

### Jenkinsfile 说明

`Environment` 阶段执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

`Test` 阶段执行：

```bash
mkdir -p reports
.venv/bin/python -m pytest tests -q --junitxml=reports/junit.xml
```

构建结束后，`post` 区块使用 Jenkins JUnit 插件读取 `reports/junit.xml`，同时归档报告文件。

## 命令行工具

安装项目后可以使用 `pipeline-agent` 命令：

```bash
pipeline-agent run --help
```

分析当前工作区并请求 Agent 更新测试：

```bash
pipeline-agent run "给登录接口增加无效 token 测试"
```

指定 Git 提交范围：

```bash
pipeline-agent run \
  --base-ref HEAD~1 \
  --head-ref HEAD \
  "为本次提交增加回归测试"
```

查看当前测试文件和提交差异，而不调用模型：

```bash
pipeline-agent run --dry-run
```

## Agent 架构

测试维护流程由三个角色组成：

### Context Agent

Context Agent 读取测试文件列表和相关差异，生成项目测试上下文摘要，供当前任务使用。摘要包含测试框架、测试目录、代码约定和已知风险。

### Executor Agent

Executor Agent 根据自然语言请求和上下文生成测试文件修改内容。文件操作通过 `TestWorkspace` 完成，测试目录是它的工作范围。

### Review Agent

Review Agent 读取测试差异和测试结果，输出结构化审查结论。它不保存任务状态，也不直接修改文件。

### Orchestrator

Orchestrator 负责 Agent 调用顺序、测试执行、结果审查、超时和最大循环次数：

```text
Context Agent
      -> Executor Agent
      -> pytest
      -> Review Agent
      -> approved / needs-human-review
```

任务参数通过环境变量配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AGENT_TIMEOUT_SECONDS` | `120` | 单次模型调用和任务执行的超时设置 |
| `AGENT_MAX_ROUNDS` | `3` | Executor 和 Review 的最大往返次数 |
| `AGENT_DRY_RUN` | `false` | 是否只读取工作区信息 |

## 火山引擎配置

复制配置模板：

```bash
cp .env.example .env
```

在 `.env` 中填写模型服务配置：

```dotenv
VOLCENGINE_API_KEY=your-api-key
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=your-model-endpoint
AGENT_TIMEOUT_SECONDS=120
AGENT_MAX_ROUNDS=3
AGENT_DRY_RUN=false
```

`.env` 已加入 `.gitignore`。Jenkins 环境可以将这些变量配置在 Jenkins Credentials 或节点环境中。

## Git 工作流

提交测试修改并推送：

```bash
git add .
git commit -m "Update tests"
git push origin main
```

Jenkins 轮询到新提交后，会使用该提交的 Jenkinsfile 创建构建并发布测试结果。

## 许可证

项目代码目前以仓库内容为准，后续可根据发布方式补充许可证文件。
