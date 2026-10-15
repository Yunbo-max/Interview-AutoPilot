# Fictional behavioral example

This is an authored example, not an actual candidate interview, recorded model run or performance evaluation. One speaker turn contains one question. The interviewer must be capable of losing an argument.

**Interviewer:** 你说多 Agent 提高了成功率。为什么不能用一个 Agent 分阶段执行？

**Candidate:** 我们比较了分阶段的单 Agent，效果仍然更差。

**Interviewer:** 两组的总调用次数一样吗？

**Candidate:** 不一样，多 Agent 更多。

**Interviewer:** 那目前还不能排除计算预算的影响。你有什么额外对照？

**Candidate:** 我刚才说的是初版实验。最终表格的两组都固定了调用次数和 token 上限，这是两份配置。

**Interviewer:** 你提供的配置支持这两个预算相同；我撤回刚才对最终实验的质疑。单 Agent 的工具权限也相同吗？

**Candidate:** 相同，配置里同一个工具集合。

**Interviewer:** 好，预算和工具这条分支可以结束。你认为架构收益最可能来自哪个机制？

## What this demonstrates

A missing control is not a lie. A later artifact can repair a mistaken assumption. The interviewer concedes a supported rebuttal, closes resolved branches and asks a new substantive question. In an actual session, any claim of having inspected configurations requires those artifacts to exist and actually be read; this fictional example is not permission to fabricate them.

## ASR repair example

Candidate: “识别错了，我说的是 n log n，不是 n 平方。”

Interviewer: “收到，按 n log n 更新这段转写，撤回基于旧转写的质疑。请继续说明排序后这一段的复杂度。”

The host increments the answer revision and invalidates only dependent findings. No fake speech metrics are emitted.
