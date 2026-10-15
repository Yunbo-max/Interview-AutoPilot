# Speech feedback without unsupported inference

## Separate four layers

1. Signal quality: clipping, missing audio, noise, speaker overlap and uncertain alignment.
2. Acoustic observations: speaking pace, articulation rate, pauses, pitch and relative energy.
3. Linguistic observations: fillers, repetition, repairs, answer structure and relevance.
4. Technical claims: checked under coding, mathematics or research rules, never inferred from the voice.

Report quality limitations first. Do not grade an inaudible or misattributed segment. Only assess the candidate channel; exclude interviewer TTS, media playback and other people.

## Metric definitions

Use the same counting convention within a comparison. For English, words per minute = 60 * word count / answer-span seconds, including within-answer pauses. Articulation rate uses voiced-speaking seconds as the denominator and must be labelled separately. For Chinese, report Han characters per minute with punctuation excluded. In mixed language, report separate counts and spans or mark rate incomparable; an LLM token count is not a word count.

Pause statistics come from aligned audio/VAD intervals. State the pause threshold and exclude time spent reading a new question or actively coding. Filler rates require verbatim-compatible transcription; a cleaned transcript cannot establish that no fillers occurred. Pitch statistics use valid voiced frames; pitch-extraction failures and octave errors must be screened. Relative amplitude changes are not calibrated physical loudness or universal confidence scores.

Prefer within-person comparisons between comparable answer types. Do not label a universal speed 'too fast'. A short volunteered baseline can be collected before the clock starts. Without a baseline, report measurements and uncertainty rather than an abnormality score.

## Output form

For each observation: audio source/segment, exact time interval if available, measurement and units, method/version, quality limitations, a cautious interpretation and one actionable practice change. Example wording: 'In this answer your pace rose relative to your earlier explanation; replay this interval and try pausing after the conclusion.' Numeric values require actual measurements. This example does not authorize inventing a value or timestamp.

Speech-only feedback stays outside technical scoring. Do not infer anxiety, confidence as a mental state, deception, employability, personality or health. Accent, pitch range and disfluency are not competence proxies. Candidate-requested articulation exercises are coaching, not standardized judgments.

## Missing or uncertain evidence

No audio: set `audio_available=false`, emit no acoustic metrics and assess only text organization. No word alignment: do not invent word-level timestamps. Unknown ASR confidence: mark unknown, not 0.99. Consequential numbers, negations, complexity orders and symbols must be clarified before content penalties. A transcript correction invalidates affected findings without rewriting unrelated evidence.

The [speech example](../assets/speech.example.json) intentionally demonstrates the no-audio case. Actual collection, acoustic extraction and playback require a host adapter and have not been implemented by this design package.
