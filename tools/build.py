"""Rebuild the pinned, unsigned SPK and web assets (Python >= 3.12, stdlib only)."""
from pathlib import Path,PurePosixPath
import hashlib,io,json,shutil,subprocess,sys,tarfile,urllib.request

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'.build'
LOCK=json.loads((ROOT/'sources.lock.json').read_text(encoding='utf-8'))

def download(url,path,expected):
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'transmission-web-control-zhcn-build'})
        with urllib.request.urlopen(req,timeout=120) as response:path.write_bytes(response.read())
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected:raise RuntimeError('Source SHA256 mismatch: '+path.name)
    return path

def main():
    if sys.version_info<(3,12):raise SystemExit('Python 3.12 or later is required')
    WORK.mkdir(exist_ok=True)
    original=LOCK['original_spk']
    spk=download(original['url'],WORK/original['filename'],original['sha256'])
    twc=LOCK['twc']
    archive=download(twc['archive_url'],WORK/'twc-upstream.tar.gz',twc['sha256'])
    unpack=WORK/'twc-upstream-extracted'
    with tarfile.open(archive) as t:t.extractall(unpack,filter='data')
    extracted=unpack/('transmission-web-control-'+twc['commit'])
    assert (extracted/'src/index.html').is_file()
    manifest=dict(twc,extracted_root=extracted.relative_to(WORK).as_posix())
    (WORK/'twc-upstream-manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    (WORK/'original-manifest.json').write_text(json.dumps({'url':original['url'],'sha256':original['sha256'],'size':spk.stat().st_size}),encoding='utf-8')
    with tarfile.open(spk) as t:
        payload=t.extractfile('package.tgz').read()
        (WORK/'package.tgz').write_bytes(payload)
        (WORK/'original-INFO').write_bytes(t.extractfile('INFO').read())
    # Only regular official web files are needed. Never dereference package links on the build host.
    with tarfile.open(fileobj=io.BytesIO(payload)) as t:
        for member in t:
            name=member.name.removeprefix('./')
            if not member.isfile() or not name.startswith('share/transmission/public_html/'):continue
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts:raise RuntimeError('Unsafe package member')
            target=WORK/'payload'/path
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(t.extractfile(member).read())
    shutil.copyfile(ROOT/'src/rpc-compat.js',WORK/'rpc-compat.js')
    for name in ['install-web-ui.sh','restore-web-ui.sh']:shutil.copyfile(ROOT/'tools'/name,WORK/name)
    for tool in ['build_twc.py','package_release.py']:
        subprocess.run([sys.executable,str(ROOT/'tools'/tool)],check=True)
    # The first release's reviewed and DSM-tested binaries are the expected build output.
    actual=json.loads((ROOT/'dist/build-manifest.json').read_text(encoding='utf-8'))
    expected=ROOT/'release-manifest.json'
    if expected.exists():
        reference=json.loads(expected.read_text(encoding='utf-8'))
        assert actual['spk_sha256']==reference['spk_sha256'],'Build differs from the reviewed release'
        assert actual['web_tar_sha256']==reference['web_tar_sha256'],'Web build differs from the reviewed release'
    print('Build complete; all source hashes and 16 unchanged core binaries verified.')

if __name__=='__main__':main()
