"""Local-only speech decoding. Imports are lazy so HTTP tests need no model."""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

MAX_SECONDS = 180
SAMPLE_RATE = 16_000


def offline_environment() -> None:
    # Network/model download is permitted only by the explicit `download` command.
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'


def decode_audio_limited(blob: bytes, max_seconds: int = MAX_SECONDS):
    """Decode incrementally, refusing excessive duration rather than truncating."""
    import av
    import numpy as np
    chunks = []
    samples = 0
    resampler = av.AudioResampler(format='s16', layout='mono', rate=SAMPLE_RATE)
    with av.open(io.BytesIO(blob), mode='r') as container:
        if not container.streams.audio:
            raise ValueError('文件没有音轨。请重新录音。')
        def collect(frames):
            nonlocal samples
            for frame in frames:
                chunk = frame.to_ndarray().reshape(-1)
                samples += len(chunk)
                if samples > SAMPLE_RATE * max_seconds:
                    raise ValueError(f'录音超过 {max_seconds} 秒，请分段录制。')
                chunks.append(chunk)
        for frame in container.decode(audio=0):
            collect(resampler.resample(frame))
        collect(resampler.resample(None))
    if not chunks:
        raise ValueError('音频为空。请检查麦克风并重新录音。')
    return np.concatenate(chunks).astype(np.float32) / 32768.0


class LocalWhisper:
    def __init__(self, model: str = 'base', threads: int = 4, compute_type: str = 'int8'):
        offline_environment()
        from faster_whisper import WhisperModel
        self.model_name = model
        self.model = WhisperModel(
            model, device='cpu', compute_type=compute_type,
            cpu_threads=threads, num_workers=1, local_files_only=True,
        )

    def transcribe(self, blob: bytes, language: str | None = None) -> dict[str, Any]:
        import numpy as np
        audio = decode_audio_limited(blob)
        duration = len(audio) / SAMPLE_RATE
        # Exact/near digital silence: never ask a decoder to invent content.
        if float(np.max(np.abs(audio))) < 1e-5:
            return {'raw_text':'', 'language':language or 'unknown',
                    'duration_seconds':duration, 'segments':[],
                    'warning':'未检测到有效音频；请检查输入设备。'}
        segments, info = self.model.transcribe(
            audio, language=language, task='transcribe',
            beam_size=5, vad_filter=True, condition_on_previous_text=False,
            word_timestamps=False,
        )
        result = [{'start':float(s.start), 'end':float(s.end), 'text':s.text}
                  for s in segments]  # Consume the generator: this runs inference.
        text = ''.join(s['text'] for s in result).strip()
        return {'raw_text':text, 'language':info.language,
                'duration_seconds':duration, 'segments':result,
                'warning':'' if text else '没有识别到语音。请检查麦克风或重新录音。'}


def download(model: str) -> str:
    """Explicit network operation: model files only, no user recordings."""
    os.environ.pop('HF_HUB_OFFLINE', None)
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    from faster_whisper.utils import download_model
    return download_model(model)
