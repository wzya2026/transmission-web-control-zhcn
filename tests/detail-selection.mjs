// Exercise the shipped detail-loading function with deliberately reordered RPC responses.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=fs.readFileSync(path.join(root,'.build/twc-modern/tr-web-control/script/system.js'),'utf8');
const start=source.indexOf('\tgetTorrentInfos: function (id) {');
const end=source.indexOf('\tclearTorrentAttribute: function',start);
assert(start>0&&end>start);
const calls=[],painted=[];let clears=0;
const torrents={1:{id:1,name:'First',totalSize:10},2:{id:2,name:'Second',totalSize:20}};
const ctx={transmission:{torrents:{all:torrents,datas:{},getMoreInfos(fields,id,callback){calls.push({fields,id,callback});}}},jQuery:{extend:Object.assign}};
vm.createContext(ctx);vm.runInContext('var system={'+source.slice(start,end)+'};',ctx);
Object.assign(ctx.system,{currentTorrentId:0,panel:{attribute:{panel(){return {collapsed:false}}}},clearTorrentAttribute(){clears++},fillTorrentBaseInfos(t){painted.push(t.id)},fillTorrentFileList(){},fillTorrentServerList(){},fillTorrentPeersList(){},fillTorrentConfig(){}});
ctx.system.getTorrentInfos(1);ctx.system.getTorrentInfos(2);
assert.deepEqual(calls.map(x=>x.id),[1,2],'Changing selection must not wait for the previous RPC');
calls[1].callback([{id:2,files:[{}],leftUntilDone:4}]);
calls[0].callback([{id:1,files:[{}],leftUntilDone:6}]);
assert.deepEqual(painted,[2],'A stale response must not replace the selected task');
assert.equal(clears,0,'A stale response must not clear a newer result');
assert.equal(ctx.system.currentTorrentId,2);
ctx.system.getTorrentInfos(2);ctx.system.getTorrentInfos(2);
assert.equal(calls.length,3,'Repeated requests for the same in-flight task are coalesced');
assert(calls[2].fields.includes('secondsSeeding'));
console.log('PASS: selection switches while a request is in flight; stale response does not clear or overwrite; duplicate requests coalesce.');
// Initial navigation must wait for both the grid and the RPC data, in either order.
const desktop=fs.readFileSync(path.join(root,'src/desktop-ui.js'),'utf8');
for(const order of ['grid-first','data-first']){
 let gridReady=order==='grid-first',selections=0;
 const app={lang:{},config:{defaultSelectNode:'all'},currentTorrentId:0,uiIsInitialized:true,desktopDetailsInitialized:true,initUIStatus(){},fillTorrentBaseInfos(){},clearTorrentAttribute(){},control:{torrentlist:{data(){return gridReady}}},panel:{left:{tree(method,key){if(method==='getSelected')return null;if(method==='find')return {target:'node-'+key};if(method==='select'){selections++;return this;}}}}};
 const w={system:app,transmission:{torrents:{all:order==='data-first'?{}:null}},jQuery:function(){}};
 vm.runInNewContext(desktop,{window:w});
 app.ensureDesktopInitialSelection();assert.equal(selections,0);
 gridReady=true;w.transmission.torrents.all={};app.initUIStatus();
 assert.equal(app.config.defaultSelectNode,'torrent-all');assert.equal(selections,1);
 app.ensureDesktopInitialSelection();assert.equal(selections,1);
}
console.log('PASS: initial task selection handles either grid/data readiness order and migrates the old all-node setting.');
