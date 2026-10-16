// Simulated DOM/media bridge tests. No real microphone or transcription model.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {disabled:true,value:id==='language'?'auto':'',textContent:'',classList:{toggle(){}},focus(){},select(){}});
  return elements.get(id);
}
let opens=0, stops=0, transcribes=0, saves=0, instance, fail=false, lastHeader;
let question={question_id:'q1',text:'为什么用这个算法？'};
class Recorder {
  static isTypeSupported(){return true;}
  constructor(){this.state='inactive';this.mimeType='audio/webm';instance=this;}
  start(){this.state='recording';}
  stop(){this.state='inactive';}
}
const context={
  document:{getElementById:element},location:{hash:'#token=fixture',pathname:'/'},history:{replaceState(){}},URLSearchParams,Blob,
  MediaRecorder:Recorder,
  navigator:{mediaDevices:{async getUserMedia(){opens++;return {getTracks:()=>[{stop(){stops++;}}]};}},clipboard:{async writeText(){}}},
  window:{isSecureContext:true,MediaRecorder:Recorder,addEventListener(){},confirm(){return true;}},
  performance:{now:()=>0},setInterval:()=>1,clearInterval(){},
  async fetch(url,options={}) {
    if(fail) throw new Error('fixture disconnect');
    let data;
    if(url==='/api/health') data={agent_mode:true,max_seconds:180,max_audio_bytes:20971520,model:'FAKE',output_dir:'private'};
    else if(url==='/api/question') data={question,stopped:false};
    else if(url.startsWith('/api/transcribe')){transcribes++;lastHeader=options.headers['X-Question-ID'];data={question_id:lastHeader,raw_text:'这是草稿',draft_id:'d1'};}
    else if(url==='/api/save'){saves++;data={question_id:question.question_id,revision:1,text_path:'private/answer.txt'};}
    return {ok:true,async json(){return data;}};
  }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../skills/ai-interview/scripts/web/app.js'),'utf8'),context);
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(opens,0);
  assert.equal(element('question').textContent,'为什么用这个算法？');
  assert.equal(element('start').disabled,false);
  await element('start').onclick();
  instance.ondataavailable({data:new Blob(['fixture'])});
  element('stop').onclick();await instance.onstop();
  assert.equal(stops,1);assert.equal(transcribes,1);assert.equal(lastHeader,'q1');
  assert.equal(saves,0,'transcription is not confirmation');
  element('text').value='这是我确认后的答案';await element('save').onclick();
  assert.equal(saves,1);assert.match(element('receipt').textContent,/q1/);
  question={question_id:'q2',text:'边界条件呢？'};await vm.runInContext('refreshQuestion()',context);
  assert.equal(element('text').value,'');assert.equal(element('question-id').textContent,'q2');
  await element('start').onclick();
  fail=true;await vm.runInContext('refreshQuestion()',context);
  assert.equal(instance.state,'inactive');assert.equal(stops,2);
  await instance.onstop();
  assert.equal(transcribes,1,'disconnect cancels rather than submits audio');
  assert.equal(element('start').disabled,true);
  console.log('PASS: 15 simulated bridge/UI assertions (not real browser/ASR)');
})().catch(e=>{console.error(e);process.exitCode=1;});
