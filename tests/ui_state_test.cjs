// Simulated DOM/media state regression test; NOT a browser or microphone test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    disabled:true, value:id==='language'?'auto':'', textContent:'',
    classList:{toggle(){}}, focus(){}, select(){}
  });
  return elements.get(id);
}
let microphoneOpens = 0, stops = 0, transcriptionCalls = 0, instance;
const track = {stop(){stops++;}};
class FakeRecorder {
  static isTypeSupported(){return true;}
  constructor(){this.state='inactive'; this.mimeType='audio/webm'; instance=this;}
  start(){this.state='recording';}
  stop(){this.state='inactive';} // Native onstop is asynchronous, deliberately not fired here.
}
const context = {
  crypto:require('node:crypto').webcrypto, document:{getElementById:element}, location:{hash:'#token=fixture',pathname:'/'},
  history:{replaceState(){}}, URLSearchParams, MediaRecorder:FakeRecorder, Blob,
  navigator:{mediaDevices:{async getUserMedia(){microphoneOpens++;return {getTracks:()=>[track]};}},
    clipboard:{async writeText(){}}},
  window:{isSecureContext:true, MediaRecorder:FakeRecorder, addEventListener(){},confirm(){return true;}},
  performance:{now:()=>0}, setInterval:()=>1, clearInterval(){},
  async fetch(url) {
    if (url.startsWith('/api/transcribe')) transcriptionCalls++;
    return {ok:true,async json(){return url==='/api/health'
      ? {max_seconds:180,max_audio_bytes:20971520,model:'fake',output_dir:'fixture'}
      : {raw_text:'fake transcript',draft_id:'fixture-draft'};}};
  }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../skills/ai-interview/scripts/web/app.js'),'utf8'), context);
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(microphoneOpens,0,'page load must not open microphone');
  await element('start').onclick();
  assert.equal(microphoneOpens,1);
  instance.ondataavailable({data:new Blob(['fixture'])});
  element('stop').onclick();
  assert.equal(stops,1,'stop releases microphone immediately');
  assert.equal(element('start').disabled,true,'must prevent another recording until asynchronous onstop completes');
  await instance.onstop();
  assert.equal(transcriptionCalls,1);
  assert.equal(element('text').value,'fake transcript');
  await element('start').onclick();
  element('cancel').onclick();
  await instance.onstop();
  assert.equal(transcriptionCalls,1,'cancel must not transcribe');
  assert.equal(stops,2);
  console.log('PASS: 8 simulated UI/media-state assertions (not real browser/ASR)');
})().catch(e=>{console.error(e);process.exitCode=1;});
