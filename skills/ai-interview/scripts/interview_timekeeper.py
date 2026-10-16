"""Independent, deterministic timing supervisor for an active interview.

It sees only the *age of an unsubmitted question*, not microphone activity.
No model calls, recording access, scoring, autonomous answer or persistence.
"""
from __future__ import annotations

from datetime import datetime, timezone

SESSION_LIMIT = 3600
SESSION_WARNING_AT = (3300, 3540, SESSION_LIMIT)
PHASE_WINDOWS = {
    'hr': (60, 120, 300),
    'math': (120, 240, 360),
    'research': (120, 240, 360),
    'generation': (120, 240, 360),
}
DEFAULT_WINDOWS = (90, 180, 300)
CODING_WINDOWS = (300, 600, 900)
REMINDER_LEVELS = ('gentle', 'progress', 'offer_skip')
OUTCOMES = ('answered', 'skipped', 'unfinished', 'time_limit')
MAX_EXTENSIONS = 2
EXTENSION_SECONDS = 60


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _duration(seconds: int, language: str) -> str:
    if language == 'zh':
        return f'{seconds // 60}分钟' if seconds % 60 == 0 else f'{seconds}秒'
    return f'{seconds // 60} minutes' if seconds % 60 == 0 else f'{seconds} seconds'


def _question_message(level, seconds, language):
    waited = _duration(seconds, language)
    if language == 'zh':
        if level == 'gentle':
            return f'本题已用时{waited}，目前尚未提交答案。可以先说明你的思路。'
        if level == 'progress':
            return f'本题已用时{waited}，目前尚未提交答案。需要的话可以申请一分钟，或讲出已有推导。'
        return f'本题已用时{waited}，目前尚未提交答案。可以选择跳过或继续思考；不会自动判错。'
    if level == 'gentle':
        return f'{waited} on this question; no answer submitted yet. You can start with your reasoning.'
    if level == 'progress':
        return f'{waited} on this question. You can request a minute or explain your current approach.'
    return f'{waited} on this question, with no submission yet. Skip or continue thinking; this is not graded as wrong.'



def _interviewer_checkin(level, language):
    """One natural interviewer question, not an assessment or microphone claim."""
    if language == 'zh':
        return {
            'gentle': '你还在思考这道题吗？需要我重复一下问题吗？',
            'progress': '你愿意先讲讲目前想到哪一步，还是希望我澄清题意？',
            'offer_skip': '这题要继续想一会儿，还是先跳过进入下一题？',
        }[level]
    return {
        'gentle': 'Are you still thinking it through, or would it help if I repeated the question?',
        'progress': 'Would you like to talk me through your approach so far, or should I clarify the question?',
        'offer_skip': 'Would you like a little more thinking time, or should we move to the next question?',
    }[level]

def _session_message(seconds, language):
    remaining = max(0, SESSION_LIMIT-seconds)
    if language == 'zh':
        return f'面试还剩{remaining // 60}分钟。请注意时间预算。' if remaining else '60分钟面试时间已到。当前未提交答案不会判错，请结束并查看复盘。'
    return f'{remaining // 60} minutes remaining in the interview.' if remaining else 'The 60-minute interview time is up. No unsubmitted answer is graded; finish and review.'


class TimekeeperAgent:
    """Recorded local sub-agent driven solely by SessionClock active elapsed."""

    def __init__(self, target_seconds: int = SESSION_LIMIT, utc_source=_utc_now):
        self.target_seconds = target_seconds
        self.utc_source = utc_source
        self.question = None
        self.turns = []
        self.session_reminders = []
        self._session_emitted = set()

    def begin(self, question: dict, total_active_seconds: float):
        if self.question is not None:
            raise ValueError('Close the previous question before beginning another')
        base = CODING_WINDOWS if question['kind'] == 'code' else PHASE_WINDOWS.get(question['phase'], DEFAULT_WINDOWS)
        self.question = {
            'question_id': question['id'], 'phase': question['phase'], 'kind': question['kind'],
            'started_at_utc': self.utc_source(), 'started_at_active_seconds': float(total_active_seconds),
            'base_thresholds': base, 'extensions_seconds': 0, 'reminders': [],
            'acoustic_checkins': [],
        }

    def _thresholds(self, question):
        first, second, final = question['base_thresholds']
        return [first, second, final + question['extensions_seconds']]

    def observe(self, total_active_seconds: float, running: bool):
        if not running:
            return
        total_active_seconds = max(0, float(total_active_seconds))
        for sec in SESSION_WARNING_AT:
            if sec <= self.target_seconds and total_active_seconds >= sec and sec not in self._session_emitted:
                self._session_emitted.add(sec)
                self.session_reminders.append({'id':f'session:{sec}', 'at_seconds':sec, 'observed_at_utc':self.utc_source()})
        if self.question is None:
            return
        q = self.question
        elapsed = max(0, total_active_seconds - q['started_at_active_seconds'])
        for level, threshold in zip(REMINDER_LEVELS, self._thresholds(q)):
            if elapsed >= threshold and not any(e['level'] == level for e in q['reminders']):
                q['reminders'].append({'id':f'{q["question_id"]}:{level}', 'level':level,
                                       'at_seconds':threshold, 'observed_at_utc':self.utc_source()})

    def note_local_acoustic_checkin(self, question_id: str, total_active_seconds: float):
        """Store only a bounded client-supplied indicator, never audio or proof of silence."""
        q=self.question
        if q is None or q['question_id'] != question_id or q['kind']!='voice':
            raise ValueError('No matching active spoken question for microphone check-in')
        if q['acoustic_checkins']:
            return dict(q['acoustic_checkins'][0])
        event={
            'question_id':question_id,
            'at_active_seconds':int(max(float(total_active_seconds),q['started_at_active_seconds'])),
            'observed_at_utc':self.utc_source(),
            'source':'client_observed_approximate_low_microphone_activity',
            'note':'Approximate local signal, not proof of silence or an answer score.',
        }
        q['acoustic_checkins'].append(event)
        return dict(event)

    def extend(self, question_id: str):
        q = self.question
        if q is None or q['question_id'] != question_id:
            raise ValueError('Stale question ID; cannot extend another question')
        if q['extensions_seconds'] >= MAX_EXTENSIONS * EXTENSION_SECONDS:
            raise ValueError('Extra-time limit already reached for this question')
        q['extensions_seconds'] += EXTENSION_SECONDS
        return q['extensions_seconds']

    def snapshot(self, total_active_seconds: float, running: bool, language='en'):
        self.observe(total_active_seconds, running)
        q = self.question
        if q is None:
            return {'question_id':None, 'elapsed_seconds':0, 'recommended_seconds':0,
                    'thresholds_seconds':[], 'reminders':[], 'extensions_seconds':0,
                    'session_reminders':[self._session_event(e,language) for e in self.session_reminders],
                    'note':'Timing is ungraded.'}
        thresholds = self._thresholds(q)
        elapsed = max(0, int(float(total_active_seconds) - q['started_at_active_seconds']))
        return {
            'question_id': q['question_id'], 'elapsed_seconds':elapsed,
            'recommended_seconds':thresholds[-1], 'thresholds_seconds':thresholds,
            'extensions_seconds':q['extensions_seconds'],
            'reminders':[{
                **e, 'message':_question_message(e['level'],e['at_seconds'],language),
                'checkin_prompt':_interviewer_checkin(e['level'],language)
            } for e in q['reminders']],
            'session_reminders':[self._session_event(e,language) for e in self.session_reminders],
            'note':'No acoustic silence detection. Unsubmitted is not incorrect.',
        }

    @staticmethod
    def _session_event(event, language):
        return {**event, 'message':_session_message(event['at_seconds'],language)}

    def close(self, total_active_seconds: float, outcome: str):
        if outcome not in OUTCOMES:
            raise ValueError('Unrecognized timekeeper outcome')
        if self.question is None:
            return None
        self.observe(total_active_seconds, True)
        q = self.question
        record = {
            'question_id':q['question_id'], 'phase':q['phase'], 'kind':q['kind'],
            'started_at_utc':q['started_at_utc'], 'ended_at_utc':self.utc_source(),
            'active_seconds':max(0,int(float(total_active_seconds)-q['started_at_active_seconds'])),
            'extensions_seconds':q['extensions_seconds'], 'reminders':list(q['reminders']),
            'acoustic_checkins':list(q['acoustic_checkins']),
            'outcome':outcome,
        }
        self.turns.append(record)
        self.question = None
        return record.copy()

    def report(self):
        answered=[item['active_seconds'] for item in self.turns if item['outcome']=='answered']
        return {
            'turns':[dict(entry) for entry in self.turns],
            'session_reminders':list(self.session_reminders),
            'answered_count':len(answered),
            'skipped_count':sum(x['outcome']=='skipped' for x in self.turns),
            'unanswered_count':sum(x['outcome'] in ('unfinished','time_limit') for x in self.turns),
            'mean_answer_seconds':round(sum(answered)/len(answered),1) if answered else None,
            'note':'Active duration excludes explicit pause and model waits. Response time is not a competence score.',
        }
