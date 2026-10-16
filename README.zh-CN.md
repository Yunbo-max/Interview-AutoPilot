<div align="center">
  <img src="docs/assets/hero.svg" alt="AI Interview：不仅要懂，更要能为你的推理和研究辩护。" width="100%" />

  <p><strong>以语音为主的技术面试 · 简历与科研对抗追问 · 有来源的最新知识挑战</strong></p>
  <p>
    <a href="#一键开始">一键开始</a> ·
    <a href="#我们与其他项目有什么区别">项目对比</a> ·
    <a href="#实际面试体验">体验流程</a> ·
    <a href="README.md">English</a>
  </p>
  <p>
    <img alt="Version 0.7.0" src="https://img.shields.io/badge/version-0.7.0-234f3d?style=flat-square" />
    <img alt="MIT license" src="https://img.shields.io/badge/license-MIT-234f3d?style=flat-square" />
    <img alt="Mac one-click setup" src="https://img.shields.io/badge/Mac-one--click_setup-a7d79f?style=flat-square" />
    <img alt="Local-first voice" src="https://img.shields.io/badge/voice-local--first-a7d79f?style=flat-square" />
  </p>
</div>

**我们不想再造一个背题工具。** AI-Interview 从你的真实简历出发，让你解释项目贡献、方法局限、实验是否公平；再根据岗位考察 Transformer、RL、Quant、Agent、Diffusion 等基础与前沿。它是**真实面试之前的练习工具**，不是面试作弊助手，也不自动投递简历。

## 一键开始

在支持的 **MacBook Pro / Apple Silicon** 上，既可以让本地 Codex、Claude Code、Gemini CLI 运行安装命令，也可以通过 Finder 双击 `AI-Interview.command`：

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
bash AI-Interview.command --yes
```

第一次运行会准备独立 Python 环境与依赖，下载本地 Whisper 备用模型；M 系列 Mac 可以下载并校验**独立安装的 VoiceStudio 官方 DMG**，然后启动本机面试网页。**但 Mac 麦克风权限、第三方模型许可证、系统安全确认仍由你本人批准。** 作为面试官的 Codex/Claude/Gemini 需提前登录，其他模型需要对应 API Key。

<details>
<summary><strong>更多选项：检查环境、轻量模式、停止面试服务</strong></summary>

```bash
bash AI-Interview.command --doctor              # 只读检查
bash AI-Interview.command --dry-run             # 预览安装操作
bash AI-Interview.command --launch-only         # 重新打开已有面试会话
bash AI-Interview.command --stop                # 通过本机令牌停止服务
bash AI-Interview.command --no-voicestudio --yes  # 不安装 VoiceStudio
```

VoiceStudio 官方打包的本地后端要求 **Apple Silicon + macOS 13.3+**；Intel Mac 可使用独立的 Faster-Whisper 和浏览器朗读方案。VoiceStudio 官方建议约 **10 GB 磁盘空间**用于基础应用及运行环境，额外模型可能需要更多。真实 Mac 安装过程与语音速度仍须实机验证。

[Mac / Agent 一键安装指南](skills/ai-interview/references/one-click-mac.md) · [VoiceStudio 使用说明](skills/ai-interview/references/voicestudio-backend.md)

</details>

## 实际面试体验

<div align="center">
  <img src="docs/assets/studio-preview.svg" alt="面试网页示意：上传 PDF 简历、选择目标岗位与语音引擎。" width="100%" />
  <sub>根据当前网页界面绘制的示意图；不是现场录屏、真实候选人数据或模型效果展示。</sub>
</div>

| 面试前 | 面试中 | 面试结束 |
| :--- | :--- | :--- |
| 上传**可提取文字的 PDF 简历**，核对内容；选择六类岗位之一，可选岗位 JD 与近期研究论文。 | **AI 用声音问**，你用麦克风答；核对最终转写再提交。Coding 题自动切换代码编辑器。 | 查看**模型生成的复盘与参考解**、导出报告，按需保存一份精简的私人 Memory。 |

语音是主要交互形式，但也支持文字输入。可选 VoiceStudio 实时字幕只是预览；**只有你确认并点击提交的文字才会交给面试官模型。** 当前为**逐轮对话**，不是真正全双工通话；代码编辑器**不执行提交的代码**。

### Timekeeper Agent：会控场、但不乱扣分的计时监督器

新增了**独立的本地确定性 Timekeeper**：面试官模型继续负责出题和追问，计时监督器只负责每道题的时长、分级提醒、暂停/跳过、总时间预算和可导出的时间记录。**它不额外调用 LLM，也不监听声音判断你是否“沉默”**；没有提交，不代表答错。只有录音结束、没有正在播放/录制语音时才可能朗读简短提醒；Coding 题只做视觉提醒。

| 题型 | 第一次提示 | 第二次提示 | 建议考虑跳过 |
| :--- | ---: | ---: | ---: |
| **HR / 简历** | **1 分钟** | **2 分钟** | **5 分钟** |
| Transformer / RL / Agent / ML / 系统 / Quant | 1 分 30 秒 | 3 分钟 | 5 分钟 |
| **数学 / 科研 / 生成模型** | 2 分钟 | 4 分钟 | 6 分钟 |
| **Coding** | 5 分钟 | 10 分钟 | 15 分钟 |

你可以自己点击 **+1 minute**（每题最多两次，只延长该题*建议*时限）、**Skip question**（明确跳过、不评分），或者 **Pause** 暂停计时。面试总限额仍是 **60 分钟有效时间**，剩余五分钟、一分钟时提醒；等待面试官 LLM 和已经绑定题目的 Whisper/VoiceStudio **转写处理**不会计入答题时间。面试结束的 JSON 报告里会有每题真实有效用时。**关闭浏览器不等于自动暂停**，离开之前请点击 Pause。[具体时间规则](skills/ai-interview/references/timekeeper-agent.md)。

### 六类岗位

| Quant / 工程 | AI / 研究 |
| :--- | :--- |
| **Quant Researcher**：概率、统计、随机过程、Python、研究方法 | **AI Researcher**：Attention、模型架构、RL、实验设计、消融 |
| **Quant Developer**：算法、数据结构、复杂度、并发与性能 | **LLM / Agent Engineer**：Coding、Transformer、MCP、工具调用、Planning、评估 |
| **ML Engineer**：ML 基础、训练、部署、系统设计 | **Generative AI Researcher**：Diffusion、Score/Flow Matching、多模态与研究方法 |

所有岗位都从 **HR + 简历真实性与个人贡献深挖**开始。技术题与追问根据岗位、JD、回答不断调整。60 分钟是目标流程，并非已经通过一小时真实语音压力测试。

## 从准备到持续复练

<div align="center"><img src="docs/assets/workflow.svg" alt="Profile、Scrape、Rank、Interview、Memory 五阶段学习闭环；Trends 用于可选研究更新。" width="100%" /></div>

| 命令 | 实际行为 |
| :--- | :--- |
| **`/profile`** | 本地读取 PDF 简历，生成保留来源的可编辑 Markdown 草稿；需明确同意才交给模型润色。 |
| **`/scrape`** | 生成 LinkedIn **职位搜索链接**、读取公开 Greenhouse/Lever 企业招聘接口，或导入 JD。**不非法爬取 LinkedIn。** |
| **`/rank`** | 基于简历与 JD 展示可解释的岗位匹配和能力缺口；**不是录取概率**。 |
| **`/interview`** | 按岗位进行语音面试、简历反驳、技术追问与可选 Coding。 |
| **`/memory`** | 经你主动确认后记录覆盖阶段和知识证据，供后续复练；默认不存完整对话。 |
| **`/trends`（辅助）** | 可选检索有日期的 arXiv / Hugging Face Daily Papers 摘要，为技术面试提供前沿追问线索。**摘要不等于论文实验验证。** |

**很久没有测试 ≠ 忘记知识。** Memory 区分“已有证据证明掌握”“需要再次检验”和“领域出现新技术”。最新论文使用明确的发表与抓取日期；热度不能代替科学证据。

## 我们与其他项目有什么区别

**语音面试不是我们独创的。** 真正的差异是：围绕 Quant、LLM、Agent、生成模型和 AI Research 的**项目/科研对抗**，加入**有来源和日期的近期研究问题**，再与候选人控制的能力复练记录联系起来。

| 对比 | **AI-Interview（我们）** | [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) | [DeepInterview](https://github.com/ngoanpv/DeepInterview) | [VoiceStudio](https://github.com/debpalash/VoiceStudio) |
| :--- | :--- | :--- | :--- | :--- |
| **主要定位** | 技术与科研面试训练 | 求职、简历和申请管理 | 实时语音模拟面试与复盘 | 语音生成及识别工具 |
| **面试方式** | **逐轮语音**、简历技术反驳、计时提醒与动态追问 | 按实际申请准备，聊天式模拟 | **实时语音**，其直播链路支持插话 | 提供语音 API，**不负责面试** |
| **专业方向** | **Quant / ML / Attention / RL / Agent / Diffusion** | 按职位和申请阶段定制 | CV/JD 驱动的自适应问答与题库 | ASR/TTS 模型及声音管理 |
| **最新知识** | 可选**有日期的 arXiv/HF 摘要追问** | 公司、岗位信息研究 | 公司研究与学习辅导 | 非面试科研产品 |
| **长期记录** | 可选知识证据与覆盖记录，不预设能力退化 | 投递、反馈、结果档案 | 面试评分与学习教练 | 声音与音频项目历史 |
| **现有局限** | 无代码执行、全双工和真实 Mac 长测认证 | 不是独立的实时语音面试应用 | 实时直播链路依赖更多组件/配置 | 需单独安装，AGPL 与模型许可独立 |

<sub>基于截至 2026-10-16 的公开项目说明进行**功能定位对比**，不是 GitHub Trending 排名、真实性能测试，也不表示其他项目绝对不支持某项未列功能。DeepInterview 的实时语音链路比我们当前的逐轮方案更成熟。</sub>

## AI 的“大脑”和“声音”可以分别选择

| 层次 | 可选方案 | 要点 |
| :--- | :--- | :--- |
| **面试官（推理）** | Codex CLI、Claude Code CLI、Gemini CLI、Qwen、DeepSeek、GLM、Kimi | CLI 需要本地登录；API 需要 Key。七种适配已编写，**尚未全部实机验证**。 |
| **默认语音** | 浏览器 SpeechSynthesis + 本地 Faster-Whisper | 不必安装 VoiceStudio；下载 Whisper 模型后可以在本机转写。 |
| **可选语音** | [VoiceStudio](https://github.com/debpalash/VoiceStudio) | 独立本地软件，支持 TTS 和实时/批量 STT。**是否完全本地取决于它选择的引擎**，许可条件另算。 |

### 隐私和真实性说明

- **用户简历、录音、未提交的回答不会上传公开 GitHub。** PDF 本地解析，程序不主动持久保存录音；私人工作目录默认为 `~/.local/share/ai-interview/`。
- **面试不一定完全离线。** 在你授权后，选择的 LLM 可能收到简历、JD 和确认回答；VoiceStudio 若选了远程引擎，也可能发送音频到外部服务。
- **不会自动投递或辅助真实面试作弊。** 不登录 LinkedIn、不控制鼠标、不直接运行候选人代码，也不凭声音推断人格、情绪或能力。
- **测试与实机效果要分开。** v0.7.0 的计时监督器、HTTP 与语音交互已完成 **177 项 Python 测试及六组网页模拟测试**；[见具体结果](docs/TIMEKEEPER-VERIFICATION.md)；真实 Mac、麦克风效果、不同模型账号以及完整一小时语音面试**尚未全部认证**。

[一键安装验证](docs/ONE-CLICK-MAC-VERIFICATION.md) · [VoiceStudio 桥接验证](docs/VOICESTUDIO-VERIFICATION.md) · [求职流程验证](docs/CAREER-VERIFICATION.md) · [研究来源规范](docs/SOURCES.md)

---

<div align="center">
  <strong>Defend your work. Explain the fundamentals. Keep up with what changed.</strong>
  <br />
  <sub>Open source · MIT · Local-first · 真正的面试之前，先把每个主张讲清楚。</sub>
  <br />
  <a href="README.md">English</a> · <a href="skills/ai-interview/SKILL.md">Skill 说明</a>
</div>
