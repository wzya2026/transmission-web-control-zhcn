from pathlib import Path
import json,shutil,re,difflib
ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'.build'
manifest=json.loads((R/'twc-upstream-manifest.json').read_text())
up=R/manifest['extracted_root']
out=R/'twc-modern'
shutil.copytree(up/'src',out,dirs_exist_ok=True)
def edit(rel,old,new,count=1):
 p=out/rel;s=p.read_text(encoding='utf-8')
 assert old in s,'Edit target missing: '+rel+' '+old[:70]
 p.write_text(s.replace(old,new,count),encoding='utf-8',newline='\n')
for name in ['index.html','index.mobile.html']:
 p=out/name;s=p.read_text(encoding='utf-8')
 s=s.replace('<html>','<html lang="zh-CN">')
 for module in ['system','system.mobile','transmission.torrents']:
  s=s.replace('script/min/'+module+'.min.js','script/'+module+'.js')
 s,found=re.subn(r'(src="tr-web-control/script/min/transmission\.min\.js\?v=\d+"></script>)',r'\1\n<script src="tr-web-control/script/rpc-compat.js?v=20261019"></script>',s,count=1)
 assert found==1
 s=s.replace('Theme: ','主题：').replace('Language：','语言：')
 s=s.replace('v=20200914','v=20261019').replace('v=20201001','v=20261019')
 p.write_text(s,encoding='utf-8',newline='\r\n')
shutil.copyfile(R/'rpc-compat.js',out/'tr-web-control/script/rpc-compat.js')
edit('tr-web-control/config.js','defaultLang: ""','defaultLang: "zh-CN"')
edit('tr-web-control/config.js','defaultSelectNode: "actively"','defaultSelectNode: "torrent-all"')
theme_names={'Default':'默认','Gray':'灰色','Metro':'简洁','Material':'质感','Bootstrap':'经典','Black':'黑色','Metro Blue':'简洁蓝','Metro Gray':'简洁灰','Metro Green':'简洁绿','Metro Orange':'简洁橙','Metro Red':'简洁红','Cupertino':'浅色','Dark Hive':'深色','Pepper Grinder':'棕色','Sunny':'暖色','Base':'基础','UI':'更多主题'}
p=out/'tr-web-control/config.js';s=p.read_text(encoding='utf-8')
for old,new in theme_names.items():s=s.replace("text: '"+old+"'","text: '"+new+"'").replace("group: '"+old+"'","group: '"+new+"'")
p.write_text(s,encoding='utf-8',newline='\r\n')
edit('tr-web-control/script/system.js','version: "1.6.1"','version: "1.6.1-zhCN.2"')
edit('tr-web-control/script/system.js','codeupdate: "20200913"','codeupdate: "20261019"')
# Avoid the archived updater advertising the unmodified legacy release over this continuation.
edit('tr-web-control/script/system.js','checkUpdate: function (','checkUpdate: function (',count=1) if False else None
for name in ['system.js','system.mobile.js']:
 p=out/'tr-web-control/script'/name
 if p.exists():
  s=p.read_text(encoding='utf-8')
  s=re.sub(r'version:\s*"1\.6\.[^"]*"','version: "1.6.1-zhCN.2"',s,count=1)
  s=re.sub(r'codeupdate:\s*"[^"]*"','codeupdate: "20261019"',s,count=1)
  # Both clients use the same RPC compatibility layer. UI-specific old updater is read-only.
  s=re.sub(r'(checkUpdate\s*:\s*function\s*\([^)]*\)\s*\{)',r'\1\n return; // Upstream is archived; local updates are distributed as reviewed packages.\n',s)
  p.write_text(s,encoding='utf-8',newline='\r\n')
edit('tr-web-control/script/transmission.torrents.js','uploadLimit,uploadLimited"','uploadLimit,uploadLimited,sequentialDownload"')
edit('tr-web-control/script/system.js','case "downloadLimited":','case "sequentialDownload":\n\t\t\t\t\tcase "downloadLimited":')
rel='tr-web-control/template/torrent-attribute.html'
edit(rel,'<input id="downloadLimited"','<input id="sequentialDownload" type="checkbox"/><label for="sequentialDownload">按文件顺序下载（4.1+）</label><br/><input id="downloadLimited"')
edit(rel,'var input = inputs[key];','var input = inputs[key];\n if (input.id === "sequentialDownload" && !transmission.modernRpc) continue;')
# Add global sequential download and default public trackers to existing Save workflow.
rel='tr-web-control/template/dialog-system-config.html'
edit(rel,'<input id="start-added-torrents"','<input id="sequential-download" type="checkbox"/><label for="sequential-download">新任务默认按文件顺序下载（4.1+）</label><br/><input id="start-added-torrents"')
edit(rel,'// Set content',"thisDialog.find('#sequential-download').prop('checked', !!system.serverConfig['sequential-download']).prop('disabled', !transmission.modernRpc);\n thisDialog.find('#modern-default-trackers').val(system.serverConfig['default-trackers'] || '').prop('disabled', !transmission.modernRpc);\n // Set content")
edit(rel,"var configType = input.getAttribute('config-type') || 0;","var configType = input.getAttribute('config-type') || 0;\n if (input.id === 'sequential-download' && !transmission.modernRpc) continue;")
edit(rel,'// If the parameters are changed, save',"var defaultTrackers = thisDialog.find('#modern-default-trackers').val();\n if (transmission.modernRpc && defaultTrackers !== (system.serverConfig['default-trackers'] || '')) config['default-trackers'] = defaultTrackers;\n // If the parameters are changed, save")
needle='        </div>\n    </div>\n    <div data-options="region:\'south\',border:false"'
p=out/rel;s=p.read_text(encoding='utf-8')
assert needle in s
tab='''<div title="新版功能" style="padding:12px;" class="dialog">
<p>保留原作者界面，适配 Transmission 4.1。下面的设置直接保存在下载服务中。</p>
<label for="modern-default-trackers">默认公开 Tracker（仅用于公开种子）</label>
<textarea id="modern-default-trackers" config-type="1" style="width:96%;height:110px;"></textarea>
<p>每行一个地址；同组备用地址紧随主地址，不同组之间空一行。私有种子不应用此设置。</p>
<button type="button" id="modern-port-ipv4" config-type="1">检查 IPv4 端口</button>
<button type="button" id="modern-port-ipv6" config-type="1">检查 IPv6 端口</button>
<p id="modern-port-result" role="status"></p>
<p>设置完成后，点击下方“保存”。网络限制或缺少对应网络时，端口检查可能失败。</p>
</div>
'''
s=s.replace(needle,tab+needle,1)
s=s.replace('page.init();', '''page.init();
 ['ipv4','ipv6'].forEach(function(protocol){
   thisDialog.find('#modern-port-'+protocol).prop('disabled',!transmission.modernRpc).on('click',function(){
     var button=$(this);button.prop('disabled',true);thisDialog.find('#modern-port-result').text('正在检查 '+protocol.toUpperCase()+'…');
     transmission.exec({method:'port-test',arguments:{ip_protocol:protocol}},function(data){
       thisDialog.find('#modern-port-result').text(protocol.toUpperCase()+'：'+(data.result==='success'?(data.arguments['port-is-open']?'端口开放':'端口关闭或不可达'):'检查失败：'+data.result));button.prop('disabled',false);
     });
   });
 });''',1)
# This dialog defines thisDialog as the closure argument, so the additional controls share its scope.
p.write_text(s,encoding='utf-8',newline='\r\n')
# Translate remaining static UI headings without touching field IDs or protocol strings.
headings={'Basic Information':'基本设置','Network':'网络与队列','Speed':'速度限制','Other':'其他','User Interface':'界面设置','User Labels':'用户标签','User labels':'用户标签','Advanced':'高级设置','About':'关于','Label Management':'标签管理'}
for p in (out/'tr-web-control/template').glob('*.html'):
 s=p.read_text(encoding='utf-8')
 for a,b in headings.items():s=s.replace('title="'+a+'"','title="'+b+'"')
 p.write_text(s,encoding='utf-8',newline='\r\n')
official=R/'payload/share/transmission/public_html'
for p in official.rglob('*'):
 if p.is_file():
  target=out/('index.original.html' if p.name=='index.html' and p.parent==official else p.relative_to(official))
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
langfile=out/'tr-web-control/i18n/zh_CN.json'
lang=json.loads(langfile.read_text(encoding='utf-8'))
lang['toolbar']['ui-original']='官方原版'
lang['toolbar']['tip']['ui-original']='切换到官方原版界面（英文，供排错使用）'
langfile.write_text(json.dumps(lang,ensure_ascii=False,indent=2),encoding='utf-8',newline='\r\n')
shutil.copyfile(up/'LICENSE',out/'LICENSE-transmission-web-control.txt')
# Desktop layout inspired by the familiar list + lower information pane pattern.
for asset in ['desktop-ui.js','desktop-ui.css']:
 target=out/'tr-web-control'/('script' if asset.endswith('.js') else 'style')/asset
 shutil.copyfile(ROOT/'src'/asset,target)
edit('index.html','<body>','<body class="twc-desktop">')
edit('index.html','</head>','<link rel="stylesheet" href="tr-web-control/style/desktop-ui.css?v=20261019-2"/>\n<script src="tr-web-control/script/desktop-ui.js?v=20261019-2"></script>\n</head>')
edit('index.html',"href:'tr-web-control/template/torrent-attribute.html'","href:'tr-web-control/template/torrent-attribute.html?v=20261019-2'")
p=out/'index.html';s=p.read_text(encoding='utf-8').replace('?v=20261019"','?v=20261019-2"');p.write_text(s,encoding='utf-8',newline='\n')
edit('tr-web-control/script/system.js','system.getTorrentInfos(rowData.id);','system.showDesktopDetails(rowData);\n\t\t\t\t\tsystem.getTorrentInfos(rowData.id);')
edit('tr-web-control/script/system.js','\t\t}, "json");\n\n\t\t// 刷新当前页数据','\t\t\tsystem.ensureDesktopInitialSelection();\n\t\t}, "json");\n\n\t\t// 刷新当前页数据')
edit('tr-web-control/script/system.js','\t\tif (this.currentTorrentId > 0 && transmission.torrents.all[this.currentTorrentId]) {\n\t\t\tif (transmission.torrents.all[this.currentTorrentId].infoIsLoading) return;\n\t\t}\n','')
edit('tr-web-control/script/system.js','if (system.currentTorrentId == 0 || system.currentTorrentId != id) {\n\t\t\t\t\tsystem.clearTorrentAttribute();','if (system.currentTorrentId == 0 || system.currentTorrentId != id) {')
edit('tr-web-control/script/system.js','pieceCount,pieceSize"','pieceCount,pieceSize,downloadedEver,secondsDownloading,secondsSeeding,isPrivate"')
edit('tr-web-control/script/system.js','rowdata[key] = formatLongTime(stats[key]);','rowdata[key] = stats[key] > 0 ? formatLongTime(stats[key]) : "—";')
edit('tr-web-control/script/system.js','value = formatSize(value, true, "speed");','value = formatSize(value, false, "speed");')
rel='tr-web-control/template/torrent-attribute.html'
summary='''<div data-options="region:'north',border:false" class="desktop-detail-summary">
<div class="desktop-detail-heading"><strong id="desktop-detail-name">点选上方任务，查看详细信息</strong><span id="desktop-detail-status">未选择任务</span></div>
<div class="desktop-detail-metrics">
<div id="desktop-detail-progress" role="progressbar" aria-label="任务完成进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>
<span>总大小<b id="desktop-detail-size">—</b></span><span>已完成<b id="desktop-detail-completed">—</b></span>
<span>下载<b id="desktop-detail-download">—</b></span><span>上传<b id="desktop-detail-upload">—</b></span>
<span class="desktop-metric-ratio">分享率<b id="desktop-detail-ratio">—</b></span>
</div></div>
'''
edit(rel,'\t<div data-options="region:\'center\'"',summary+'\t<div data-options="region:\'center\'"')
edit(rel,"tabPosition:'left',border:0,headerWidth:105","tabPosition:'top',border:0")
more='''<tr><td class="title">累计下载</td><td><span id="torrent-attribute-value-downloadedEver"></span></td><td class="title">私有种子</td><td><span id="torrent-attribute-value-isPrivate"></span></td></tr>
<tr><td class="title">下载用时</td><td><span id="torrent-attribute-value-secondsDownloading"></span></td><td class="title">做种用时</td><td><span id="torrent-attribute-value-secondsSeeding"></span></td></tr>
'''
edit(rel,'\t\t\t\t\t<tr>\n\t\t\t\t\t\t<td colspan="4">',more+'\t\t\t\t\t<tr>\n\t\t\t\t\t\t<td colspan="4">')
langfile=out/'tr-web-control/i18n/zh_CN.json';lang=json.loads(langfile.read_text(encoding='utf-8'))
lang['title']['attribute']='任务详情 · 点选任务查看，拖动上沿调整高度'
lang['torrent']['attribute']['tabs'].update({'base':'概览','servers':'Tracker','users':'连接用户'})
langfile.write_text(json.dumps(lang,ensure_ascii=False,indent=2),encoding='utf-8',newline='\r\n')
patch=[];changed=[]
for p in out.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(out);q=up/'src'/rel
 if not q.exists() or p.read_bytes()!=q.read_bytes():
  changed.append(str(rel))
  if p.suffix in ('.js','.html','.json'):
   before=q.read_text(encoding='utf-8').splitlines(True) if q.exists() else []
   patch.extend(difflib.unified_diff(before,p.read_text(encoding='utf-8').splitlines(True),fromfile='upstream/'+str(rel),tofile='localized/'+str(rel)))
(R/'twc-changes.patch').write_text(''.join(patch),encoding='utf-8')
(R/'twc-changed-files.json').write_text(json.dumps(changed,indent=2),encoding='utf-8')
print('Updated upstream UI; changed files:',len(changed))
