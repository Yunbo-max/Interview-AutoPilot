'use strict';
const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
// The token remains in this page's JS memory, not localStorage/cookies/history.
history.replaceState(null, '', location.pathname);
let pageActive = true, pendingSubmission = null, answerRevision = 0;
let stream = null, recorder = null, chunks = [], blob = null, draft = null;
let tick = null, started = 0, busy = false, stopping = false, discarded = false, healthy = false;
let agentMode = false, questionId = null, recordingQuestionId = null, polling = false;
let maxSeconds = 180, maxBytes = 20 * 1024 * 1024, accumulatedBytes = 0, lastReceipt = null;

function status(text, recording=false) {
  $('status').textContent = text;
  $('status').classList.toggle('recording', recording);
}
function controls() {
  const recording = !!recorder && recorder.state !== 'inactive';
  $('start').disabled = !pageActive || !healthy || busy || stopping || recording || (agentMode && !questionId);
  $('stop').disabled = busy || !recording;
  $('cancel').disabled = busy || !recording;
  $('retry').disabled = !pageActive || !healthy || busy || stopping || recording || !blob;
  $('language').disabled = busy || recording;
  $('text').disabled = busy || recording;
  $('copy').disabled = busy || recording || !$('text').value.trim();
  $('save').disabled = !pageActive || !healthy || busy || recording || !draft || !$('text').value.trim() || (agentMode && draft.question_id !== questionId);
}
function releaseMic() {
  if (stream) stream.getTracks().forEach(track => track.stop());
  stream = null;
  clearInterval(tick); tick = null;
}
async function api(path, options={}) {
  const response = await fetch(path, {...options, headers: {'Authorization':'Bearer '+token, ...(options.headers||{})}, cache:'no-store'});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
async function transcribe() {
  if (!pageActive || !healthy || !blob || busy) return;
  busy = true; draft = null; controls();
  status('正在本机转写。麦克风已关闭；速度取决于你的电脑和模型。');
  try {
    draft = await api('/api/transcribe?language='+encodeURIComponent($('language').value), {
      method:'POST', headers:{'Content-Type':blob.type || 'application/octet-stream', ...(agentMode ? {'X-Question-ID':recordingQuestionId} : {})}, body:blob
    });
    if (!pageActive || !healthy || (agentMode && draft.question_id !== questionId)) { draft = null; blob = null; throw new Error('题目已改变，旧转写不会提交给新题。'); }
    $('text').value = draft.raw_text;
    $('raw').textContent = draft.raw_text;
    lastReceipt = null; pendingSubmission = null;
    $('receipt').textContent = '';
    status(draft.warning || '转写完成。请核对术语与数字，再复制或确认保存。');
  } catch (err) {
    status(err.message + (blob && pageActive ? ' 音频暂留在本页内存，可点“重试转写”；刷新会丢失。' : ' 已丢弃该录音，没有提交新的回答。'));
  } finally { busy = false; controls(); }
}
function endRecording(cancel=false) {
  // Cancellation must survive an inactive recorder whose final events are still queued.
  if (cancel) { discarded = true; chunks = []; blob = null; }
  if (!recorder || recorder.state === 'inactive') { releaseMic(); controls(); return; }
  stopping = true;
  recorder.stop();
  releaseMic();
  controls();
}
async function startRecording() {
  if (!pageActive || !healthy || busy || stopping || (agentMode && !questionId)) return;
  if ($('text').value.trim() && !lastReceipt && !window.confirm('开始下一段将替换当前未保存文字。继续吗？')) return;
  busy = true; controls(); status('请允许浏览器使用麦克风…');
  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder)
      throw new Error('当前环境不支持安全录音。请打开终端打印的 127.0.0.1 链接，并使用支持 MediaRecorder 的浏览器。');
    recordingQuestionId = questionId;
    stream = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true, noiseSuppression:true}, video:false});
    if (!pageActive || !healthy || (agentMode && recordingQuestionId !== questionId)) { releaseMic(); throw new Error('服务或题目已改变；麦克风已释放。'); }
    const type = ['audio/webm;codecs=opus','audio/webm','audio/ogg;codecs=opus','audio/mp4']
      .find(t => MediaRecorder.isTypeSupported(t));
    recorder = new MediaRecorder(stream, type ? {mimeType:type} : undefined);
    chunks = []; accumulatedBytes = 0; discarded = false; blob = null; draft = null;
    lastReceipt = null; pendingSubmission = null; $('receipt').textContent = ''; $('text').value = ''; $('raw').textContent = '';
    recorder.ondataavailable = event => {
      if (!event.data.size || discarded) return;
      accumulatedBytes += event.data.size;
      if (accumulatedBytes > maxBytes) {
        endRecording(true); status('录音超过大小限制，已取消；请录制更短片段。'); return;
      }
      chunks.push(event.data);
    };
    recorder.onerror = () => { stopping = true; endRecording(true); releaseMic(); status('录音设备出现错误，请检查麦克风。'); controls(); };
    recorder.onstop = async () => {
      stopping = false;
      releaseMic();
      if (discarded || !pageActive || !healthy || (agentMode && recordingQuestionId !== questionId)) {
        chunks = []; blob = null; status('录音已取消，没有转写或保存。'); controls(); return;
      }
      blob = new Blob(chunks, {type:recorder.mimeType || type || 'application/octet-stream'});
      chunks = [];
      if (!blob.size) { status('录音为空，请检查输入设备。'); controls(); return; }
      await transcribe();
    };
    recorder.start(500);
    started = performance.now();
    tick = setInterval(() => {
      const sec = Math.floor((performance.now()-started)/1000);
      $('timer').textContent = `${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')} / 03:00`;
      if (sec >= maxSeconds-1) endRecording(false); // Leave a little encoder flush margin.
    }, 200);
    status('正在录音；说完后点击“结束并转写”。', true);
  } catch(err) {
    releaseMic(); recorder = null;
    status(err.name === 'NotAllowedError' ? '麦克风权限被拒绝。请在浏览器站点权限和系统隐私设置里允许麦克风后重试。' : err.message);
  } finally { busy = false; controls(); }
}
$('start').onclick = startRecording;
$('stop').onclick = () => endRecording(false);
$('cancel').onclick = () => endRecording(true);
$('retry').onclick = transcribe;
$('text').oninput = () => { lastReceipt = null; pendingSubmission = null; controls(); };
$('copy').onclick = async () => {
  try { await navigator.clipboard.writeText($('text').value); status('文字已复制。请粘贴到 Codex，作为本轮回答。'); }
  catch { $('text').focus(); $('text').select(); status('无法自动访问剪贴板；已选中文字，请使用系统复制快捷键。'); }
};
$('save').onclick = async () => {
  if (!pageActive || !healthy || !draft || busy) return;
  busy = true; controls();
  try {
    // A retry has the same intent ID; editing creates a new, revision-checked intent.
    if (!pendingSubmission) pendingSubmission = {draft_id:draft.draft_id, text:$('text').value,
      submission_id:crypto.randomUUID(), expected_revision:answerRevision};
    lastReceipt = await api('/api/save', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify(pendingSubmission)});
    if (!pageActive || (agentMode && lastReceipt.question_id !== questionId)) return;
    answerRevision = Math.max(answerRevision, lastReceipt.revision || 0);
    $('receipt').textContent = agentMode
      ? `已确认题目 ${lastReceipt.question_id}，回答版本 ${lastReceipt.revision}。\n本地文件：${lastReceipt.text_path}\nCodex 正在执行 wait 时会收到这份答案；未在运行时，可在 Codex 中说‘继续语音面试’。`
      : `已保存：${lastReceipt.text_path}\n请让 Codex 读取此文件。`;
    blob = null; // No audio persistence. Release the retry copy after confirmation.
    status(agentMode ? '答案已确认，可由当前 Codex 会话读取。原始音频不保存。' : '确认文本已保存在本机；原始音频不保存。');
  } catch (err) { status(err.message); }
  finally { busy = false; controls(); }
};
async function refreshQuestion() {
  if (!pageActive || polling || !agentMode) return;
  polling = true;
  try {
    const data = await api('/api/question');
    if (!pageActive) return;
    if (data.stopped) throw new Error('语音服务已停止。');
    healthy = true;
    const nextId = data.question?.question_id || null;
    if (nextId !== questionId) {
      endRecording(true);
      questionId = nextId;
      answerRevision = data.answer_revision || 0; pendingSubmission = null;
      $('question').textContent = data.question?.text || '等待 Codex 的下一题…';
      $('question-id').textContent = nextId || '';
      draft = null; blob = null; lastReceipt = null;
      $('text').value = ''; $('raw').textContent = ''; $('receipt').textContent = '';
      status(nextId ? '题目已更新。准备好后点击“开始录音”。' : '等待 Codex 发送题目。');
    } else if (Number.isInteger(data.answer_revision)) {
      answerRevision = Math.max(answerRevision, data.answer_revision);
    }
  } catch (err) {
    healthy = false;
    endRecording(true);
    releaseMic();
    status('本地服务不可达，已释放麦克风。关闭本页或检查 Codex 中的语音服务状态。');
  } finally { polling = false; controls(); }
}
window.addEventListener('pagehide', () => {
  pageActive = false; healthy = false; endRecording(true);
});
(async () => {
  try {
    if (!token) throw new Error('缺少访问令牌。请打开终端打印的完整链接，而不是手动输入网页地址。');
    const data = await api('/api/health');
    if (!pageActive) return;
    maxSeconds = data.max_seconds; maxBytes = data.max_audio_bytes; healthy = true; agentMode = data.agent_mode === true;
    if (agentMode) { await refreshQuestion(); setInterval(refreshQuestion, 1000); }
    $('info').textContent = `本地模型：${data.model} · 保存目录：${data.output_dir}`;
    status(agentMode && !questionId ? '等待 Codex 发送题目；尚未打开麦克风。' : '服务已就绪。点击“开始录音”后才会打开麦克风。');
  } catch(err) { status(err.message); }
  controls();
})();
