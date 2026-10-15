# Primary-source integration notes

Checked 2026-10-15. External APIs and packaging rules can change; runtime adapters must check current documentation and record actual versions. These sources ground compatibility statements, not the effectiveness of the interview design.

| Source | Narrow fact used |
|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | A skill is a directory with SKILL.md metadata/instructions and optional references/assets; format constraints and progressive disclosure. |
| [OpenAI skill documentation](https://developers.openai.com/codex/skills/) | Codex discovery locations, explicit invocation and optional agents/openai.yaml metadata. |
| [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) | Portable root plugin.json and supported .codex-plugin/plugin.json compatibility packaging; packaging does not deploy a service. |
| [OpenAI App Server](https://developers.openai.com/codex/app-server/) | Application integration, initialization, threads, turns, approvals and streaming; recheck protocol version. |
| [OpenAI realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription) | Model/transport-specific transcription events and output capabilities; do not assume timestamps or confidence exist. |
| [OpenAI realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations) | Provider session lifecycle; the checked documentation states a 60-minute maximum, separate from the product's active clock. |
| [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) | Browser audio/video permission and secure-context requirements. |
| [MDN getDisplayMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia) | Explicit display capture selection and permission constraints. |
| [librosa pYIN](https://librosa.org/doc/latest/generated/librosa.pyin.html) | A method for voiced pitch estimation, not psychological inference. |
| [SymPy assumptions](https://docs.sympy.org/latest/guides/assumptions.html) | Symbolic results depend on assumptions; unknown is distinct from false. |

No existing third-party interview skill was copied into this package. Cross-examination policy, examples, reference tasks and data contracts are original design content. No current model ID, price, subscription entitlement, hiring statistic or employer-specific interview claim is hard-coded.
