// Fake browser + fake VoiceStudio. Does not open a device, install a model or play audio.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const elements=new Map();
const n=id=>{if(!elements.has(id))elements.set(id,{id,value:id==='language'?'zh':id==='speech-engine'?'builtin':'',disabled:false,checked:false,hidden:false,
 files:[],dataset:{},style:{},textContent:'',listeners:{},classList:{add(){},remove(){}},
 addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(...children){this.children=children;},appendChild(){},click(){}});return elements.get(id)};
class FakeRecorder {
  static isTypeSupported(v){return v.includes('webm');}
  constructor(stream,config){this.mimeType=config?.mimeType||'audio/webm';this.state='inactive';global.recorder=this;}
  start(){this.state='recording';} stop(){this.state='inactive';}
}
class FakeWebSocket {
  static OPEN=1;
  constructor(url){assert.match(url,/^ws:\/\/127\.0\.0\.1:/);this.readyState=0;global.ws=this;global.wsOpens++;setImmediate(()=>{this.readyState=1;this.onopen?.()});}
  send(value){if(typeof value==='string'){
      let payload=JSON.parse(value);
      if(payload.type==='start')setImmediate(()=>this.onmessage?.({data:JSON.stringify({type:'ready',question_id:payload.question_id})}));
      else if(payload.type==='input_audio.end')setImmediate(()=>this.onmessage?.({data:JSON.stringify({type:'final',final_kind:'summary',text:'Final confirmed by VoiceStudio'})}));
    }else{
      global.sentAudio++;
      setImmediate(()=>this.onmessage?.({data:JSON.stringify({type:'partial',text:'not final yet'})}));
      setImmediate(()=>this.onmessage?.({data:JSON.stringify({type:'final',final_kind:'utterance',text:'intermediate final'})}));
    }}
  close(){this.readyState=3;setImmediate(()=>this.onclose?.());}
}
let microphoneOpens=0, stopped=0, speechRequests=0, submits=0, browserSpeeches=0;
global.wsOpens=0;global.sentAudio=0;
class Opt{constructor(label,value){this.label=label;this.value=value;}}
class FakeAudio {constructor(url){this.url=url;this.paused=false;global.player=this;}play(){global.playedAudio=(global.playedAudio||0)+1;return Promise.resolve();}pause(){this.paused=true;}}
const ctx={
 document:{getElementById:n,createElement:()=>({textContent:'',appendChild(){}})},
 location:{hash:'#token=secret',pathname:'/'},history:{replaceState(){}},URLSearchParams,Option:Opt,WebSocket:FakeWebSocket,Audio:FakeAudio,
 navigator:{mediaDevices:{async getUserMedia(){microphoneOpens++;return {getTracks(){return [{stop(){stopped++}}]}}}}},
 window:{MediaRecorder:FakeRecorder,WebSocket:FakeWebSocket,speechSynthesis:{speak(){browserSpeeches++},cancel(){}},SpeechSynthesisUtterance:class {},addEventListener(){},crypto:{randomUUID(){return 'r0'}}},
 MediaRecorder:FakeRecorder,SpeechSynthesisUtterance:class {},performance:{now:()=>0},
 URL:{createObjectURL(){return 'blob:fake'},revokeObjectURL(){}},setTimeout,clearTimeout,setInterval(){return 1;},clearInterval(){},setImmediate,confirm:()=>true,
 Blob,Date,Math,AbortController,
 fetch:async(url,options={})=>{
   let data;
   if(url==='/api/providers')data={roles:[{id:'ai_researcher',label:'AI Researcher',phases:[]}],providers:[{id:'codex',configured:true,requires:'codex'}]};
   else if(url==='/api/health')data={speech_ready:false};
   else if(url==='/api/state')data={status:'setup'};
   else if(url==='/api/jobs')data={jobs:[]};
   else if(url==='/api/voicestudio/status')data={available:true,streaming:true,voices:['default','fake-voice'],relay_url:'ws://127.0.0.1:39999/stream'};
   else if(url==='/api/evidence-summary?role=ai_researcher')data={recent_papers:0,memory_topics:0};
   else if(url==='/api/resume')data={characters:120,preview:'Candidate resume'};
   else if(url==='/api/start')data={id:'q101',kind:'voice',phase:'hr',phase_label:'HR',question:'Why the attention model?'};
   else if(url==='/api/voicestudio/speak'){
     speechRequests++;const q=JSON.parse(options.body);assert.equal(q.question_id,'q101');
     return {ok:true,headers:{get:()=> 'audio/wav'},blob:async()=>new Blob(['RIFFfake'],{type:'audio/wav'})};
   }
   else if(url==='/api/answer'){
     submits++;assert.equal(JSON.parse(options.body).text,'Final confirmed by VoiceStudio');
     data={id:'q102',kind:'code',phase:'coding',phase_label:'Coding',question:'Implement a heap'};
   }
   else data={};
   return {ok:true,json:async()=>data};
 }
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../skills/ai-interview/scripts/studio_web/app.js'),'utf8'),ctx);
(async()=>{
 await new Promise(setImmediate);
 assert.equal(microphoneOpens,0);
 assert.equal(global.wsOpens,0);
 assert.equal(n('speech-engine').value,'builtin');
 assert.equal(n('voice-profile').children.length,2,'discovered voice profiles are exposed');
 n('speech-engine').value='voicestudio';await n('speech-engine').listeners.change();
 assert.equal(n('speech-engine').value,'builtin','no VoiceStudio connection without explicit external-backend approval');
 n('voicestudio-consent').checked=true;
 n('speech-engine').value='voicestudio';await n('speech-engine').listeners.change();
 n('resume').files=[{name:'resume.pdf',size:40,arrayBuffer:async()=>new Uint8Array([1]).buffer}];
 await n('resume').listeners.change();n('consent').checked=true;n('consent').listeners.change();
 await n('begin').listeners.click();
 await new Promise(resolve=>setTimeout(resolve,30));
 assert.equal(speechRequests,1);assert.equal(browserSpeeches,0);
 assert.equal(global.playedAudio,1);
 const firstRecording=n('record').onclick();
 const overlapping=n('record').onclick();
 await Promise.all([firstRecording,overlapping]);
 assert.equal(microphoneOpens,1);assert.equal(global.wsOpens,1);
 assert.equal(global.player.paused,true,'recording interrupts interviewer playback');
 global.recorder.ondataavailable({data:new Blob(['WebM CHUNK'])});
 await new Promise(resolve=>setTimeout(resolve,20));
 assert.equal(n('transcript').value,'','partials cannot become final answer');
 assert.equal(submits,0);
 n('record').onclick();await global.recorder.onstop();
 assert.equal(stopped,1);
 assert.equal(n('transcript').value,'Final confirmed by VoiceStudio');
 assert.equal(submits,0,'not auto-submitted');
 await n('submit').listeners.click();
 assert.equal(submits,1);
 assert.equal(n('code-panel').hidden,false);
 console.log('PASS: VoiceStudio mocked streaming STT, confirmed-only answer, TTS, and coding transition');
})().catch(e=>{console.error(e);process.exitCode=1});
