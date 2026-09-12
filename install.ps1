# install.ps1 — universal-assistant 一键安装（Windows PowerShell）
#
# 用法（在仓库目录内右键「使用 PowerShell 运行」，或）：
#   .\install.ps1 <技能根目录>      例： .\install.ps1 $env:USERPROFILE\.workbuddy\skills
#   .\install.ps1                   仅打印用法与各 agent 技能根示例
#
# 行为：
#   1. 克隆到 <技能根>/universal-assistant（目录名自动正确，避免 ZIP -main 陷阱）
#   2. 运行自带安装器 install.py（女娲决策树 + 安装自检 + 汇报）
# 说明：只复制本技能自身，不碰其它软件数据；女娲缺失不阻断安装。
param(
  [string]$Root = ""
)

$ErrorActionPreference = "Stop"
$Repo  = "https://github.com/marsma-101/universal-assistant.git"
$Name  = "universal-assistant"

if (-not $Root) {
  Write-Host "用法: .\install.ps1 <技能根目录>"
  Write-Host "示例:"
  Write-Host "  .\install.ps1 $env:USERPROFILE\.workbuddy\skills   # WorkBuddy"
  Write-Host "  .\install.ps1 $env:USERPROFILE\.claude             # Claude Code"
  Write-Host "  .\install.ps1 $env:USERPROFILE\.codex             # Codex"
  Write-Host ""
  Write-Host "不传参数则只打印以上帮助。"
  exit 2
}

# 展开 $env:... / ~ 等
$Root = $ExecutionContext.InvokeCommand.ExpandString($Root)
if ($Root -match '^~[\\/]') { $Root = Join-Path $HOME $Root.Substring(1) }

$Dest = Join-Path $Root $Name
if (-not (Test-Path $Root)) { New-Item -ItemType Directory -Path $Root -Force | Out-Null }

if (Test-Path $Dest) {
  Write-Host "[跳过] 已存在: $Dest"
} else {
  Write-Host "克隆到(目录名已自动正确): $Dest"
  git clone $Repo $Dest
  if (-not (Test-Path $Dest)) {
    Write-Host "[失败] 克隆失败，请检查 git/网络，或手动："
    Write-Host "  git clone $Repo `"$Dest`""
    exit 1
  }
}

Write-Host "运行自安装器（女娲决策树 + 安装自检）..."
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py (Join-Path $Dest "install.py") --root $Root
if ($LASTEXITCODE -ne 0) {
  Write-Host "[提示] 安装器返回非零（可能非交互环境）。可改跑："
  Write-Host "  $py `"$Dest\install.py`" --root `"$Root`" --no-nvwa"
}
Write-Host "安装完成。请重启 agent 会话使技能生效。"
