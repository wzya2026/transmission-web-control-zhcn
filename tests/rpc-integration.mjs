import path from 'node:path';import {fileURLToPath} from 'node:url';
import fs from'node:fs';import vm from'node:vm';import crypto from'node:crypto';import assert from'node:assert/strict';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const root=path.join(repo,'.build');const manifest=JSON.parse(fs.readFileSync(root+'/twc-upstream-manifest.json','utf8'));
if(process.env.TWC_ALLOW_MUTATING_TESTS!=='1') throw Error('Use only a disposable, empty test daemon; set TWC_ALLOW_MUTATING_TESTS=1');
const testUrl=process.env.TWC_TEST_RPC_URL;if(!testUrl)throw Error('TWC_TEST_RPC_URL is required');
if(!['127.0.0.1','localhost','[::1]'].includes(new URL(testUrl).hostname))throw Error('Test endpoint must be mapped to localhost');
const requests=[];let failNetwork;
const jq={extend:Object.assign,ajax:async function(options){
 try{
  let headers={...options.headers};if(options.contentType)headers['Content-Type']=options.contentType;
  let body=options.data;requests.push(body?JSON.parse(body):null);
  const response=await fetch(options.url,{method:options.type||'GET',headers,body,signal:AbortSignal.timeout(12000)});
  const xhr={status:response.status,getResponseHeader:name=>response.headers.get(name)};
  if(!response.ok){options.error?.(xhr,'error');return;}
  options.success?.(await response.json(),'success');
 }catch(error){failNetwork?.(error);}
}};
const ctx={jQuery:jq,console,Base64:class{encode(x){return Buffer.from(x).toString('base64')}}};ctx.window=ctx;
vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,manifest.extracted_root,'src/tr-web-control/script/transmission.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(repo,'src/rpc-compat.js'),'utf8'),ctx);
await new Promise((resolve,reject)=>{failNetwork=reject;ctx.transmission.init({rpcpath:testUrl},resolve)});
const tr=ctx.transmission;assert.equal(tr.modernRpc,true);console.log('Modern JSON-RPC negotiated:',tr.rpcVersionSemver);
async function run(method,args={}){return await new Promise((resolve,reject)=>{failNetwork=reject;tr.exec({method,arguments:args},data=>data.result==='success'?resolve(data.arguments):reject(Error(method+': '+data.result)));});}
const checks=[];function pass(name){checks.push(name);console.log('PASS',name)}
let session=await run('session-get');assert.equal(session['download-dir'],'/tmp/twc-downloads','Use a dedicated test download directory');assert.equal((await run('session-stats')).torrentCount,0,'Test daemon must be empty');assert.equal(session.version.startsWith('4.1.3'),true);assert.equal(typeof session.seedRatioLimited,'boolean');assert.equal(typeof session['cache-size-mb'],'number');pass('session fields retain original UI names and types');
let stats=await run('session-stats');assert.equal(typeof stats.activeTorrentCount,'number');assert.equal(typeof stats['current-stats'].downloadedBytes,'number');pass('statistics and nested current session fields');
let space=await run('free-space',{path:'/tmp/twc-downloads'});assert.ok(space['size-bytes']>0);pass('free space response');
function bencode(v){if(Buffer.isBuffer(v))return Buffer.concat([Buffer.from(v.length+':'),v]);if(typeof v==='string')return bencode(Buffer.from(v));if(typeof v==='number')return Buffer.from('i'+v+'e');if(Array.isArray(v))return Buffer.concat([Buffer.from('l'),...v.map(bencode),Buffer.from('e')]);return Buffer.concat([Buffer.from('d'),...Object.keys(v).sort().flatMap(k=>[bencode(k),bencode(v[k])]),Buffer.from('e')]);}
const content=Buffer.from('Isolated Chinese UI compatibility test.\n');const info={name:'中文界面适配测试.txt',length:content.length,'piece length':16384,pieces:crypto.createHash('sha1').update(content).digest()};const torrent=bencode({info});
const stale=(await run('torrent-get',{fields:['id','name']})).torrents.filter(x=>x.name===info.name);if(stale.length)await run('torrent-remove',{ids:stale.map(x=>x.id),'delete-local-data':false});
const added=await run('torrent-add',{metainfo:torrent.toString('base64'),paused:true,'download-dir':'/tmp/twc-downloads'});assert.ok(added['torrent-added']?.id);const id=added['torrent-added'].id;pass('add torrent with a Chinese filename, paused by default');
const duplicate=await run('torrent-add',{metainfo:torrent.toString('base64'),paused:true});assert.equal(duplicate['torrent-duplicate'].id,id);pass('duplicate torrent response');
let list=await run('torrent-get',{ids:[id],fields:['id','name','status','hashString','fileStats','files','wanted','downloadLimited','peer-limit','sequentialDownload','trackerList']});let item=list.torrents[0];assert.equal(item.name,info.name);assert.equal(item.hashString.length,40);assert.equal(typeof item['peer-limit'],'number');assert.equal(item.wanted[0],1);pass('torrent fields, Unicode names, file selection and peer-limit alias');
await run('torrent-set',{ids:[id],sequentialDownload:true,downloadLimited:true,downloadLimit:64,labels:['中文适配测试']});
item=(await run('torrent-get',{ids:[id],fields:['sequentialDownload','downloadLimited','downloadLimit','labels']})).torrents[0];assert.equal(item.sequentialDownload,true);assert.equal(item.downloadLimited,true);assert.equal(item.downloadLimit,64);assert.equal(item.labels[0],'中文适配测试');pass('per-torrent sequential mode, speed limit and native labels');
await run('torrent-start',{ids:[id]});await run('torrent-stop',{ids:[id]});for(let attempt=0;attempt<20;attempt++){item=(await run('torrent-get',{ids:[id],fields:['status']})).torrents[0];if(item.status===0)break;await new Promise(r=>setTimeout(r,50));}assert.equal(item.status,0);pass('start and pause operations');
list=await run('torrent-get',{ids:'recently-active',fields:['id','status']});assert.ok(Array.isArray(list.torrents));pass('recently-active identifier conversion');
await run('session-set',{'sequential-download':true,'default-trackers':'https://tracker.example.invalid/announce','cache-size-mb':8,encryption:'tolerated',seedRatioLimit:2.5});session=await run('session-get');assert.equal(session['sequential-download'],true);assert.equal(session['default-trackers'],'https://tracker.example.invalid/announce');assert.equal(session['cache-size-mb'],8);assert.equal(session.encryption,'tolerated');assert.equal(session.seedRatioLimit,2.5);pass('new global defaults, cache unit and encryption compatibility');
await run('session-set',{'default-trackers':'','sequential-download':false});
await run('torrent-verify',{ids:[id]});pass('verify local data request');
await run('torrent-remove',{ids:[id],'delete-local-data':false});pass('remove only the disposable test task');
const before=requests.length;tr.headers['X-Transmission-Session-Id']='expired-test-session';await run('session-get');assert.equal(requests.length,before+2);pass('expired CSRF session retries once');
const future=ctx.TWCCompatibility.encodeArguments({'download-dir':'C:/Private-Path/Keep-Me','labels':['Do-Not-Translate'],fields:['hashString','fileStats'],filename:'https://example.invalid/Case-Sensitive-Path'});assert.equal(future.filename,'https://example.invalid/Case-Sensitive-Path');assert.equal(future.download_dir,'C:/Private-Path/Keep-Me');assert.equal(future.labels[0],'Do-Not-Translate');pass('user paths, URLs and labels remain opaque values');
// A legacy daemon omits the new header: make sure old wire messages are still used.
tr.modernRpc=false;await run('session-get');assert.equal(requests.at(-1).method,'session-get');assert.equal(requests.at(-1).jsonrpc,undefined);pass('legacy protocol fallback');
fs.writeFileSync(root+'/rpc-test-results.json',JSON.stringify({daemon:session.version,protocol:tr.rpcVersionSemver,passed:checks.length,checks},null,2));
console.log('ALL PASSED:',checks.length);
