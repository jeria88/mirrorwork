
import{bundle}from'@remotion/bundler';
import{renderMedia,selectComposition}from'@remotion/renderer';
import{createRequire}from'module';
import path from'path';
import{fileURLToPath}from'url';
import fs from'fs';
const __dirname=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(import.meta.url);
const ffmpegPath=require('ffmpeg-static');
const outDir=path.join(__dirname,'..','mp4');
fs.mkdirSync(outDir,{recursive:true});
const b=await bundle({entryPoint:path.resolve(__dirname,'src/index.jsx'),webpackOverride:c=>c,enableCaching:true});
const comp=await selectComposition({serveUrl:b,id:'R1',browserExecutable:'/usr/bin/google-chrome'});
await renderMedia({composition:comp,serveUrl:b,codec:'h264',outputLocation:path.join(outDir,'R1.mp4'),ffmpegPath,browserExecutable:'/usr/bin/google-chrome',puppeteerArgs:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu'],onProgress:({progress})=>{process.stdout.write('PROGRESS:'+Math.round(progress*100)+'\n');},chromiumOptions:{disableWebSecurity:true}});
console.log('DONE');