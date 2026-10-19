from pathlib import Path
import tarfile,io,gzip,copy,hashlib,json,re,zipfile,urllib.request
ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'.build'
D=ROOT/'dist';D.mkdir(exist_ok=True)
VERSION='4.1.3-3102'
STAMP=1792368000
def sha(data):return hashlib.sha256(data).hexdigest()
def tgz(entries):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w',format=tarfile.GNU_FORMAT) as t:
  for member,body in entries:t.addfile(member,io.BytesIO(body) if body is not None else None)
 return gzip.compress(b.getvalue(),compresslevel=9,mtime=0)
def regular(name,body,mode=0o644):
 m=tarfile.TarInfo(name);m.size=len(body);m.mode=mode;m.mtime=STAMP;m.uid=m.gid=0;m.uname=m.gname='root'
 return m,body
web=[]
for p in sorted((R/'twc-modern').rglob('*')):
 if p.is_file():web.append(regular(p.relative_to(R/'twc-modern').as_posix(),p.read_bytes()))
webtgz=tgz(web)
(D/'transmission-web-control-zhCN.tar.gz').write_bytes(webtgz)
(D/'web-ui.sha256').write_text(sha(webtgz)+'  transmission-web-control-zhCN.tar.gz\n',encoding='ascii')
for name in ['install-web-ui.sh','restore-web-ui.sh']: (D/name).write_bytes((R/name).read_bytes())
license_data={name:(ROOT/'licenses'/name).read_bytes() for name in ['Transmission-COPYING.txt','SynoCommunity-LICENSE.txt']}
entries=[];original_binary_hashes={}
with tarfile.open(R/'package.tgz') as old:
 for m in old:
  normalized=m.name.removeprefix('./').rstrip('/')
  if normalized=='share/transmission/public_html' or normalized.startswith('share/transmission/public_html/'):continue
  data=old.extractfile(m).read() if m.isfile() else None
  entries.append((copy.copy(m),data))
  if m.isfile() and (normalized.startswith('bin/') or normalized.startswith('lib/')):original_binary_hashes[m.name]=sha(data)
for m,data in web:
 m=copy.copy(m);m.name='share/transmission/public_html/'+m.name;entries.append((m,data))
for name,body in license_data.items():entries.append(regular('share/transmission/licenses/'+name,body))
payload=tgz(entries)
replacements={
'Basic configuration':'基本设置',
'Please select a shared folder for storing downloads. If this folder doesn\'t exist at the time of installation, it will be created.':'请选择保存下载文件的共享文件夹。该文件夹不存在时，安装程序将创建它。',
'Shared folder':'下载共享文件夹','Subdirectories are not supported.':'这里只填写共享文件夹名称，不填写子目录或完整路径。',
'Web interface username. Defaults to admin':'设置网页界面的登录用户名；留空时使用原版默认值 admin。',
'Web interface password. Defaults to admin':'请设置网页界面的登录密码，不建议留空；原版留空时默认使用 admin。',
'Username':'用户名','Password':'登录密码','DSM Permissions':'文件夹权限说明',
'Please read <a target=\\"_blank\\" href=\\"https://github.com/SynoCommunity/spksrc/wiki/Permission-Management\\">Permission Management</a> for details.':'安装完成后，在“控制面板 → 共享文件夹 → 编辑 → 权限”中切换到“系统内部用户”，允许 sc-transmission 读写下载文件夹。<a target=\\"_blank\\" href=\\"https://github.com/SynoCommunity/spksrc/wiki/Permission-Management\\">原项目权限说明</a>',
'Uninstall package':'卸载套件','Keep or delete package settings.':'请选择保留或删除套件设置。',
'<b>Uninstall only.</b> Keep existing files for future re-installation.':'<b>只卸载程序。</b>保留套件配置及任务数据，以便以后重新安装。',
'<b style=\\"color: red\\">Erase all of the package data files. (Not Recoverable)</b>':'<b style=\\"color: red\\">删除全部套件配置和任务数据（无法恢复，请谨慎选择）。</b>'
}
spk=[]
with tarfile.open(R/'transmission-4.1.3-31-original-x64.spk') as old:
 for m in old:
  if m.name=='syno_signature.asc':continue
  data=old.extractfile(m).read() if m.isfile() else None
  if m.name=='package.tgz':data=payload
  elif m.name=='INFO':
   text=data.decode('utf-8');text=re.sub(r'^version=.*$',f'version="{VERSION}"',text,flags=re.M)
   text=re.sub(r'^checksum=.*$',f'checksum="{hashlib.md5(payload).hexdigest()}"',text,flags=re.M)
   text=re.sub(r'^displayname=.*$','displayname="Transmission 中文适配版"',text,flags=re.M)
   text=re.sub(r'^maintainer=.*$','maintainer="Community Chinese adaptation; upstream SynoCommunity and ronggang"',text,flags=re.M)
   text=re.sub(r'^distributor=.*$','distributor="Unofficial local Chinese build"',text,flags=re.M)
   text=re.sub(r'^changelog=.*$','changelog="新增桌面式上下分栏、横向任务详情标签及进度速度摘要；修复快速切换任务和首次列表加载；保留 4.1 JSON-RPC 适配及中文安装向导。"',text,flags=re.M)
   text+='\ndescription_chs="Transmission 中文网页适配包，保留原下载内核，基于作者归档版前端更新。非 SynoCommunity 官方发布。"\n'
   data=text.encode('utf-8')
  elif m.name.startswith('WIZARD_UIFILES/') and data:
   text=data.decode('utf-8')
   for a,b in replacements.items():text=text.replace(a,b)
   data=text.encode('utf-8')
  entry=copy.copy(m)
  if data is not None:entry.size=len(data)
  spk.append((entry,data))
filename='Transmission-4.1.3-3102-zhCN-x64-DSM7.spk'
assert len(original_binary_hashes)>=6,'No original core binary files selected for verification'
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w',format=tarfile.GNU_FORMAT) as t:
 for m,data in spk:t.addfile(m,io.BytesIO(data) if data is not None else None)
(D/filename).write_bytes(b.getvalue())
# Verify the final artifact, not just the working tree. Keep all original core executable/library bytes.
with tarfile.open(D/filename) as t:
 info=t.extractfile('INFO').read().decode();assert 'geminilake' in info and 'epyc7002' in info
 body=t.extractfile('package.tgz').read();assert hashlib.md5(body).hexdigest() in info
 assert 'syno_signature.asc' not in t.getnames()
 with tarfile.open(fileobj=io.BytesIO(body)) as files:
  for name,digest in original_binary_hashes.items():assert sha(files.extractfile(name).read())==digest,name
  assert b'rpc-compat.js' in files.extractfile('share/transmission/public_html/index.html').read()
  assert '基本设置' in t.extractfile('WIZARD_UIFILES/install_uifile.sh').read().decode()
manifest={'version':VERSION,'web_version':'1.6.1-zhCN.2','upstream_spk_sha256':json.loads((R/'original-manifest.json').read_text())['sha256'],'source_commit':json.loads((R/'twc-upstream-manifest.json').read_text())['commit'],'spk':filename,'spk_sha256':sha(b.getvalue()),'payload_md5':hashlib.md5(payload).hexdigest(),'preserved_core_files':original_binary_hashes,'web_tar_sha256':sha(webtgz),'dsm_minimum':'7.1-42661','signature':'unsigned custom package; not an official SynoCommunity release'}
(D/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'spk':filename,'bytes':len(b.getvalue()),'sha256':sha(b.getvalue()),'original_core_files_verified_unchanged':len(original_binary_hashes)},ensure_ascii=True),flush=True)
