# AI Interview 0.3.0 · 语音主导的多岗位模拟面试

**先上传 PDF 简历，再选岗位和模型，然后开启 60 分钟目标的真实对抗式面试。** 非 Coding 题由浏览器语音朗读，你对着麦克风回答（本机 Whisper 转文字、校对后才提交）；Coding 题提供网页编辑器，提交代码文本但不执行不受信任的程序。数学题可以语音解释，也可用文本补充公式。严格面试结束后查看模型生成的复盘和参考解；数学/代码尚无独立自动判题认证。

## 运行方式（macOS / Linux）

```bash
git clone https://github.com/Yunbo-max/AI-Interview.git
cd AI-Interview
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r skills/ai-interview/scripts/requirements-studio.txt
python skills/ai-interview/scripts/interview_studio.py doctor
# 只想试上传 PDF、角色和文字输入，可不安装语音：
python skills/ai-interview/scripts/interview_studio.py serve --without-stt
```

启用真正的本地麦克风转写（需主动允许依赖/模型下载）：

```bash
python -m pip install -r skills/ai-interview/scripts/requirements-voice.txt
python skills/ai-interview/scripts/interview_studio.py download-model --allow-download --model base
python skills/ai-interview/scripts/interview_studio.py serve --model base
```

浏览器打开终端打印的**完整私有 127.0.0.1 链接**。录音只在你点击 Record 且同意浏览器麦克风授权后开始；浏览器的 `speechSynthesis` 朗读题目，可以 Replay / Mute，也可以在不支持声音时查看文字。不会自动录屏或开启摄像头。原始 PDF 和音频不由本程序写盘；报告只有你点击导出才下载。模型仍可能通过网络处理 CV/文字，开始前需明确同意。

## 六种岗位

| 岗位 | 主要覆盖 |
|---|---|
| Quant Research / Trader | HR/简历 15m + 概率统计随机过程 20m + Python 15m + 策略回测 10m |
| Quant Developer | HR 15m + LeetCode 20m + 系统性能 15m + 金融基础 10m |
| ML Engineer | HR 15m + Coding 15m + ML/实验 20m + MLOps 10m |
| AI Researcher | HR/论文 15m + Transformer 15m + RL/生成模型 15m + 科研实验设计 15m |
| LLM / Agent Engineer | HR 15m + Coding 15m + Transformer 10m + Agent Harness/Memory/MCP 20m |
| Generative AI Researcher | HR/论文 15m + 数学 10m + Diffusion/Flow/DiT 25m + 科研设计 10m |

时间是目标阶段安排；真实本地计时只在服务运行期间有效，明确暂停和模型响应等待不计入。若进程退出，当前仅内存的会话不会自动恢复。

## 七种模型/宿主

**本地 CLI Host：** Codex（`codex exec`）、Claude Code（`claude --print`）、Gemini CLI（`gemini --prompt`），须自己先安装并登录。**模型 API：** Qwen（`DASHSCOPE_API_KEY`）、DeepSeek（`DEEPSEEK_API_KEY`）、GLM（`ZAI_API_KEY`）、Kimi（`MOONSHOT_API_KEY`）。API Key 设置在启动程序的终端环境中，不放在网页里；服务地址固定，不允许用户任意指定 URL。不同服务需要自己开通额度或订阅，不是同一张 ChatGPT 订阅自动覆盖。

> Codex、Claude Code、Gemini 可把整个 `skills/ai-interview/` 作为标准 Skill 安装，或者仅使用这个独立网页（无需 CLI 自动安装 Skill）。Codex/Gemini 用户可放 `~/.agents/skills/ai-interview/`，Claude Code 可放 `~/.claude/skills/ai-interview/`；不要只复制 SKILL.md，随包脚本和静态网页缺一不可。

这个版本**没有 Hermes Agent**。同一个被选中的模型负责全程动态追问，依据你最新回答挑战，而不是机械题库。

## 如何理解验证范围

自动测试验证了课程总时长、简历上传、会话状态、各种模型协议请求形状、服务器鉴权、语音网页/编辑器模拟流程及旧版语音桥接回归。无法在当前环境验证你的真实麦克风、真实 Whisper 推理、七家已登录账号、浏览器 TTS 发声质量或连续交互一小时。不要把模型生成的参考答案视为经过代码沙箱/数学证明器认证。

[英文 README](README.md) · [Skill 入口](skills/ai-interview/SKILL.md) · [Studio 运行说明](skills/ai-interview/references/voice-first-studio.md)
