'use strict';
const el = id => document.getElementById(id);
const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
history.replaceState(null, '', location.pathname);
const context = {question:null, role:null, provider:null, muted:false, busy:false, voiceReady:false,
  stream:null, recorder:null, chunks:[], started:0, timer:null, cancel:false, recordingQuestion:null,
  pendingId:null, pendingText:null, session:null, lastSpoken:null,
  builtinReady:false, voiceStudio:{available:false,streaming:false,voices:[],relay_url:null},
  speechChoice:'builtin', playback:null, playbackUrl:null, playFetch:null, speechEpoch:0,
  live:null, recordingBytes:0, finishingRecording:false, openingRecording:false, departed:false,
  paused:false, timekeeperSeen:new Set(), sessionWarningsSeen:new Set(), autoReviewPending:false, pendingSkipId:null,
  silenceWatch:null, micCheckin:null, lastCheckinAt:-Infinity};
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
  el('record').disabled=v||context.openingRecording||context.finishingRecording||!canRecord()||!context.question||context.question.kind==='code';
  el('pause').disabled=v;el('finish').disabled=v;
  el('more-time').disabled=v||context.paused||!context.question;
  el('skip-question').disabled=v||context.paused||!context.question;
}
function canRecord(){
  return el('speech-engine').value==='voicestudio' ? !!context.voiceStudio.available : !!context.builtinReady;
}
function stopPlayback(){
  cancelMicCheckin();
  context.speechEpoch++;
  if(context.playFetch){context.playFetch.abort();context.playFetch=null;}
  if(context.playback){context.playback.pause();context.playback=null;}
  if(context.playbackUrl){URL.revokeObjectURL(context.playbackUrl);context.playbackUrl=null;}
  if('speechSynthesis' in window)window.speechSynthesis.cancel();
}
function builtinSpeak(q){
  if(!('speechSynthesis'in window)){notice('Speech playback is unavailable. Read the question on screen.');return;}
  const u=new SpeechSynthesisUtterance(q.question);
  u.lang=/[\u3400-\u9fff]/.test(q.question)?'zh-CN':'en-GB';u.rate=.94;u.pitch=1;
  u.onerror=()=>notice('Browser speech playback was blocked. Click Play question to retry.');
  window.speechSynthesis.speak(u);context.lastSpoken=q.id;
}
async function refreshVoiceStudio(showNotice=false){
  try{
    const data=await api('/api/voicestudio/status');
    context.voiceStudio={available:data.available===true, streaming:data.streaming===true,
      relay_url:typeof data.relay_url==='string'?data.relay_url:null,
      voices:Array.isArray(data.voices)?data.voices:[]};
    const choices=['default',...context.voiceStudio.voices.filter(id=>id!=='default')].slice(0,20);
    const old=el('voice-profile').value;
    el('voice-profile').replaceChildren(...choices.map(id=>new Option(id==='default'?'Default voice':id,id)));
    if(choices.includes(old))el('voice-profile').value=old;
    if(!data.available && el('speech-engine').value==='voicestudio'){
      el('speech-engine').value='builtin';context.speechChoice='builtin';stopPlayback();
    }
    el('voice-backend-status').textContent=data.available
      ? `Local VoiceStudio detected. ${data.streaming?'Streaming subtitles + TTS available.':'Batch transcription + TTS only (stream relay unavailable).'} Models may still need to be installed in VoiceStudio.`
      : `VoiceStudio not available. Start the separately installed app/backend, then Check VoiceStudio. ${data.detail||''}`;
    if(showNotice)notice(data.available?'VoiceStudio detected. Select it in Speech Engine.':'VoiceStudio not detected; browser/Whisper fallback remains available.');
  }catch(e){
    context.voiceStudio={available:false,streaming:false,voices:[],relay_url:null};
    el('voice-backend-status').textContent='Unable to check VoiceStudio; legacy voice options remain available.';
    if(showNotice)notice('VoiceStudio check failed: '+e.message);
  }
  context.voiceReady=canRecord();setBusy(context.busy);
}
el('check-voice').addEventListener('click',()=>refreshVoiceStudio(true));
el('speech-engine').addEventListener('change',()=>{
  if(context.busy || context.finishingRecording || context.recorder?.state==='recording'){
    el('speech-engine').value=context.speechChoice;
    notice('Finish or cancel the current recording before switching speech backends.');return;
  }
  if(el('speech-engine').value==='voicestudio' && !el('voicestudio-consent').checked){
    el('speech-engine').value='builtin';notice('Review the external VoiceStudio model/download and remote-routing settings, then check the consent box.');
  }
  if(el('speech-engine').value==='voicestudio' && !context.voiceStudio.available){
    el('speech-engine').value='builtin';notice('VoiceStudio not running; click Check VoiceStudio after starting it.');
  }
  context.speechChoice=el('speech-engine').value;
  stopPlayback();context.voiceReady=canRecord();
  el('voice-info').textContent=context.speechChoice==='voicestudio'
    ? 'VoiceStudio: realtime preview if relay is available. Final text must be reviewed and submitted.'
    : 'Browser TTS + optional local Whisper; click Record and edit transcription before submitting.';
  setBusy(context.busy);
});
el('voicestudio-consent').addEventListener('change',()=>{
  if(el('voicestudio-consent').checked)return;
  if(el('speech-engine').value==='voicestudio'){
    if(context.recorder?.state==='recording')stopRecording(true);
    if(context.live){context.live.cancelled=true;context.live.resolveFinal(null);context.live.socket.close();context.live=null;}
    stopPlayback();el('speech-engine').value='builtin';context.speechChoice='builtin';
    context.voiceReady=canRecord();setBusy(context.busy);
    notice('VoiceStudio consent revoked; microphone stream and VoiceStudio playback stopped.');
  }
});
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
    context.roles=meta.roles;context.providers=meta.providers;context.builtinReady=health.speech_ready;context.voiceReady=health.speech_ready;
    await refreshVoiceStudio(false);
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
    if(!context.builtinReady && !context.voiceStudio.available){el('voice-info').textContent='No local STT is available. Type your response below, or install Whisper / start VoiceStudio.';notice('Local speech recognition not loaded. Text mode remains available.');}
    if(state.status!=='setup'){
      context.session=state;context.role=state.role;context.provider=state.provider;
      if(state.status==='completed')renderReview(state.review || await jsonPost('/api/finish',{}));
      else {show('session');if(state.question){renderQuestion(state.question);
        // Do not replay old reminders aloud after a tab reload.
        for(const event of state.timekeeper?.reminders||[])context.timekeeperSeen.add(event.id);
        for(const event of state.timekeeper?.session_reminders||[])context.sessionWarningsSeen.add(event.id);}
        updateClock(state);}
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
el('mute').addEventListener('change',()=>{context.muted=el('mute').checked;if(context.muted)stopPlayback();});
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
  stopPlayback();
  if(el('speech-engine').value!=='voicestudio' || !context.voiceStudio.available){builtinSpeak(question);return;}
  const epoch=context.speechEpoch;
  const aborter=new AbortController();context.playFetch=aborter;
  (async()=>{
    try{
      const response=await fetch('/api/voicestudio/speak',{
        method:'POST',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},
        cache:'no-store',redirect:'error',signal:aborter.signal,
        body:JSON.stringify({question_id:question.id,text:question.question,voice:el('voice-profile').value||'default'})
      });
      if(!response.ok){const data=await response.json();throw Error(data.error||`HTTP ${response.status}`);}
      const blob=await response.blob();
      if(context.muted || context.departed || epoch!==context.speechEpoch || context.question?.id!==question.id)return;
      const url=URL.createObjectURL(blob);context.playbackUrl=url;
      const player=new Audio(url);context.playback=player;
      player.onended=()=>{if(context.playback===player)stopPlayback();};
      await player.play();context.lastSpoken=question.id;
    }catch(e){
      if(epoch===context.speechEpoch && context.question?.id===question.id && !context.muted && !context.departed){
        notice('VoiceStudio speech unavailable; using browser voice instead. '+e.message);
        builtinSpeak(question);
      }
    }finally{if(context.playFetch===aborter)context.playFetch=null;}
  })();
}
function renderQuestion(q){
  stopPlayback();
  if(context.recorder&&context.recorder.state!=='inactive')stopRecording(true);
  context.question=q;
  context.pendingId=null;context.pendingText=null;context.pendingSkipId=null;context.timekeeperSeen=new Set();
  el('question-elapsed').textContent='00:00 / TIME GUIDE';el('question-progress').style.width='0%';
  el('timekeeper-note').textContent='Timekeeper checks in after long unanswered intervals. Optional local microphone-silence checks run only while recording; thinking time is never graded.';
  context.lastCheckinAt=-Infinity;
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
  el('live-preview').textContent='Streaming partials are not graded; wait for final text.';
  el('record-flag').textContent='READY';
  speak(q);
  setBusy(context.busy);
}
el('replay').onclick=()=>{
  if(context.recorder?.state==='recording'){notice('Stop recording before replaying the interviewer question.');return;}
  if(context.question)speak(context.question);
};

// These prompts are part of the interviewer's role, but generated by the local
// deterministic Timekeeper. Asking for clarification never starts an LLM call.
function microphoneCheckinPrompt(){
  const language=context.session?.language||el('language').value;
  return language==='zh'
    ? '你还在思考吗？需要我重复一下题目，或者再给你一点时间吗？'
    : 'Are you still thinking it through? Should I repeat the question, or give you a little more time?';
}
function cancelMicCheckin(){
  const active=context.micCheckin;
  if(!active)return;
  context.micCheckin=null;
  if(active.timeout)clearTimeout(active.timeout);
  for(const {track,wasEnabled} of active.tracks){
    if(track.readyState!=='ended')track.enabled=wasEnabled;
  }
}
function stopSilenceWatch(){
  const watch=context.silenceWatch;
  context.silenceWatch=null;
  if(!watch)return;
  clearInterval(watch.timer);
  try{watch.source?.disconnect();}catch{}
  try{watch.analyser?.disconnect();}catch{}
  try{watch.audio?.close();}catch{}
}
function spokenCheckinWhileRecording(message,recorder,questionId){
  if(context.muted || context.departed || context.paused || context.busy ||
     context.micCheckin || context.question?.id!==questionId || recorder.state!=='recording' ||
     !('speechSynthesis' in window) || window.speechSynthesis.speaking ||
     !context.stream?.getAudioTracks)return false;
  const tracks=context.stream.getAudioTracks();
  // If any track cannot be muted, NEVER speak into an active recorder.
  if(!tracks.length || tracks.some(t=>typeof t.enabled!=='boolean'))return false;
  const guard={tracks:tracks.map(track=>({track,wasEnabled:track.enabled})),timeout:null};
  context.micCheckin=guard;
  for(const {track} of guard.tracks)track.enabled=false;
  try{
    const utterance=new SpeechSynthesisUtterance(message);
    utterance.lang=/[\u3400-\u9fff]/.test(message)?'zh-CN':'en-GB';
    utterance.rate=.95;
    utterance.onend=()=>cancelMicCheckin();
    utterance.onerror=()=>cancelMicCheckin();
    guard.timeout=setTimeout(()=>{
      if(context.micCheckin===guard){
        cancelMicCheckin();
        window.speechSynthesis.cancel();
      }
    },12000);
    window.speechSynthesis.speak(utterance);
    context.lastCheckinAt=performance.now();
    return true;
  }catch{
    cancelMicCheckin();
    return false;
  }
}
function startSilenceWatch(stream,recorder,questionId){
  stopSilenceWatch();
  const Monitor=window.AIInterviewSilenceMonitor;
  const AudioContextClass=window.AudioContext||window.webkitAudioContext;
  if(!Monitor || !AudioContextClass)return;
  let audio=null;
  try{
    audio=new AudioContextClass();
    if(audio.state==='suspended' && typeof audio.resume==='function'){
      void Promise.resolve(audio.resume()).catch(()=>{});
    }
    const source=audio.createMediaStreamSource(stream);
    const analyser=audio.createAnalyser();
    analyser.fftSize=1024;
    source.connect(analyser); // no connection to audio output or speaker
    const bytes=new Uint8Array(analyser.fftSize);
    const policy=new Monitor.SilenceMonitor({startedAt:performance.now()});
    const watch={audio,source,analyser,timer:null,recorder,questionId};
    watch.timer=setInterval(()=>{
      if(context.silenceWatch!==watch || context.paused || context.departed || context.busy ||
         context.micCheckin || recorder.state!=='recording' || context.question?.id!==questionId ||
         audio.state!=='running')return;
      analyser.getByteTimeDomainData(bytes);
      if(!policy.sample(Monitor.rmsFromBytes(bytes),performance.now()))return;
      const prompt=microphoneCheckinPrompt();
      el('timekeeper-note').textContent='INTERVIEWER CHECK-IN · '+prompt;
      notice('Prolonged low microphone activity detected locally (approximate). Your answer is not graded.');
      void jsonPost('/api/acoustic-checkin',{question_id:questionId}).catch(()=>{});
      if(performance.now()-context.lastCheckinAt>=90000){
        spokenCheckinWhileRecording(prompt,recorder,questionId);
      }else{
        // An unanswered-question reminder was spoken recently: avoid piling on.
        // This recording's monitor is deliberately once-only.
      }
    },500);
    context.silenceWatch=watch;
  }catch{
    try{audio?.close();}catch{}
    // Browser lacks Web Audio or rejects analyser: regular unanswered-question
    // timekeeper still works; never pretend that acoustic silence was detected.
  }
}
function release(){
  if(context.micCheckin){cancelMicCheckin();if('speechSynthesis' in window)window.speechSynthesis.cancel();}
  stopSilenceWatch();
  if(context.stream){context.stream.getTracks().forEach(t=>t.stop());context.stream=null;}
  if(context.timer){clearInterval(context.timer);context.timer=null;}
  el('record').classList.remove('recording');el('record-flag').textContent='READY';el('cancel-record').disabled=true;
}
async function openLiveStream(questionId){
  const server=context.voiceStudio.relay_url;
  if(!server || !context.voiceStudio.streaming || !('WebSocket'in window))return null;
  let socket;
  return new Promise((resolve,reject)=>{
    let settled=false, timer;
    const fail=message=>{
      if(settled)return;settled=true;clearTimeout(timer);
      try{socket?.close();}catch{}
      reject(new Error(message));
    };
    try{socket=new WebSocket(server);}catch(e){reject(e);return;}
    const live={socket,questionId,sendChain:Promise.resolve(),cancelled:false,completed:false,
      finalPromise:null,resolveFinal:null};
    live.finalPromise=new Promise(done=>live.resolveFinal=done);
    timer=setTimeout(()=>fail('VoiceStudio streaming handshake timed out'),7000);
    socket.onopen=()=>socket.send(JSON.stringify({type:'start',token,question_id:questionId}));
    socket.onmessage=ev=>{
      let data;
      try{data=JSON.parse(ev.data);}catch{return;}
      if(!settled){
        if(data.type==='ready'){
          settled=true;clearTimeout(timer);
          if(context.question?.id!==questionId || context.departed){
            live.cancelled=true;socket.close();live.resolveFinal(null);
            reject(new Error('Interview question changed before recording'));
          }else resolve(live);
        }else if(data.type==='error')fail(data.message||'VoiceStudio connection refused');
        return;
      }
      if(live.cancelled || context.question?.id!==questionId)return;
      if(data.type==='partial' && typeof data.text==='string'){
        el('live-preview').textContent='LIVE (unconfirmed): '+data.text.slice(0,400);
      }else if(data.type==='final' && data.final_kind==='utterance' && typeof data.text==='string'){
        el('live-preview').textContent='Utterance (not final answer): '+data.text.slice(0,400);
      }else if(data.type==='final' && data.final_kind==='summary' && typeof data.text==='string'){
        live.completed=true;live.resolveFinal(data.text);socket.close();
      }else if(data.type==='error'){
        live.resolveFinal(null);socket.close();
      }
    };
    socket.onerror=()=>{if(!settled)fail('VoiceStudio streaming socket failed');else live.resolveFinal(null);};
    socket.onclose=()=>{if(!settled)fail('VoiceStudio streaming handshake closed');else live.resolveFinal(null);};
  });
}
function stopRecording(cancel=false){
  context.cancel=cancel;
  context.finishingRecording=true;
  if(cancel && context.live){context.live.cancelled=true;context.live.resolveFinal(null);
    try{context.live.socket.close();}catch{}context.live=null;}
  if(context.recorder&&context.recorder.state!=='inactive')context.recorder.stop();
  release();
}
async function recordPressed(){
  if(context.recorder&&context.recorder.state==='recording'){stopRecording(false);return;}
  if(context.busy||context.openingRecording||context.finishingRecording||!context.question||context.question.kind!=='voice')return;
  if(el('transcript').value.trim()&&!confirm('Starting a new recording will replace your unsubmitted draft. Continue?'))return;
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){notice('Microphone API unavailable. Type your answer instead.');return;}
  stopPlayback();
  context.openingRecording=true;setBusy(context.busy);
  try{
    const id=context.question.id;
    let live=null;
    if(el('speech-engine').value==='voicestudio' && context.voiceStudio.streaming && context.voiceStudio.relay_url){
      try{live=await openLiveStream(id);}catch(e){notice(e.message+'; using VoiceStudio batch transcription instead.');}
    }
    context.live=live;
    if(context.departed || context.question?.id!==id){if(live)live.socket.close();return;}
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    if(!context.question||context.question.id!==id || context.departed ||
        (live && !el('voicestudio-consent').checked)){stream.getTracks().forEach(t=>t.stop());if(live)live.socket.close();return;}
    context.stream=stream;context.recordingQuestion=id;context.cancel=false;context.chunks=[];context.recordingBytes=0;
    const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(x=>MediaRecorder.isTypeSupported(x));
    const recorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined);context.recorder=recorder;
    recorder.ondataavailable=e=>{
      if(context.cancel||!e.data?.size)return;
      context.recordingBytes+=e.data.size;
      if(context.recordingBytes>MAX_AUDIO_BYTES){stopRecording(true);notice('Recording too large; discarded, not silently truncated.');return;}
      context.chunks.push(e.data);
      if(live && !live.cancelled){
        live.sendChain=live.sendChain.then(()=>e.data.arrayBuffer()).then(bytes=>{
          if(live.socket.readyState===1 && !live.cancelled)live.socket.send(bytes);
        }).catch(()=>{live.resolveFinal(null);});
      }
    };
    recorder.onstop=async()=>{
      const canceled=context.cancel||context.question?.id!==id||context.departed;
      release();
      if(canceled){context.chunks=[];if(live){live.cancelled=true;live.socket.close();}
        context.live=null;context.finishingRecording=false;setBusy(false);notice('Recording discarded.');return;}
      const audio=new Blob(context.chunks,{type:recorder.mimeType||'application/octet-stream'});context.chunks=[];
      if(audio.size>MAX_AUDIO_BYTES||!audio.size){context.finishingRecording=false;setBusy(false);notice('Recording is empty or too large.');return;}
      setBusy(true);el('record-state').textContent='Transcribing locally…';
      try{
        let finalText=null;
        if(live && !live.cancelled){
          try{
            await live.sendChain;
            if(live.socket.readyState===1)live.socket.send(JSON.stringify({type:'input_audio.end'}));
            finalText=await Promise.race([live.finalPromise,new Promise(resolve=>setTimeout(()=>resolve(null),15000))]);
          }finally{live.socket.close();}
        }
        if(finalText===null){
          const backend=el('speech-engine').value==='voicestudio'?'voicestudio':'builtin';
          const result=await api('/api/transcribe?backend='+backend+'&question_id='+encodeURIComponent(id),'POST',audio,audio.type);
          finalText=result.raw_text||'';
        }
        if(context.question?.id===id && !context.departed){
          el('transcript').value=finalText;
          el('live-preview').textContent='FINAL TRANSCRIPT — review and submit explicitly.';
          notice('Review names, numbers, formulas and negation before submitting.');
        }
      }catch(e){notice(e.message+' No answer was submitted. Retry or type your response.');}
      finally{
        context.live=null;context.finishingRecording=false;
        setBusy(false);el('record-state').textContent='Click to record';
      }
    };
    recorder.onerror=()=>{stopRecording(true);notice('Microphone recording failed. Try typing instead.');};
    recorder.start(500);context.started=performance.now();el('record').classList.add('recording');
    startSilenceWatch(stream,recorder,id);
    el('record-state').textContent='Recording… click to stop';el('record-flag').textContent='LIVE';el('cancel-record').disabled=false;
    context.timer=setInterval(()=>{
      const elapsed=performance.now()-context.started;
      el('record-time').textContent=`${Math.floor(elapsed/1000)}s / 180s`;
      if(elapsed>=MAX_CLIP_MS)stopRecording(false);
    },250);
  }catch(e){if(context.live){context.live.cancelled=true;context.live.socket.close();context.live=null;}
    release();context.finishingRecording=false;notice(e?.name==='NotAllowedError'?'Microphone permission denied. You may type instead.':e.message);}
  finally{context.openingRecording=false;setBusy(context.busy);}
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
function clockLabel(seconds){
  const s=Math.max(0,Math.floor(Number(seconds)||0));
  return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
}
function remindAloud(message,questionKind){
  if(performance.now()-context.lastCheckinAt<90000)return;
  if(context.muted || context.busy || context.departed || context.paused ||
     questionKind==='code' || context.openingRecording || context.finishingRecording ||
     (context.recorder && context.recorder.state==='recording') ||
     context.playback || !!el('transcript').value.trim() ||
     !('speechSynthesis' in window) || window.speechSynthesis.speaking)return;
  // Local, short alert; do not call another model or VoiceStudio just to tell time.
  const u=new SpeechSynthesisUtterance(message);
  u.lang=/[\u3400-\u9fff]/.test(message)?'zh-CN':'en-GB';u.rate=.96;
  window.speechSynthesis.speak(u);
  context.lastCheckinAt=performance.now();
}
function updateQuestionTimer(timing,status){
  if(!timing || timing.question_id!==context.question?.id)return;
  const elapsed=timing.elapsed_seconds||0;
  const budget=Math.max(1,timing.recommended_seconds||300);
  el('question-elapsed').textContent=`${clockLabel(elapsed)} / ${clockLabel(budget)} GUIDE`;
  el('question-progress').style.width=Math.min(100,100*elapsed/budget)+'%';
  const reminders=timing.reminders||[];
  const newest=reminders[reminders.length-1];
  if(newest)el('timekeeper-note').textContent=newest.message;
  const unread=reminders.filter(e=>!context.timekeeperSeen.has(e.id));
  for(const reminder of unread)context.timekeeperSeen.add(reminder.id);
  if(unread.length && status==='active' && context.question?.kind==='voice')
    remindAloud(unread[unread.length-1].checkin_prompt||unread[unread.length-1].message,context.question.kind);
  const remainingEvents=(timing.session_reminders||[]).filter(e=>!context.sessionWarningsSeen.has(e.id));
  for(const event of remainingEvents)context.sessionWarningsSeen.add(event.id);
  if(remainingEvents.length){
    const latest=remainingEvents[remainingEvents.length-1];
    el('timekeeper-note').textContent=latest.message;
    if(status==='active')remindAloud(latest.message,context.question?.kind);
  }
}
function updateClock(data){
  const remaining=Math.max(0,(data.target_seconds||3600)-(data.elapsed_seconds||0));
  el('clock').textContent=`${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')} REMAINING`;
  el('progress-fill').style.width=Math.min(100,(data.elapsed_seconds/3600)*100)+'%';
  el('pause').textContent=data.status==='paused'?'Resume':'Pause';
  context.paused=data.status==='paused';
  updateQuestionTimer(data.timekeeper,data.status);
  setBusy(context.busy);
}
setInterval(async()=>{
  if(el('session').hidden || context.busy)return;
  try{const data=await api('/api/state');updateClock(data);
    if(data.status==='completed' && !context.autoReviewPending){
      context.autoReviewPending=true;stopPlayback();
      if(context.recorder?.state==='recording')stopRecording(true);
      setBusy(true);
      try{renderReview(data.review||await jsonPost('/api/finish',{}));}
      catch(e){context.autoReviewPending=false;notice('Interview clock finished; review could not load: '+e.message);}
      finally{setBusy(false);}
    }
  }
  catch{notice('Connection to the local interview service is unavailable; no answer will be submitted until restored.');}
},3000);
el('more-time').addEventListener('click',async()=>{
  const q=context.question;
  if(!q||context.busy||context.paused)return;
  setBusy(true);
  try{
    const result=await jsonPost('/api/extend-question',{question_id:q.id});
    if(context.question?.id!==q.id)return;
    updateQuestionTimer(result.timekeeper,'active');
    notice("One minute added to this question's suggested budget. The 60-minute session limit is unchanged.");
  }catch(e){notice('Cannot extend this question: '+e.message);}
  finally{setBusy(false);}
});
el('skip-question').addEventListener('click',async()=>{
  const q=context.question;
  if(!q||context.busy||context.paused||context.openingRecording||context.finishingRecording||context.recorder?.state==='recording')return;
  if(!confirm('Skip this question without grading it? Any unsubmitted draft will be discarded.'))return;
  if(!context.pendingSkipId)context.pendingSkipId=newSubmissionId();
  setBusy(true);stopPlayback();
  try{
    const response=await jsonPost('/api/skip',{question_id:q.id,submission_id:context.pendingSkipId});
    if(response.status==='completed'){
      renderReview(await jsonPost('/api/finish',{}));return;
    }
    renderQuestion(response);notice('Question explicitly skipped without a correctness rating.');
  }catch(e){notice('Could not skip the question: '+e.message+'; try again.');}
  finally{setBusy(false);}
});
el('pause').onclick=async()=>{
  if(context.busy)return;
  if(context.recorder?.state==='recording')stopRecording(true);
  const paused=el('pause').textContent==='Resume';
  try{const state=await jsonPost(paused?'/api/resume-session':'/api/pause',{});updateClock(state);
    if(!paused)stopPlayback();notice(paused?'Interview resumed.':'Interview paused.');}
  catch(e){notice(e.message);}
};
el('finish').onclick=async()=>{
  if(!confirm('End this interview and show your review?'))return;
  if(context.recorder?.state==='recording')stopRecording(true);
  stopPlayback();
  setBusy(true);
  try{renderReview(await jsonPost('/api/finish',{}));}catch(e){notice(e.message);}finally{setBusy(false);}
};
function renderReview(data){
  show('review');context.session=data;context.question=null;
  const stats=data.timing||{};
  el('timing-summary').textContent=`Timekeeper: ${stats.answered_count||0} answered, ${stats.skipped_count||0} skipped, ${stats.unanswered_count||0} unfinished; ${stats.turns?.length||0} questions timed. Time taken is never treated as a competence score.`;
  const body=el('review-body');body.replaceChildren();
  for(const entry of data.history||[]){
    const box=document.createElement('section');box.className='review-entry';
    const title=document.createElement('strong');title.textContent=`${entry.phase?.toUpperCase()} — ${entry.question}`;box.appendChild(title);
    const answer=document.createElement('pre');answer.textContent=entry.response_status==='skipped'?'[Skipped explicitly · not assessed]':entry.answer;box.appendChild(answer);
    const timing=document.createElement('p');timing.className='smallnote';timing.textContent=`Active answer time: ${clockLabel(entry.answer_elapsed_seconds||0)} · ${entry.response_status||'answered'}`;box.appendChild(timing);
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
window.addEventListener('pagehide',()=>{context.departed=true;if(context.recorder?.state==='recording')stopRecording(true);
  if(context.live){context.live.cancelled=true;context.live.resolveFinal(null);context.live.socket.close();context.live=null;}
  release();stopPlayback();});
init();
