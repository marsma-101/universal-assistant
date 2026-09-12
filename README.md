# 通用私人助理 · 情报官（universal-assistant）技能

一个**可重命名、可移植**的通用 AI 助理技能模板。任何人拿到后起个名字即可用，预设能力全部内置，无需从头调教。

## 它是什么

本技能把「私人助理 / 情报官 / 调度前端」三种角色合成一个可复用的身份：

- **情报官**：收集信息、交叉验证、信源分级（`[一手]/[二手]/[推断]`）、存疑必标。
- **参谋**：只把信息收拾干净摆在你面前，**绝不替你下结论**（非高风险可给「临时倾向+依据+反方最强论点」）。
- **调度前端**：遇专业领域先建议你蒸馏一位专家当顾问，遇执行类任务转交执行智能体。

> 它自己不下结论、不替你干活——只整理、汇总，给出「已知事实 / 关键不确定 / 各选项利弊 / 你需拍板的点」。

## 核心能力

| 能力 | 说明 |
|---|---|
| 敏锐感知 | 先察觉、先看到细节 |
| 沉浸式调研 | 沉到现场拿一手，不靠二手拼凑 |
| 交叉验证 + 信源分级 | 事实标 `[一手]/[二手]/[推断]`，单源不进结论区，存疑必标 `[存疑]` |
| 悬置判断 | 呈现事实，结论留给你 |
| 办事妥帖 + 能读人 | 先确认再动手；看懂你没说的意图时给建议、由你决策，不擅自行动 |

## 安装（自安装模型）

本技能遵循「**自安装**」模型：你把仓库交给**自己的** agent，由该 agent 把自己装进去——不是由一个 agent 去扫描并改写其它 agent 软件的数据。跨软件写入人设是可选的独立工具（`tools/propagate.py`），默认不执行。

### 方式一：克隆（推荐，目录名自动正确）

```bash
git clone https://github.com/marsma-101/universal-assistant.git <技能根>/universal-assistant
```

> `<技能根>` 即你的 agent 的技能目录，例如 Claude Code 的 `~/.claude`、WorkBuddy 的 `~/.workbuddy/skills`、DSH 的技能根。

### 方式二：Download ZIP（注意目录名！）

GitHub 的「Download ZIP」解压后得到的是 `universal-assistant-main/`（多了 `-main` 后缀）。而 Agent Skills 规范**硬性要求目录名 == 技能 `name`（`universal-assistant`）**，带 `-main` 时规范型 agent 会**静默跳过**整个技能（不报错）。

**解压后必须改名：** 

```bash
mv universal-assistant-main universal-assistant
```

### 方式三：用自带安装器（自动处理目录名校验）

```bash
python install.py --agent claude-code          # 读环境变量推断技能根
python install.py --root ~/.claude             # 显式指定技能根
```

安装器只做一件事：把本技能复制到 `<技能根>/universal-assistant` 并校验目录名与 frontmatter，随后提示你**重启 agent 会话**（DSH 有文件监听可即时生效）。它不碰任何其它软件的数据。

### 可选依赖：女娲（huashu-nvwa）

蒸馏领域专家需要女娲，但它**不是运行本助理的前提**——未装时通用信息正常干活、专业领域降级为通用简报。

```bash
python tools/install-nvwa.py --root <技能根>   # 默认从咱们镜像 marsma-101/nuwa-skill 拉取，并校验归属指向 alchaincyf（上游），防装到旧镜像
```

或手动：`git clone https://github.com/marsma-101/nuwa-skill.git <技能根>/huashu-nvwa`。
上游官方仓库：https://github.com/alchaincyf/nuwa-skill （作者：花叔，MIT）；咱们镜像：https://github.com/marsma-101/nuwa-skill。

### 首次激活时会发生什么

助理会：① 请你起个名字（写入 config）；② 检查女娲（可选，缺失不阻断）；③ 运行 `scripts/check_install.py` 自检安装规范性；④ 向你汇报。后续激活直接读 config，不再重复提问。

## 改名 / 改称呼

运行期配置优先级：`~/.universal-assistant/config.json` > `<技能目录>/config.json` > 默认值。仓库发的是 `config.json.example`（不跟踪实际 config，避免 git 弄脏）。

```json
{
  "agent_name": "",
  "address_term": "用户"
}
```

- `agent_name`：首次激活时助理会请你起名并写入；也可手动填好直接生效。
- `address_term`：助理对你的称呼，默认「用户」，可改成你习惯的叫法。

## 目录结构

```
universal-assistant/
├── SKILL.md              # 技能本体（身份/边界/协议/层级关系）
├── config.json.example   # 配置模板（实际 config.json 不入库）
├── install.py            # 自安装器：复制到 <技能根>/universal-assistant 并校验
├── references/
│   ├── examples.md       # 可验证使用示例（合同/选标的/用药+反例）
│   └── non-use-cases.md  # 不适用场景清单
├── scripts/
│   └── check_install.py  # 自检：我在哪、装得对不对（核心，首次激活调用）
├── tools/                # 可选、低频、高权限，默认不执行
│   ├── install-nvwa.py   # 安装女娲（可选依赖），带原版归属校验
│   └── propagate.py      # 跨软件写入人设（可选增强），须确认+备份+留痕
├── README.md
├── LICENSE
└── .gitignore
```

## 与其它智能体的关系

```
用户（问题提出者）
   ↓
助手智能体【本助理，名字由你起】
   · 查看问题，完善边界与目标
   · 需专业建议时：调用已蒸馏的其它智能体，或调女娲（huashu-nvwa）蒸馏对应专家
   · 制作 / 整理 / 汇总，不独立给终局方案，不独立动手解决复杂问题
   ↓
其它智能体与技能（两类）
   · 一类：提供信息 / 观点 / 方案素材（如蒸馏顾问）
   · 一类：按既定目标与框架动手干活（如执行智能体）
```

## 兼容性

需要联网检索工具（WebSearch / web_fetch 等）与子智能体能力；可选依赖 huashu-nvwa（未装时降级为通用简报）。
- **已验证**：WorkBuddy / DSH / Claude Code
- **未验证**：Codex / opencode / Hermes

## 隐私说明

- 核心技能（SKILL.md）只做自查与多源信息收集，**不读取、不上传任何隐私数据**。
- `scripts/check_install.py` 仅读取本技能自身目录，不扫描全机、不碰其它软件。
- `tools/propagate.py` 是可选工具，默认不执行；执行时也必须先出清单、逐项确认、备份原文件、回读校验、留痕（可卸载还原）。
- 本技能不含任何账号、密码或外部网络调用（女娲蒸馏在你本地完成、信息不外发）。

## 许可

MIT —— 随意使用、改名、二次分发。
