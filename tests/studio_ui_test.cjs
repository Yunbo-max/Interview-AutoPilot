// Simulated DOM/UI lifecycle, not a real browser, speaker or speech model.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const elements=new Map();
function node(id){if(!elements.has(id))elements.set(id,{
 id,disabled:false,hidden:false,value:id==='language'?'zh':'',dataset:{},files:[],checked:false,textContent:'',className:'',style:{},
 listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(...children){this.children=children;},
 appendChild(){},focus(){},classList:{add(){},remove(){}},click(){},
});return elements.get(id);}
let played=0, microphone=0, turns=0, posted=null, startPayload=null, refreshCalled=0, memorySaves=0;
class Speech {constructor(text){this.text=text;}}
class Opt {constructor(label,value){this.label=label;this.value=value;}}
const roles=[{id:'ai_researcher',label:'AI Research Scientist',phases:[{id:'hr',label:'HR',minutes:15}]}];
const providers=[{id:'codex',kind:'cli',configured:true,requires:'codex'}];
const context={
 document:{getElementById:node,createElement:name=>({textContent:'',appendChild(){}})},
 location:{hash:'#token=fake',pathname:'/'},history:{replaceState(){}},URLSearchParams,Option:Opt,
 window:{speechSynthesis:{speak(){played++;},cancel(){}},SpeechSynthesisUtterance:Speech,addEventListener(){},crypto:{randomUUID:()=>`id-${turns}`} },
 SpeechSynthesisUtterance:Speech,
 navigator:{mediaDevices:{getUserMedia(){microphone++;throw Error('must not auto record');}}},
 performance:{now:()=>0},setInterval:()=>1,clearInterval(){},confirm:()=>true,
 Blob,URL,Date,Math,
 fetch:async(url,options={})=>{
   let data;
   if(url==='/api/health')data={version:'0.3',speech_ready:false};
   else if(url==='/api/providers')data={roles,providers};
   else if(url==='/api/state')data={status:'setup',resume_loaded:false};
   else if(url==='/api/resume')data={characters:100,preview:'My resume projects'};
   else if(url==='/api/evidence-summary?role=ai_researcher')data={recent_papers:2,memory_topics:3};
   else if(url==='/api/jobs')data={jobs:[{id:'job-123',title:'Agent Engineer',company:'Example'}]};
   else if(url==='/api/trends-refresh'){refreshCalled++;data={status:'retrieved',count:5,source:'arxiv'};}
   else if(url==='/api/save-memory'){memorySaves++;data={status:'saved'};}
   else if(url==='/api/start'){startPayload=JSON.parse(options.body);turns++;data={id:'q1',kind:'voice',phase:'hr',phase_label:'HR',question:'Tell me your actual contribution.'};}
   else if(url==='/api/answer'){
     posted=JSON.parse(options.body);turns++;
     data=turns===2?{id:'q2',kind:'code',phase:'coding',phase_label:'Coding',question:'Implement a hash map solution.'}:{status:'completed'};
   }
   else if(url==='/api/finish')data={status:'completed',history:[{phase:'hr',question:'Tell me',answer:'I wrote tests',assessment:'More evidence'}],reference_solutions:'Reference code after interview'};
   return {ok:true,json:async()=>data};
 }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../skills/ai-interview/scripts/studio_web/app.js'),'utf8'),context);
(async()=>{
 await new Promise(setImmediate);
 assert.equal(microphone,0,'page load must never record');
 assert.equal(played,0,'no spontaneous speech before user starts');
 node('role').value='ai_researcher';node('provider').value='codex';
 node('resume').files=[{name:'candidate.pdf',size:80,arrayBuffer:async()=>new Uint8Array([1,2]).buffer}];
 await node('resume').listeners.change();
 node('consent').checked=true;node('consent').listeners.change();
 node('include-trends').checked=true;node('include-memory').checked=true;
 node('job-target').value='job-123';
 await node('refresh-research').listeners.click();
 assert.equal(refreshCalled,1);
 await node('begin').listeners.click();
 assert.equal(startPayload.use_trends,true);assert.equal(startPayload.use_memory,true);
 assert.equal(startPayload.job_id,'job-123');
 assert.equal(node('session').hidden,false);
 assert.equal(played,1,'noncoding question should be spoken');
 assert.equal(microphone,0,'question output must not start microphone');
 node('transcript').value='I wrote tests';
 await node('submit').listeners.click();
 assert.equal(posted.kind,'voice');
 assert.equal(node('code-panel').hidden,false,'coding should open editor');
 assert.equal(node('voice-panel').hidden,true);
 assert.equal(played,1,'code prompt is not auto-spoken');
 node('code').value='def solve(nums): return len(nums)';
 await node('submit').listeners.click();
 assert.equal(posted.kind,'code');
 assert.match(node('reference-solutions').textContent,/Reference code/);
 assert.equal(memorySaves,0,'never autosave personal interview data');
 await node('save-memory').listeners.click();
 assert.equal(memorySaves,1);
 console.log('PASS: studio UI simulated resume, consent, TTS, voice and code turn');
})().catch(e=>{console.error(e);process.exitCode=1;});
