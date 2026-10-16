// Browser mock: the microphone is opened only by the candidate. Acoustic
// amplitude is sampled locally, and the interviewer cannot record its own voice.
const assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs'),vm=require('node:vm');
const elements=new Map(), intervals=[];
let now=0, amplitude=128, opened=0, stopped=0, submitted=0, speeches=[],micEvents=[];
function n(id){if(!elements.has(id))elements.set(id,{id,value:id==='language'?'zh':id==='speech-engine'?'builtin':'',disabled:false,checked:false,hidden:false,style:{},textContent:'',dataset:{},files:[],listeners:{},classList:{add(){},remove(){}},addEventListener(k,f){this.listeners[k]=f},replaceChildren(...c){this.children=c},appendChild(){},click(){}});return elements.get(id)}
const track={enabled:true,readyState:'live',stop(){this.readyState='ended';stopped++;}};
class FakeAudioContext{
  constructor(){this.state='running';this.closed=false;global.audio=this}
  createMediaStreamSource(stream){return {connect(){},disconnect(){}}}
  createAnalyser(){return {fftSize:1024,getByteTimeDomainData(values){values.fill(amplitude)},disconnect(){}}}
  close(){this.closed=true;return Promise.resolve()}
}
class FakeRecorder{
  static isTypeSupported(type){return type.startsWith('audio/webm')}
  constructor(stream,opts){this.mimeType='audio/webm';this.state='inactive';global.recorder=this}
  start(){this.state='recording'}
  stop(){this.state='inactive';this.onstop?.()}
}
class Utterance{constructor(t){this.text=t;this.onend=null;this.onerror=null;}}
class Option{constructor(label,value){this.label=label;this.value=value}}
const synthesis={speaking:false,speak(u){speeches.push(u);this.speaking=true;},cancel(){this.speaking=false}};
const ctx={
  document:{getElementById:n,createElement(){return {textContent:'',appendChild(){}}}},
  location:{hash:'#token=unit',pathname:'/'},history:{replaceState(){}},URLSearchParams,Option,Blob,Date,Math,Uint8Array,
  window:{AudioContext:FakeAudioContext,MediaRecorder:FakeRecorder,SpeechSynthesisUtterance:Utterance,speechSynthesis:synthesis,addEventListener(){},crypto:{randomUUID:()=> 'mock'}},
  SpeechSynthesisUtterance:Utterance,MediaRecorder:FakeRecorder,AudioContext:FakeAudioContext,
  navigator:{mediaDevices:{async getUserMedia(){opened++;return {getTracks(){return [track]},getAudioTracks(){return [track]}}}}},
  performance:{now:()=>now},setInterval(fn,delay){intervals.push({fn,delay});return intervals.length},clearInterval(id){},
  setTimeout,clearTimeout,confirm:()=>true,
  fetch:async(url,opts)=>{
    let result={};
    if(url==='/api/providers')result={roles:[{id:'ai_researcher',label:'AI Research Scientist',phases:[]}],providers:[{id:'codex',kind:'cli',configured:true,requires:'installed'}]};
    else if(url==='/api/health')result={speech_ready:true};
    else if(url==='/api/state')result={status:'setup'};
    else if(url==='/api/jobs')result={jobs:[]};
    else if(url==='/api/voicestudio/status')result={available:false,streaming:false,voices:[]};
    else if(url.startsWith('/api/evidence-summary'))result={recent_papers:0,memory_topics:0};
    else if(url==='/api/resume')result={characters:100,preview:'CV preview'};
    else if(url==='/api/start')result={id:'q1',question:'Tell me about your research',kind:'voice',phase:'hr',phase_label:'HR'};
    else if(url==='/api/answer'){submitted++;result={id:'q2',kind:'voice',phase:'hr',phase_label:'HR',question:'Next question'};}
    else if(url==='/api/acoustic-checkin'){micEvents.push(JSON.parse(opts.body));result={status:'logged'};}
    else if(url.startsWith('/api/transcribe'))result={raw_text:'A real candidate reply'};
    return {ok:true,json:async()=>result};
  }
};
vm.createContext(ctx);
const base=path.join(__dirname,'../skills/ai-interview/scripts/studio_web');
vm.runInContext(fs.readFileSync(path.join(base,'silence_monitor.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(base,'app.js'),'utf8'),ctx);
(async()=>{
  await new Promise(setImmediate);
  n('resume').files=[{size:5,name:'cv.pdf',arrayBuffer:async()=>new Uint8Array([1]).buffer}];
  await n('resume').listeners.change();n('provider').value='codex';n('role').value='ai_researcher';n('consent').checked=true;n('consent').listeners.change();
  await n('begin').listeners.click();
  assert.equal(speeches.length,1,'initial interviewer asks question');
  assert.equal(opened,0,'no microphone opened automatically');
  await n('record').onclick();
  assert.equal(opened,1,'mic opened after candidate click');
  const initialSpeechCount=speeches.length;
  n('replay').onclick();
  assert.equal(speeches.length,initialSpeechCount,'replaying a question cannot feed it to an active microphone');
  assert.equal(track.enabled,true);
  const pulses=intervals.filter(x=>x.delay===500);
  assert.ok(pulses.length>=1,'microphone-only silence monitor sampled at 500ms');
  now=39000;pulses.at(-1).fn();assert.equal(speeches.length,1);
  now=40500;pulses.at(-1).fn();
  assert.equal(speeches.length,2,'interviewer checks in after prolonged acoustic silence');
  assert.match(speeches.at(-1).text,/思考|重复|需要/);
  assert.equal(track.enabled,false,'mic is disabled while the interviewer speaks');
  assert.equal(submitted,0,'check-in cannot advance or grade interview');
  await new Promise(setImmediate);
  assert.equal(micEvents.length,1,'local amplitude check-in logged once without recording');
  assert.deepEqual(micEvents[0],{question_id:'q1'});
  speeches.at(-1).onend?.();synthesis.speaking=false;
  assert.equal(track.enabled,true,'mic restored after interviewer finishes');
  now=85000;pulses.at(-1).fn();assert.equal(speeches.length,2,'no repeated acoustic check-in in same recording');
  assert.equal(micEvents.length,1,'acoustic check-in is logged once');
  n('record').onclick();
  await new Promise(setImmediate);
  assert.equal(global.audio.closed,true,'mic analyser closed after recording');
  assert.equal(stopped,1);
  track.enabled=true;track.readyState='live';
  await n('record').onclick();
  assert.equal(opened,2);
  now=133000;intervals.filter(x=>x.delay===500).at(-1).fn();
  assert.equal(track.enabled,false,'second check-in is audible only with mic temporarily disabled');
  n('cancel-record').onclick();
  await new Promise(setImmediate);
  assert.equal(track.enabled,true,'cancelling mid-check-in restores mic state');
  assert.equal(submitted,0,'cancelling a check-in never submits a candidate answer');
  console.log('PASS: natural check-in once, mic muted/restore on end or cancel, no auto-submit, teardown');
})().catch(err=>{console.error(err);process.exitCode=1});
