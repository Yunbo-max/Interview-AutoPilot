"""Interviewer-paced question check-ins are independent of grading and mic access."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/ai-interview/scripts'))

class NaturalCheckinTests(unittest.TestCase):
    def test_idle_question_exposes_a_natural_interviewer_question(self):
        from interview_timekeeper import TimekeeperAgent
        for lang in ('zh','en'):
            t = TimekeeperAgent()
            t.begin({'id':'q1','phase':'hr','kind':'voice'}, 0)
            t.observe(60, True)
            first = t.snapshot(60, True, language=lang)['reminders'][0]
            self.assertIn('checkin_prompt', first)
            self.assertEqual(first['level'], 'gentle')
            self.assertTrue(first['checkin_prompt'].endswith(('？', '?')))
            self.assertNotIn('未提交', first['checkin_prompt'])
            self.assertNotIn('wrong', first['checkin_prompt'].lower())
            t.observe(120, True)
            second = t.snapshot(120, True, language=lang)['reminders'][1]
            self.assertNotEqual(first['checkin_prompt'], second['checkin_prompt'])
            self.assertEqual(len(t.snapshot(120, True, language=lang)['reminders']), 2)

    def test_candidate_initiated_mic_observation_is_bounded_and_never_graded(self):
        from interview_timekeeper import TimekeeperAgent
        t=TimekeeperAgent()
        t.begin({'id':'q1','phase':'hr','kind':'voice'},0)
        first=t.note_local_acoustic_checkin('q1',43)
        again=t.note_local_acoustic_checkin('q1',53)
        self.assertEqual(first,again,'Only one self-reported low-activity event per question')
        self.assertIn('client_observed',first['source'])
        self.assertNotIn('audio',repr(first).lower().replace('local_audio',''))
        record=t.close(60,'unfinished')
        self.assertEqual(len(record['acoustic_checkins']),1)
        self.assertEqual(t.report()['answered_count'],0)
        with self.assertRaises(ValueError):t.note_local_acoustic_checkin('q1',61)
        t.begin({'id':'q2','phase':'coding','kind':'code'},70)
        with self.assertRaises(ValueError):t.note_local_acoustic_checkin('q2',100)

    def test_paused_question_does_not_issue_checkins_or_grade_silence(self):
        from interview_timekeeper import TimekeeperAgent
        t = TimekeeperAgent()
        t.begin({'id':'q1','phase':'hr','kind':'voice'}, 0)
        self.assertEqual(t.snapshot(1000, False)['reminders'], [])
        self.assertEqual(t.report()['answered_count'], 0)
        self.assertEqual(t.close(1000, 'unfinished')['outcome'], 'unfinished')

if __name__ == '__main__': unittest.main()
