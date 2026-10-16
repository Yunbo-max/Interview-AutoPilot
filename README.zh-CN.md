# AI Interview 0.6.0 · 简历、岗位、语音面试与前沿知识追踪

我们的目标不是做另一个自动投递简历工具，而是**让技术人才持续准备真正有难度、紧贴岗位要求和最新研究进展的面试**。

新工作流：**`/profile → /scrape → /rank → /interview → /memory`**。独立的 `/trends` 用于更新岗位相关论文和技术热点。保留 0.3.0 的本地语音网页、六类岗位、一小时目标阶段规划和七种模型适配方案。

## MacBook Pro 一键安装启动（0.6.0 新增）

现在本地 Codex、Claude Code、Gemini CLI 或 macOS Finder 可以直接执行
**一条命令**完成安装并启动网页：

```bash
# 在你的 MacBook Pro 上克隆源码后执行；不要让云端容器代替 Mac 安装
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
bash AI-Interview.command --yes
```

**也可以在 Finder 双击 `AI-Interview.command`**，并按提示同意网络下载。
脚本自动检测 Python；如果当前 Mac 只有旧版 Python，会通过已有 uv/Homebrew，
或下载经过固定 SHA256 校验的官方 uv 二进制来安装 Python 3.11，不需要 sudo
或远程 `curl | sh` 脚本。随后建立私有虚拟环境、安装 Python 依赖、下载本地
Faster-Whisper base 备用模型，并给 Codex/Claude 安装完整 Skill 的符号链接。
M 系列 Mac 如果尚未安装 VoiceStudio，会从官方 GitHub Release 下载**ARM64
DMG + SHA256SUMS**并在校验后复制到 `~/Applications`。不会复制第三方源码到
我们 MIT 仓库；Intel Mac 则自动保留原本的 Whisper/浏览器语音。

面试服务会在 Mac 本地后台启动，**让 Agent 的工具调用及时结束**，并自动
打开私有浏览器页面。重复执行不会开第二个服务：

```bash
bash AI-Interview.command --doctor          # 环境检查，不改电脑配置
bash AI-Interview.command --dry-run         # 看会安装什么，不下载
bash AI-Interview.command --launch-only     # 再次打开现有面试
bash AI-Interview.command --stop            # 使用令牌安全关闭本地服务
bash AI-Interview.command --yes --no-voicestudio # 仅轻量 Whisper
```

需要明确：**Mac 上安装和允许麦克风必须在你的 Mac 上发生**，本 ChatGPT
无法从云端打开你的麦克风。VoiceStudio 首次启动时的 macOS Gatekeeper
批准、模型许可证与模型下载设置，及浏览器麦克风权限，都仍需你完成。
本命令不会替你创建 Qwen、DeepSeek、GLM、Kimi API Key，也不会自动登录
Codex/Claude/Gemini。默认模型面试调用的是你选定的在线提供商。
详见 [一键启动与 Agent 指南](skills/ai-interview/references/one-click-mac.md)。

## 0.5.0：可选 VoiceStudio 实时语音后端

**已经加入 VoiceStudio 的协议适配代码、实时语音中继、网页切换和安装说明。** 它是一个**独立安装的第三方程序**，我们不复制它的 AGPL-3.0 源码或模型权重，因此 AI-Interview 仍然保持 MIT 代码仓库。

先从 [VoiceStudio 官方 Releases](https://github.com/debpalash/VoiceStudio/releases/latest) 下载与你操作系统匹配的安装包（核对 SHA-256），打开应用，在它的 Model Manager 内选择并安装 STT/TTS 模型。确认它的后端在本机 `127.0.0.1:3900` 运行。**Intel Mac 无法使用 VoiceStudio 打包的本地 Python 后端**，可以继续使用 AI-Interview 自带的 Faster-Whisper CPU 方案。

在本地 AI-Interview 仓库虚拟环境中执行：

```bash
python -m pip install -r skills/ai-interview/scripts/requirements-studio.txt
python -m pip install -r skills/ai-interview/scripts/requirements-voicestudio.txt
python skills/ai-interview/scripts/career.py interview --doctor --voicestudio
python skills/ai-interview/scripts/career.py interview --without-stt --voicestudio
```

在面试网页顶部点 **Check VoiceStudio → 明确勾选独立语音服务授权 → Speech Engine 选择 VoiceStudio**，就可以让 AI 用 VoiceStudio 的音频朗读问题，候选人点击录音后使用实时字幕和最后的语音汇总。系统会在你停止录音、人工核对和主动点击提交后，才把文字交给选定面试模型。录音时会停止面试官正在播放的声音；Coding 则继续用编辑器。流式模型不可用时可以回退到 VoiceStudio 批量识别；也可以继续用浏览器朗读和本地 Whisper。

**重要隐私边界：** 我们只把音频交给本机 VoiceStudio 服务；但 VoiceStudio 自身可选远程语音引擎，也可能首次使用时下载模型。你必须先检查它的设置和模型许可证，再在网页授权。与在线 LLM 处理你确认后的答案是两份独立的权限。没有经过你设备的实际语音验证，不能保证流畅度和延迟。

完整逐步操作：**[VoiceStudio 安装和使用说明](skills/ai-interview/references/voicestudio-backend.md)** · [系统架构](docs/VOICESTUDIO-INTEGRATION.md) · [本轮验证](docs/VOICESTUDIO-VERIFICATION.md)。

## 五个主要入口

| 命令 | 功能 | 重要边界 |
|---|---|---|
| `/profile` | 读取简历 PDF/文本，形成私人的、可编辑 Markdown CV 草稿；可在明确同意后让模型润色 | 未证明真实经历的内容不会自动当成事实，也不会自动提交 CV |
| `/scrape` | 提供 LinkedIn 招聘搜索链接，或读取 Greenhouse/Lever 企业公开招聘 API；可导入用户指定的 JD | **不自动爬取 LinkedIn，不登录或绕开反爬**，不控制鼠标申请 |
| `/rank` | 依据岗位、JD、简历实际内容做可解释的相关性排序 | 分数是简单启发式匹配，不是录取率或求职成功概率 |
| `/interview` | 上传 CV、选择岗位/可选 JD、语音问答、Coding 编辑器、HR 对抗、技术深挖 | 语音在本机处理；模型仍可能通过网络处理你确认的内容；代码不执行 |
| `/memory` | 保存你明确同意的历次面试覆盖情况及知识点证据，提醒哪些知识应重新验证 | **半年没练习不是“失去能力”**；没有证据必须再测，而不是直接扣分 |

`/trends` 是支持命令：从 **arXiv** 获取有发表日期和抓取日期的论文元数据、摘要，或从 **Hugging Face Daily Papers** 获取社区推荐信号。它不是简单把六个月前的新闻冒充今天的前沿，也不把热门度当科学证据。最新研究材料只在你选择允许之后进入技术面试追问；**HR/简历轮不被论文新闻打断**。

## 三类不同的“知识状态”

- **基本原理已经证明掌握**：例如 Transformer Attention 的计算机制，历史回答有足够的具体证据。
- **需要再测**：上一次给出有证据的回答距今很久，系统安排新题检查；这不是失去能力的断言。
- **领域发生新变化**：检索到了有出处、日期的新论文/技术，再针对基线、缺陷、实验、公平性追问；摘要不等于完整论文审阅。

这样 AI Researcher 的数学和架构基础与对最新 Attention/RL 论文的了解会被分开评估；Quant 会重点看统计、随机过程及金融领域相关研究；Agent Engineer 的工具协议、Harness、规划与评测变化频繁，可更短周期复练。

## 本地开始使用（Mac / Linux）

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r skills/ai-interview/scripts/requirements-studio.txt

# 建立简历资料；生成待人工检查的 Markdown CV 草稿
python skills/ai-interview/scripts/career.py profile --resume /你的私有目录/CV.pdf --role ai_researcher

# 产生 LinkedIn 搜索链接（不自动抓取 LinkedIn）
python skills/ai-interview/scripts/career.py scrape --linkedin "LLM Agent Engineer" --location London

# 企业公开招聘数据（替换为真实公司 board 名称）
python skills/ai-interview/scripts/career.py scrape --greenhouse company-slug
# 或：python skills/ai-interview/scripts/career.py scrape --lever company-slug

# 岗位排序与研究更新
python skills/ai-interview/scripts/career.py rank --role ai_researcher
python skills/ai-interview/scripts/career.py trends --role ai_researcher --source arxiv

# 语音面试网页（无 Whisper 时可先用文字输入）
python skills/ai-interview/scripts/career.py interview --without-stt
```

要使用本地麦克风转文字，请额外安装 `skills/ai-interview/scripts/requirements-voice.txt`，明确授权下载 Whisper 模型，并运行 `python skills/ai-interview/scripts/career.py interview`。浏览器逐轮朗读非 Coding 题；你按麦克风按钮回答，确认转写再提交。Coding 仍在编辑器输入。

面试设置页现在可以选取 `/scrape` 缓存的具体 JD，还可以点击 **Refresh research** 主动获取本岗位最新论文元数据；勾选允许新论文/已记录知识证据进入提问。面试结束后的 **Save private memory summary** 完全是可选操作，仅保存阶段覆盖和数量，不自动永久保存完整问答。

## 需要理解的限制

**关于 LinkedIn**：目前公开条款不允许未经授权的爬虫或机器人自动化访问。因此 `/scrape --linkedin` 只生成你自己浏览的搜索链接，真实抓取使用 Greenhouse/Lever 官方公开职位接口，或者导入你手动选好的 JD。我们不宣传它能稳定爬完整 LinkedIn。

**关于 CV**：默认草稿保留来源文字；使用 `--polish-with codex|claude|gemini|qwen|deepseek|glm|kimi --allow-model-transfer` 可选择让外部模型起草更整洁的 Markdown，但其事实必须人工审核，不能保证导出精确版式的 PDF。

**关于模型**：Codex、Claude Code、Gemini CLI 需要本地安装和登录；Qwen、DeepSeek、GLM、Kimi 需要对应 API Key。未经实机验证的接入不能宣称全部联调成功。不使用 Hermes Agent。

**关于隐私**：用户资料默认保存在 `~/.local/share/ai-interview/`，不上传 GitHub。技术论文刷新会访问公开研究服务，但不会附带用户简历。将确认文本和所选 JD 交给在线模型，需要显式同意。原始音频不会由应用主动写盘。

**关于验证**：程序提供离线自动回归测试；真实 arXiv/HF/Greenhouse/Lever 网络响应、真实麦克风、模型账号和一小时稳定性需要在你的机器上再验证。详见 [验证报告](docs/CAREER-VERIFICATION.md) 与 [Skill 调用说明](skills/ai-interview/references/career-workflow.md)。
