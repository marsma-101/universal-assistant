# 通用私人助理 · 情报官（universal-assistant）技能

> **名称澄清**：本项目 `universal-assistant` 为独立项目，与网络上提及的 “UniversalAssistantPro” 无任何关联，并非同一项目、分支或衍生版本。本项目遵循“由用户控制”原则，可选操作默认不执行，不会在后台静默加载或主动写入其它软件数据。

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

> ⚠️ **安全安装须知（务必先读）**
> **绝对不要把 GitHub 链接直接丢给 agent 并命令「装上」**。`install.py` 与 `tools/install-nvwa.py` 会执行文件复制和网络拉取，`tools/propagate.py` 甚至会跨软件写入人设数据（虽默认不执行）。未审查就让 agent 自动跑这些脚本，等于授予它在你电脑上任意写文件的权限。
> **推荐安全流程**：① 先 `git clone` 到本地 → ② 人工审查 `SKILL.md` 与 `install.py` 内容 → ③ 手动 `python install.py --root <技能根>` → ④ 重启 agent 会话 → ⑤ 首次激活时核对 `scripts/check_install.py` 自检结果。若你的 agent 支持 `gh skill` 命令，可相对安全地用 `gh skill install marsma-101/universal-assistant universal-assistant`，它会自动处理目录规范——但装前审查仓库仍是必要习惯。

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

### 方式四：一键脚本（install.sh / install.ps1）

仓库根目录提供跨平台一键安装脚本，内部即「正确目录名克隆 + 运行安装器」：

```bash
# Windows（PowerShell，在仓库目录内）
.\install.ps1 $env:USERPROFILE\.workbuddy\skills
# 其它（bash / Git Bash）
bash install.sh ~/.workbuddy/skills
```

环境变量推断失败时，脚本会打印各 agent 技能根示例并引导你手动指定。

### 方式五：Download ZIP 后先做目录名校验（post-download-check.sh）

若用了「Download ZIP」（解压得到带 `-main` 后缀的目录），**务必先跑校验脚本**再装——它能自动检测并把目录改名回 `universal-assistant`，否则规范型 agent 会静默跳过本技能：

```bash
bash post-download-check.sh        # 在解压出的目录内执行
```

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
├── install.sh            # 一键安装（bash）：正确目录名克隆 + 跑安装器
├── install.ps1           # 一键安装（PowerShell）：Windows 原生同效
├── post-download-check.sh # 下载/解压后校验目录名，自动修复 -main 陷阱
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
