// Regression cases for asynchronous recording failures. Simulated media, not hardware.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../skills/ai-interview/scripts/web/app.js'), 'utf8');

async function fixture({deferredPermission=false, maxBytes=1024}={}) {
  const elements = new Map(), events = new Map();
  const stats = {starts:0, releases:0, transcribes:0, saves:[]};
  let recorder, grant, disconnected=false;
  let question={question_id:'q1', text:'Question one'};
  const element=id => {
    if (!elements.has(id)) elements.set(id,{disabled:true,value:id==='language'?'auto':'',textContent:'',classList:{toggle(){}},focus(){},select(){}});
    return elements.get(id);
  };
  const media={getTracks:()=>[{stop(){stats.releases++;}}]};
  class Recorder {
    static isTypeSupported(){return true;}
    constructor(){this.state='inactive';this.mimeType='audio/webm';recorder=this;}
    start(){this.state='recording';stats.starts++;}
    stop(){this.state='inactive';}
  }
  const context={
    crypto:require('node:crypto').webcrypto, document:{getElementById:element},location:{hash:'#token=test',pathname:'/'},history:{replaceState(){}},
    URLSearchParams,Blob,MediaRecorder:Recorder,performance:{now:()=>0},setInterval:()=>1,clearInterval(){},
    window:{isSecureContext:true,MediaRecorder:Recorder,confirm:()=>true,addEventListener:(k,fn)=>events.set(k,fn)},
    navigator:{mediaDevices:{getUserMedia(){return deferredPermission ? new Promise(resolve=>{grant=()=>resolve(media);}) : Promise.resolve(media);}},clipboard:{async writeText(){}}},
    async fetch(url, options={}) {
      if(disconnected) throw new Error('fixture connection failure');
      let data;
      if(url==='/api/health') data={agent_mode:true,max_seconds:180,max_audio_bytes:maxBytes,model:'FAKE',output_dir:'private'};
      else if(url==='/api/question') data={question,stopped:false};
      else if(url.startsWith('/api/transcribe')) {
        stats.transcribes++;
        data={question_id:options.headers['X-Question-ID'],raw_text:'unfinished fixture',draft_id:'d1'};
      }
      if(url==='/api/save') { stats.saves.push(JSON.parse(options.body)); data={question_id:'q1', revision:stats.saves.length, text_path:'fixture'}; }
      return {ok:true,async json(){return data;}};
    }
  };
  vm.createContext(context);vm.runInContext(source,context);
  await new Promise(resolve=>setImmediate(resolve));
  return {element,stats,events,get recorder(){return recorder;},grant:()=>grant(),
    setQuestion:()=>{question={question_id:'q2',text:'Question two'};},
    disconnect:()=>{disconnected=true;},refresh:()=>vm.runInContext('refreshQuestion()',context)};
}

const tests = {
  async inactive_recorder_error_discards_final_data() {
    const f=await fixture();await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['early'])});
    // Native errors may set inactive BEFORE error/dataavailable/stop are delivered.
    f.recorder.state='inactive';f.recorder.onerror();
    assert.equal(f.element('start').disabled,true,'wait for the outstanding stop event');
    f.recorder.ondataavailable({data:new Blob(['last'])});await f.recorder.onstop();
    assert.equal(f.stats.transcribes,0,'must not transcribe a failed partial recording');
  },
  async oversized_final_chunk_is_not_silently_truncated() {
    const f=await fixture({maxBytes:8});await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['1234'])});f.element('stop').onclick();
    f.recorder.ondataavailable({data:new Blob(['567890'])});await f.recorder.onstop();
    assert.equal(f.stats.transcribes,0,'must not send only the earlier chunks');
  },
  async permission_resolving_after_pagehide_releases_without_recording() {
    const f=await fixture({deferredPermission:true});const pending=f.element('start').onclick();
    f.events.get('pagehide')();f.grant();await pending;
    assert.equal(f.stats.starts,0,'a departed page must not start a recorder');
    assert.equal(f.stats.releases,1);
  },
  async question_change_between_stop_and_callback_discards_audio() {
    const f=await fixture();await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['old'])});f.element('stop').onclick();
    f.setQuestion();await f.refresh();await f.recorder.onstop();
    assert.equal(f.stats.transcribes,0,'old final data must not reach transcription');
    assert.equal(f.element('question-id').textContent,'q2');
  },
  async disconnect_between_stop_and_callback_discards_audio() {
    const f=await fixture();await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['old'])});f.element('stop').onclick();
    f.disconnect();await f.refresh();await f.recorder.onstop();
    assert.equal(f.element('retry').disabled,true,'cancelled audio must not remain available for retry');
    assert.equal(f.stats.transcribes,0);
  },
  async confirmation_retries_reuse_id_but_edits_create_new_id() {
    const f=await fixture();await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['ok'])});f.element('stop').onclick();await f.recorder.onstop();
    await f.element('save').onclick();await f.element('save').onclick();
    assert.equal(typeof f.stats.saves[0].submission_id,'string');
    assert.equal(f.stats.saves[0].submission_id,f.stats.saves[1].submission_id);
    assert.equal(f.stats.saves[0].expected_revision,0);
    f.element('text').value='intentional correction';f.element('text').oninput();await f.element('save').onclick();
    assert.notEqual(f.stats.saves[2].submission_id,f.stats.saves[0].submission_id);
  },
  async normal_stop_still_transcribes_once() {
    const f=await fixture();await f.element('start').onclick();
    f.recorder.ondataavailable({data:new Blob(['ok'])});f.element('stop').onclick();await f.recorder.onstop();
    assert.equal(f.stats.transcribes,1);
  }
};
(async()=>{
  let failures=0;
  for(const [name,run] of Object.entries(tests)) {
    try {await run(); console.log('PASS '+name);} catch(e) {failures++;console.error('FAIL '+name+': '+e.message);}
  }
  console.log(`${Object.keys(tests).length} asynchronous UI scenarios, ${failures} failed (simulated media).`);
  process.exitCode=failures?1:0;
})();
