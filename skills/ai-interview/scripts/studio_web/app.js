'use strict';
const el = id => document.getElementById(id);
const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
history.replaceState(null, '', location.pathname);
const context = {question:null, role:null, provider:null, muted:false, busy:false, voiceReady:false,
  stream:null, recorder:null, chunks:[], started:0, timer:null, cancel:false, recordingQuestion:null,
  pendingId:null, pendingText:null, session:null, lastSpoken:null};
const MAX_CLIP_MS = 178000, MAX_AUDIO_BYTES = 20*1024*1024;

function notice(message) { el('notice').textContent = message || ''; }
function show(screen) {
  ['setup','session','review'].forEach(name=>el(name).hidden=name!==screen);
}
async function api(path, method='GET', body=null, contentType=null) {
  const headers={'Authorization':'Bearer '+token};
  if(contentType) headers['Content-Type']=contentType;
  const response=await fetch(path,{method,headers,body,cache:'no-store',redirect:'error'});
  const data=await response.json();
  if(!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
function jsonPost(path,data){return api(path,'POST',JSON.stringify(data),'application/json');}
function setBusy(v){context.busy=v;
  el('begin').disabled=v||!el('consent').checked||!el('resume').dataset.loaded||!el('provider').value;
  el('submit').disabled=v;
  el('record').disabled=v||!context.voiceReady||!context.question||context.question.kind==='code';
  el('pause').disabled=v;el('finish').disabled=v;
}
function phasePills(role) {
  const container=el('role-phases');container.replaceChildren();
  const chosen=context.roles.find(r=>r.id===role);
  for(const p of chosen?.phases||[]){const span=document.createElement('span');span.textContent=`${p.label} · ${p.minutes}m`;container.appendChild(span);}
}
function setProviderInfo(){
  const p=context.providers.find(p=>p.id===el('provider').value);
  el('provider-note').textContent=p?.configured ? 'Ready in this environment; provider may still require login or network access.' : `Not configured: ${p?.requires||'select another provider'}`;
  context.provider=p?.id||null;
  setBusy(context.busy);
}
async function init(){
  if(!token){notice('Missing local access token. Open the complete private URL printed in your terminal.');return;}
  try{
    const [meta,health,state,jobs]=await Promise.all([api('/api/providers'),api('/api/health'),api('/api/state'),api('/api/jobs')]);
    context.roles=meta.roles;context.providers=meta.providers;context.voiceReady=health.speech_ready;
    el('role').replaceChildren(...meta.roles.map(r=>new Option(r.label,r.id)));
    el('provider').replaceChildren(...meta.providers.map(p=>new Option(`${p.id.toUpperCase()} ${p.configured?'✓':'· setup needed'}`,p.id)));
    el('job-target').replaceChildren(new Option('General role interview (no selected JD)',''),
      ...(jobs?.jobs||[]).map(j=>new Option(`${j.company} — ${j.title}`,j.id)));
    el('job-note').textContent=(jobs?.jobs||[]).length
      ? `${jobs.jobs.length} imported job(s) available. Select one to ground the HR and technical questions.`
      : 'No imported JDs yet. Use /scrape to add one, or continue with a general interview.';
    const first=meta.providers.find(p=>p.configured);if(first)el('provider').value=first.id;
    context.role=el('role').value;phasePills(context.role);setProviderInfo();
    await refreshEvidence();
    if(!context.voiceReady){el('voice-info').textContent='Local Whisper is unavailable. Type your response below, or install model weights and restart.';notice('Local speech recognition not loaded. Text mode remains available.');}
    if(state.status!=='setup'){
      context.session=state;context.role=state.role;context.provider=state.provider;
      if(state.status==='completed')renderReview(state.review || state);
      else {show('session'); if(state.question)renderQuestion(state.question);updateClock(state);}
    }
  }catch(e){notice('Unable to reach local interview service: '+e.message);}
}
async function refreshEvidence(){
  if(!el('role').value)return;
  try {
    const result=await api('/api/evidence-summary?role='+encodeURIComponent(el('role').value));
    el('evidence-note').textContent=`Cached for this role: ${result.recent_papers} recent source items, ${result.memory_topics} evidence topics. Nothing is fetched automatically. Older material is excluded from current-research questions.`;
  } catch(e) {
    el('evidence-note').textContent='Could not inspect the local research cache. Current-paper claims will not be assumed.';
  }
}
el('role').addEventListener('change',()=>{context.role=el('role').value;phasePills(context.role);refreshEvidence();});
el('refresh-research').addEventListener('click',async()=>{
  if(context.busy)return;
  setBusy(true);notice('Retrieving dated paper metadata from the selected public research source…');
  try {
    const result=await jsonPost('/api/trends-refresh', {role:el('role').value,source:el('trend-source').value||'arxiv'});
    await refreshEvidence();
    el('include-trends').checked=true;
    notice(`${result.count} research records fetched. The latest papers will be considered in technical rounds; the model has NOT read the full papers.`);
  } catch(e){notice('Research refresh failed: '+e.message+'. No new paper claims will be invented.');}
  finally{setBusy(false);}
});
el('provider').addEventListener('change',setProviderInfo);
el('consent').addEventListener('change',()=>setBusy(context.busy));
el('mute').addEventListener('change',()=>{context.muted=el('mute').checked;if(context.muted && 'speechSynthesis'in window)window.speechSynthesis.cancel();});
el('resume').addEventListener('change',async()=>{
  const file=el('resume').files?.[0];
  if(!file)return;
  el('resume').dataset.loaded='';setBusy(true);
  try{
    if(file.size>8*1024*1024||file.size===0||!file.name.toLowerCase().endsWith('.pdf'))throw new Error('Select a searchable PDF below 8 MiB.');
    const result=await api('/api/resume','POST',await file.arrayBuffer(),'application/pdf');
    el('upload-label').textContent=`${file.name} · ${result.characters} characters extracted`;
    el('resume-preview').textContent=result.preview;
    el('preview-block').open=true;
    el('resume').dataset.loaded='yes';notice('Resume parsed locally. Select a role and model to continue.');
  }catch(e){el('resume').dataset.loaded='';notice(e.message);}
  finally{setBusy(false);}
});
el('begin').addEventListener('click',async()=>{
  if(context.busy)return;
  setBusy(true);notice('Preparing your interviewer…');
  try{
    const question=await jsonPost('/api/start',{role:el('role').value,provider:el('provider').value,
      consent:el('consent').checked,focus:el('focus').value,language:el('language').value,
      use_trends:el('include-trends').checked,use_memory:el('include-memory').checked,
      job_id:el('job-target').value||null});
    context.role=el('role').value;context.provider=el('provider').value;
    show('session');renderQuestion(question);notice('Strict interview started. Use your microphone or the text fallback.');
  }catch(e){notice(e.message);}
  finally{setBusy(false);}
});
function speak(question){
  if(context.muted || question?.kind==='code')return;
  if(!('speechSynthesis'in window)){notice('Speech output is unavailable in this browser. Read the on-screen question.');return;}
  window.speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(question.question);
  utterance.lang=/[\u3400-\u9fff]/.test(question.question)?'zh-CN':'en-GB';
  utterance.rate=.94; utterance.pitch=1;
  utterance.onerror=()=>notice('Voice playback was blocked. Click “Play question” or read the text.');
  window.speechSynthesis.speak(utterance);context.lastSpoken=question.id;
}
function renderQuestion(q){
  if(context.recorder&&context.recorder.state!=='inactive')stopRecording(true);
  context.question=q;
  context.pendingId=null;context.pendingText=null;
  el('role-label').textContent=context.roles?.find(r=>r.id===context.role)?.label?.toUpperCase()||context.role;
  el('phase-label').textContent=q.phase_label?.toUpperCase()||q.phase?.toUpperCase();
  el('question-id').textContent=q.id;
  el('question-text').textContent=q.question;
  el('question-mode').textContent=q.kind==='code'?'CODE EDITOR':'SPOKEN ANSWER';
  el('voice-panel').hidden=q.kind==='code';el('code-panel').hidden=q.kind!=='code';
  el('transcript').value='';el('code').value='';
  el('submit-hint').textContent=q.kind==='code'?'Submit code; the service will not run it.':'Confirm transcript and submit. Only submitted text reaches the model.';
  el('session-summary').textContent=`Current: ${q.phase_label}. One challenge per answer; no answer key before review.`;
  el('record-state').textContent='Click to record';el('record-time').textContent='Up to 03:00 per clip';
  el('record-flag').textContent='READY';
  speak(q);
  setBusy(context.busy);
}
el('replay').onclick=()=>{if(context.question)speak(context.question);};
function release(){
  if(context.stream){context.stream.getTracks().forEach(t=>t.stop());context.stream=null;}
  if(context.timer){clearInterval(context.timer);context.timer=null;}
  el('record').classList.remove('recording');el('record-flag').textContent='READY';el('cancel-record').disabled=true;
}
function stopRecording(cancel=false){
  context.cancel=cancel;
  if(context.recorder&&context.recorder.state!=='inactive')context.recorder.stop();
  release();
}
async function recordPressed(){
  if(context.recorder&&context.recorder.state==='recording'){stopRecording(false);return;}
  if(context.busy||!context.question||context.question.kind!=='voice')return;
  if(el('transcript').value.trim()&&!confirm('Starting a new recording will replace your unsubmitted draft. Continue?'))return;
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){notice('Microphone API unavailable. Type your answer instead.');return;}
  if('speechSynthesis'in window)window.speechSynthesis.cancel();
  try{
    const id=context.question.id;
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    if(!context.question||context.question.id!==id){stream.getTracks().forEach(t=>t.stop());return;}
    context.stream=stream;context.recordingQuestion=id;context.cancel=false;context.chunks=[];
    const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(x=>MediaRecorder.isTypeSupported(x));
    const recorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined);context.recorder=recorder;
    recorder.ondataavailable=e=>{if(!context.cancel&&e.data?.size)context.chunks.push(e.data);};
    recorder.onstop=async()=>{
      const canceled=context.cancel||context.question?.id!==id;
      release();
      if(canceled){context.chunks=[];notice('Recording discarded.');return;}
      const audio=new Blob(context.chunks,{type:recorder.mimeType||'application/octet-stream'});context.chunks=[];
      if(audio.size>MAX_AUDIO_BYTES){notice('Clip exceeds 20 MiB; please record a shorter answer.');return;}
      setBusy(true);el('record-state').textContent='Transcribing locally…';
      try{
        const result=await api('/api/transcribe','POST',audio,audio.type);
        if(context.question?.id===id){el('transcript').value=result.raw_text||'';notice('Review names, numbers and negation before submitting.');}
      }catch(e){notice(e.message+' Your original answer has not been submitted.');}
      finally{setBusy(false);el('record-state').textContent='Click to record';}
    };
    recorder.onerror=()=>{stopRecording(true);notice('Microphone recording failed. Try typing instead.');};
    recorder.start(500);context.started=performance.now();el('record').classList.add('recording');
    el('record-state').textContent='Recording… click to stop';el('record-flag').textContent='LIVE';el('cancel-record').disabled=false;
    context.timer=setInterval(()=>{
      const elapsed=performance.now()-context.started;
      el('record-time').textContent=`${Math.floor(elapsed/1000)}s / 180s`;
      if(elapsed>=MAX_CLIP_MS)stopRecording(false);
    },250);
  }catch(e){release();notice(e?.name==='NotAllowedError'?'Microphone permission denied. You may type instead.':e.message);}
}
el('record').onclick=recordPressed;el('cancel-record').onclick=()=>stopRecording(true);
function newSubmissionId(){return window.crypto?.randomUUID?.()||('turn-'+Date.now()+'-'+Math.random().toString(36).slice(2));}
el('submit').addEventListener('click',async()=>{
  const q=context.question;if(!q||context.busy)return;
  if(context.recorder?.state==='recording'){notice('Stop recording before submitting.');return;}
  const text=(q.kind==='code'?el('code').value:el('transcript').value).trim();
  if(!text){notice('Please provide your answer first.');return;}
  if(context.pendingText!==text){context.pendingId=newSubmissionId();context.pendingText=text;}
  setBusy(true);notice('Interviewer is reviewing your answer…');
  try{
    const response=await jsonPost('/api/answer',{question_id:q.id,kind:q.kind,text,submission_id:context.pendingId});
    if(response.status==='completed'){
      const data=await jsonPost('/api/finish',{});renderReview(data);return;
    }
    renderQuestion(response);notice('Next question. Answer orally or use the editor for coding.');
  }catch(e){notice(e.message+' Your text remains available to retry.');}
  finally{setBusy(false);}
});
function updateClock(data){
  const remaining=Math.max(0,(data.target_seconds||3600)-data.elapsed_seconds);
  el('clock').textContent=`${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')} REMAINING`;
  el('progress-fill').style.width=Math.min(100,(data.elapsed_seconds/3600)*100)+'%';
  el('pause').textContent=data.status==='paused'?'Resume':'Pause';
}
setInterval(async()=>{
  if(el('session').hidden || context.busy)return;
  try{const data=await api('/api/state');updateClock(data);}
  catch{notice('Connection to the local interview service is unavailable; no answer will be submitted until restored.');}
},3000);
el('pause').onclick=async()=>{
  if(context.busy)return;
  if(context.recorder?.state==='recording')stopRecording(true);
  const paused=el('pause').textContent==='Resume';
  try{const state=await jsonPost(paused?'/api/resume-session':'/api/pause',{});updateClock(state);
    if(!paused && 'speechSynthesis'in window)window.speechSynthesis.cancel();notice(paused?'Interview resumed.':'Interview paused.');}
  catch(e){notice(e.message);}
};
el('finish').onclick=async()=>{
  if(!confirm('End this interview and show your review?'))return;
  if(context.recorder?.state==='recording')stopRecording(true);
  if('speechSynthesis'in window)window.speechSynthesis.cancel();
  setBusy(true);
  try{renderReview(await jsonPost('/api/finish',{}));}catch(e){notice(e.message);}finally{setBusy(false);}
};
function renderReview(data){
  show('review');context.session=data;
  const body=el('review-body');body.replaceChildren();
  for(const entry of data.history||[]){
    const box=document.createElement('section');box.className='review-entry';
    const title=document.createElement('strong');title.textContent=`${entry.phase?.toUpperCase()} — ${entry.question}`;box.appendChild(title);
    const answer=document.createElement('pre');answer.textContent=entry.answer;box.appendChild(answer);
    const note=document.createElement('p');note.textContent=entry.assessment||'Not assessed';box.appendChild(note);
    body.appendChild(box);
  }
  el('reference-solutions').textContent=data.reference_solutions || 'Reference solutions unavailable; no independent verification performed.';
  if(!(data.history||[]).length){const p=document.createElement('p');p.textContent='No submitted answers yet.';body.appendChild(p);}
}
el('save-memory').addEventListener('click',async()=>{
  if(context.busy || !context.session || context.session.status!=='completed') return;
  setBusy(true);
  try {
    await jsonPost('/api/save-memory',{confirm:true});
    notice('A minimal evidence summary was saved in your private workspace. No answer transcript was copied.');
  } catch(e) { notice('Could not save interview memory: '+e.message); }
  finally { setBusy(false); }
});
el('download-review').onclick=()=>{
  if(!context.session)return;
  const blob=new Blob([JSON.stringify(context.session,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ai-interview-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),400);
};
window.addEventListener('pagehide',()=>{if(context.recorder?.state==='recording')stopRecording(true);release();if('speechSynthesis'in window)window.speechSynthesis.cancel();});
init();
