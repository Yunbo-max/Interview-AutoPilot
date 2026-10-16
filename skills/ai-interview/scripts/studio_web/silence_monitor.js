'use strict';
// Pure, browser-local amplitude observer. Activated only after a candidate
// deliberately starts a microphone recording; no always-on microphone access.
(function attach(root, factory) {
  const api=factory();
  if(root)root.AIInterviewSilenceMonitor=api;
  if(typeof module==='object' && module.exports)module.exports=api;
})(typeof window!=='undefined'?window:null,function createSilenceMonitor(){
  const DEFAULT_SILENCE_MS=40000;
  const DEFAULT_RMS_THRESHOLD=0.025;

  function rmsFromBytes(samples){
    if(!samples?.length)return 0;
    let total=0;
    for(let i=0;i<samples.length;i++){
      const value=(samples[i]-128)/128;
      total+=value*value;
    }
    return Math.sqrt(total/samples.length);
  }

  class SilenceMonitor{
    constructor({startedAt,thresholdMs=DEFAULT_SILENCE_MS,rmsThreshold=DEFAULT_RMS_THRESHOLD}){
      if(!Number.isFinite(startedAt)||thresholdMs<=0||rmsThreshold<=0){
        throw new Error('Invalid microphone silence monitor config');
      }
      this.lastSpeechAt=startedAt;
      this.startedAt=startedAt;
      this.thresholdMs=thresholdMs;
      this.rmsThreshold=rmsThreshold;
      this.loudFrames=0;
      this.triggered=false;
    }
    sample(rms,now){
      if(this.triggered||!Number.isFinite(rms)||!Number.isFinite(now)||now<this.startedAt)return false;
      if(rms>=this.rmsThreshold){
        this.loudFrames++;
        if(this.loudFrames>=2)this.lastSpeechAt=now;
      }else this.loudFrames=0;
      if(now-this.lastSpeechAt>=this.thresholdMs && this.loudFrames===0){
        this.triggered=true;
        return true;
      }
      return false;
    }
  }
  return {SilenceMonitor,rmsFromBytes,DEFAULT_SILENCE_MS};
});
