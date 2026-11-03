import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {snapshotResponse} from '../shared/gediv-gateway.mjs';

// Prévia privada nesta máquina. Não é um servidor para exposição à internet.
const root=fileURLToPath(new URL('../',import.meta.url));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
  '.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png'};
let token=process.env.GEDIV_BACKEND_TOKEN;
if(process.argv.includes('--stdin')){
 if(process.stdin.isTTY)execFileSync('stty',['-echo'],{stdio:['inherit','ignore','ignore']});
 process.stdout.write('Ready for private preview configuration on stdin.\n');
 process.stdin.setEncoding('utf8');let buffer='';
 const line=await new Promise(resolve=>{process.stdin.on('data',chunk=>{buffer+=chunk;if(buffer.includes('\n'))resolve(buffer.split('\n')[0]);});});
 const config=JSON.parse(line);token=config.token;
}
const server=http.createServer(async(req,res)=>{
 try{
  const authority='127.0.0.1:'+server.address().port;
  if(req.headers.host!==authority||req.headers['sec-fetch-site']&& !['same-origin','none'].includes(req.headers['sec-fetch-site'])||
   req.headers.origin&&req.headers.origin!=='http://'+authority){res.writeHead(403);res.end('Forbidden');return;}
  if(req.method!=='GET'){res.writeHead(405,{'Allow':'GET'});res.end();return;}
  const url=new URL(req.url,'http://'+authority);
  if(url.pathname==='/api/gediv/data'){
   const reply=await snapshotResponse({manager:true,token});
   res.writeHead(reply.status,Object.fromEntries(reply.headers));res.end(Buffer.from(await reply.arrayBuffer()));return;
  }
  let name=url.pathname==='/'?'/painel-interativo/index.html':url.pathname;
  if(name.endsWith('/'))name+='index.html';
  const allowed=/^\/(?:painel-interativo\/(?:index\.html|app\.js|data\.js|export\.js|styles\.css|logo\.png)|site\/index\.html|shared\/(?:gediv-client|dashboard-model)\.mjs)$/;
  if(!allowed.test(name)){res.writeHead(404);res.end();return;}
  const bytes=await readFile(path.join(root,name));
  res.writeHead(200,{'Content-Type':mime[path.extname(name)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(bytes);
 }catch{res.writeHead(503);res.end('Não foi possível consultar a prévia privada.');}
});
server.listen(0,'127.0.0.1',()=>console.log(JSON.stringify({preview:'http://127.0.0.1:'+server.address().port,persistentWrites:false})));
