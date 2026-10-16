# AI Interview · 0.2.0

**维护原来的面试 Skill，并把本地麦克风转文本程序直接装进 Skill。**

[主入口](skills/ai-interview/SKILL.md) · [Codex 调用说明](skills/ai-interview/references/local-voice.md) · [本次验证](docs/VOICE-VERIFICATION.md)

## 怎么用

把完整的 `skills/ai-interview/` 文件夹安装到 `~/.agents/skills/ai-interview/`。更新时先把旧文件夹备份到 skills 目录之外，再放入新版本，避免同名重复加载。不要只复制 SKILL.md：scripts、web、references 等都必须保留。

在本地 Codex 中发送：

```text
$ai-interview 使用内置麦克风程序开始模拟面试。
先运行 doctor 检查环境；需要安装依赖和下载模型时先说明并获得许可。
获得许可后请执行 setup 和 start，打开本地录音页面。
每次把当前问题交给 ask，在 wait 中读取我确认后的回答，再继续追问。
使用中文、严格模式；不要提前给标准答案。
使用我已提供的简历，不要修改答案文件或上传 GitHub。
```

你只需在页面中点击录音、说话、停止、校对并确认。Codex 正在执行工具循环时，`wait` 会把确认文本直接返回给它，不需要逐轮复制粘贴。页面也会显示它发来的下一题，但目前不会朗读。

**这不是让网页直接控制 Codex。** 实际执行者是本地 Codex，它调用随 Skill 附带的 Python 脚本。如果 Codex 停止了工具循环，网页不会自行唤醒它；你可以在 Codex 里说“继续语音面试”，它再读取同一题的确认答案。不能保证任意宿主都持续等待一小时。

## 程序已经包含什么

- `scripts/voice.py`：doctor / setup / start / ask / wait / status / stop。
- `scripts/mic_stt.py`：本机 HTTP 服务、权限检查、录音上传和转写草稿。
- `scripts/speech_backend.py`：本地 faster-whisper 解码，不调用云端语音 API。
- `scripts/web/`：录音、校对、确认、题目显示和断连释放麦克风的页面。
- `references/local-voice.md`：给 Codex 的完整操作顺序、失败处理和隐私边界。

不需要语音 API Key；首次 `setup --allow-download` 需要联网下载依赖和模型。之后加载本地缓存。CPU 默认 int8，不支持时用 `--compute-type float32`。这不是模型准确率或设备兼容性的保证。

## 你也可以手动检查

macOS/Linux 示例；Windows 可使用对应的 `python` 和完整路径。

```bash
SKILL_DIR="$HOME/.agents/skills/ai-interview"
SESSION="$HOME/Interview-Workspace/voice-sessions/session-001"
python3 "$SKILL_DIR/scripts/voice.py" doctor
# 确认同意下载后，首次执行：
python3 "$SKILL_DIR/scripts/voice.py" setup --allow-download --model base
python3 "$SKILL_DIR/scripts/voice.py" start --session-dir "$SESSION"
python3 "$SKILL_DIR/scripts/voice.py" ask --session-dir "$SESSION" --question-id q001 --text "为什么选择这个算法？"
python3 "$SKILL_DIR/scripts/voice.py" wait --session-dir "$SESSION" --question-id q001 --after-revision 0 --timeout 20
python3 "$SKILL_DIR/scripts/voice.py" stop --session-dir "$SESSION"
```

`SESSION` 必须是新的私有目录；示例目录已使用过就换一个名字。不要把录音页的完整私有链接、connection.json 或真实回答上传到公开仓库。

## 正确理解结果

`waiting` 只代表还没确认，不是答错。`ready` 的 `answer.confirmed_text` 才是应评分的回答。每题绑定 question_id，每次修正增加 revision，避免上一题或旧版本被重复评分。未确认草稿不会交给 Codex。确认动作会保存本地的原始转写和校对文本，原始音频不由程序主动保存。

电脑麦克风需要本地浏览器授权；安装 Skill 不会自动录音。远程 Codex 云任务不能调用你家里电脑的麦克风。使用在线 Codex 时，确认文本仍可能进入模型服务，不能称整个面试完全离线。

每段最多三分钟，可以多轮录制。当前不提供语调/情绪评分、边说边字幕、自动朗读、全双工插话、精确一小时计时或安全判题平台。停止时关闭录音页可立即释放麦克风；页面也会在检测到服务断开后释放，但后台标签页轮询可能变慢。

## 验证范围

提供本地可运行测试，覆盖程序调用、HTTP、题目绑定、修订、防重复与模拟录音状态。测试中的解码器是假的，不代表已经完成真实麦克风、真实语音模型或一小时 Codex 联调。详见本次验证报告。GitHub 仅用于源码与普通验证记录，不包含 Actions/workflow。
