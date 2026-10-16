// Fake DOM/clock; tests UI decisions without microphone hardware or LLM access.
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const nodes=new Map(),intervals=[];
function n(id){if(!nodes.has(id))nodes.set(id,{id,hidden:false,disabled:false,checked:false,value:id==='language'?'zh':'',dataset:{},files:[],
  textContent:'',style:{},listeners:{},appendChild(child){(this.children??=[]).push(child)},replaceChildren(...children){this.children=children},
  addEventListener(type,fn){this.listeners[type]=fn},classList:{add(){},remove(){}},click(){}});return nodes.get(id)}
let said=[],posts=[],finished=0;
class Utterance{constructor(s){this.text=s;}}
class Opt{constructor(label,value){this.label=label;this.value=value;}}
const ctx={
 document:{getElementById:n,createElement:()=>({textContent:'',children:[],appendChild(child){this.children.push(child)}})},
 location:{hash:'#token=unit',pathname:'/'},history:{replaceState(){}},URLSearchParams,Option:Opt,Date,Math,Blob,URL,
 window:{speechSynthesis:{speaking:false,speak(u){said.push(u.text)},cancel(){}},SpeechSynthesisUtterance:Utterance,addEventListener(){},crypto:{randomUUID:()=>`uuid-${posts.length+1}`}},
 SpeechSynthesisUtterance:Utterance,performance:{now:()=>0},setInterval(fn,period){intervals.push({fn,period});return intervals.length},
 clearInterval(){},confirm:()=>true,navigator:{mediaDevices:{getUserMedia(){throw Error('unexpected microphone')}}},
 fetch:async(url,options={})=>{let data={};
   if(url==='/api/providers')data={roles:[{id:'ai_researcher',label:'AI Researcher',phases:[]}],providers:[{id:'codex',configured:true,requires:'codex'}]};
   else if(url==='/api/health')data={speech_ready:false};
   else if(url==='/api/state')data={status:'setup',timekeeper:{question_id:null,reminders:[],session_reminders:[]}};
   else if(url==='/api/jobs')data={jobs:[]};
   else if(url==='/api/voicestudio/status')data={available:false,voices:[],streaming:false};
   else if(url.startsWith('/api/evidence-summary'))data={recent_papers:0,memory_topics:0};
   else if(url==='/api/resume')data={characters:100,preview:'Resume text'};
   else if(url==='/api/start')data={id:'q1',kind:'voice',phase:'hr',phase_label:'HR',question:'Explain your contribution'};
   else if(url==='/api/skip'){posts.push({endpoint:url,body:JSON.parse(options.body)});data={id:'q2',kind:'code',phase:'coding',phase_label:'Coding',question:'Design an algorithm'};}
   else if(url==='/api/extend-question'){posts.push({endpoint:url,body:JSON.parse(options.body)});data={status:'extended',additional_seconds:60,timekeeper:{question_id:'q1',elapsed_seconds:125,recommended_seconds:360,reminders:[],session_reminders:[]}};}
   else if(url==='/api/finish'){finished++;data={status:'completed',history:[{phase:'hr',question:'Q',answer:'',response_status:'skipped',answer_elapsed_seconds:125}],reference_solutions:'No scoring for skips',timing:{turns:[{outcome:'skipped',active_seconds:125}],skipped_count:1}};}
   return {ok:true,json:async()=>data};
 }
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../skills/ai-interview/scripts/studio_web/app.js'),'utf8'),ctx);
(async()=>{
 await new Promise(setImmediate);
 n('resume').files=[{size:40,name:'cv.pdf',arrayBuffer:async()=>new Uint8Array([1]).buffer}];
 await n('resume').listeners.change();n('provider').value='codex';n('role').value='ai_researcher';
 n('consent').checked=true;n('consent').listeners.change();await n('begin').listeners.click();
 assert.equal(said.length,1,'interviewer question is spoken');
 const reminder={id:'q1:gentle',level:'gentle',at_seconds:60,message:'本题已用时1分钟，尚未提交。'};
 const state={status:'active',target_seconds:3600,elapsed_seconds:60,
   timekeeper:{question_id:'q1',elapsed_seconds:60,recommended_seconds:300,extensions_seconds:0,reminders:[reminder],session_reminders:[]}};
 ctx.updateClock(state);
 assert.match(n('question-elapsed').textContent,/01:00/);
 assert.match(n('timekeeper-note').textContent,/尚未提交/);
 assert.equal(said.length,2,'timekeeper offers one audible nudge for the first reminder');
 ctx.updateClock(state);assert.equal(said.length,2,'repeat poll does not repeat the voice reminder');
 n('transcript').value='Candidate is correcting the transcript';
 const draftReminder={...state,timekeeper:{...state.timekeeper,elapsed_seconds:120,reminders:[reminder,{id:'q1:progress',level:'progress',at_seconds:120,message:'本题已用时2分钟。'}]}};
 ctx.updateClock(draftReminder);
 assert.equal(said.length,2,'reviewing a written draft must not trigger intrusive spoken timing prompts');
 n('transcript').value='';
 vm.runInContext("context.recorder={state:'recording'}",ctx);
 const second={...state,elapsed_seconds:300,timekeeper:{...state.timekeeper,elapsed_seconds:300,reminders:[reminder,{id:'q1:progress',level:'progress',at_seconds:120,message:'本题已用时2分钟。'},{id:'q1:offer_skip',level:'offer_skip',at_seconds:300,message:'本题已用时5分钟，可选择跳过。'}]}};
 ctx.updateClock(second);assert.equal(said.length,2,'recording speech must not be interrupted by timer audio');
 vm.runInContext('context.recorder=null',ctx);
 await n('more-time').listeners.click();
 assert.equal(posts[0].endpoint,'/api/extend-question');assert.equal(posts[0].body.question_id,'q1');
 assert.match(n('question-elapsed').textContent,/06:00/,'recommended budget extends without changing overall 60m clock');
 await n('skip-question').listeners.click();
 assert.equal(posts[1].endpoint,'/api/skip');assert.equal(posts[1].body.question_id,'q1');
 assert.equal(n('code-panel').hidden,false,'skipped voice question leads to coding mode');
 const code={...second,timekeeper:{question_id:'q2',elapsed_seconds:300,recommended_seconds:900,reminders:[{id:'q2:gentle',at_seconds:300,level:'gentle',message:'Coding 5 minutes'}],session_reminders:[]}};
 ctx.updateClock(code);assert.equal(said.length,2,'coding-time reminders must remain visual only');
 ctx.renderReview(await (await ctx.fetch('/api/finish')).json());
 assert.match(n('timing-summary').textContent,/skipped|跳过/i);
 assert.match(n('review-body').children[0].children?.[0]?.textContent||'',/HR/);
 console.log('PASS: Timekeeper UI reminder once, no interruption, skip, extension, coding, review');
})().catch(e=>{console.error(e);process.exitCode=1});
