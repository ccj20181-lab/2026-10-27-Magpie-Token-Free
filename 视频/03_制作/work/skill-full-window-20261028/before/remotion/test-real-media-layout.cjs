const fs=require('fs');
const assert=require('node:assert/strict');
const vm=require('vm');
const ts=require('typescript');
const code=ts.transpileModule(fs.readFileSync(__dirname+'/src/realMediaLayout.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const box={exports:{}};vm.runInNewContext(code,box);
const {getRealMediaLayout}=box.exports;
let count=0;
for(const mediaSurface of ['desktop','phone']) {
 for(const [sourceWidth,sourceHeight] of [[1920,1080],[1080,1920],[540,240],[710,955]]) {
  for(const crop of [false,true]) {
   const sourceRect=crop?[10,20,sourceWidth-30,sourceHeight-40]:undefined;
   const {frame,rect,scale,content}=getRealMediaLayout({mediaSurface,sourceWidth,sourceHeight,sourceRect});
   assert.equal(frame.left+frame.width/2,540);
   assert.equal(frame.top+frame.height/2,1050);
   assert.equal(frame.top,510);
   assert.equal(frame.width,mediaSurface==='desktop'?1024:540);
   assert.equal(frame.padding,16);
   assert(Math.abs(content.width/content.height-rect[2]/rect[3])<1e-9);
   assert.equal(content.width,rect[2]*scale);
   assert.equal(content.height,rect[3]*scale);
   assert(content.left>=16-1e-8&&content.top>=16-1e-8);
   assert(content.left+content.width<=frame.width-16+1e-8);
   assert(content.top+content.height<=frame.height-16+1e-8);
   count++;
  }
 }
}
assert.equal(getRealMediaLayout({sourceWidth:400,sourceHeight:1600}).surface,'desktop','a tall computer crop is not a phone');
console.log(count+' desktop/phone crop and aspect-ratio cases passed; legacy default is desktop.');
