"""Build only current, approved PDF downloads. Unknown DCS status fails closed."""
from pathlib import Path
import argparse, hashlib, html, json, re, shutil, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from release_gate import eligible_releases

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://updates.digitalcombatsimulator.com/'
MAX_PDF = 80_000_000

def current_build():
    request = Request(SOURCE, headers={'User-Agent': 'Project-X-Guides/1.0 (DCS version check)'})
    with urlopen(request, timeout=30) as response:
        if response.url.split('/')[2] != 'updates.digitalcombatsimulator.com':
            raise ValueError('Unexpected DCS source redirect')
        body = response.read(512_001)
    if len(body) > 512_000:
        raise ValueError('Unexpected source size')
    text = html.unescape(re.sub('<[^>]*>', ' ', body.decode('utf-8')))
    found = re.findall(r'Latest\s+stable\s+version\s+is\s+(\d+\.\d+\.\d+\.\d+)\b', text, re.I)
    if len(set(found)) != 1:
        raise ValueError('Official stable DCS build is not unambiguous')
    return found[0], hashlib.sha256(body).hexdigest()

def download_pdf(artifact, destination):
    size = artifact['bytes']
    if not 0 < size <= MAX_PDF:
        raise ValueError('PDF exceeds the publication size limit')
    request = Request(artifact['url'], headers={'User-Agent': 'Project-X-Guides/1.0'})
    with urlopen(request, timeout=60) as response:
        body = response.read(size+1)
    if len(body) != size or hashlib.sha256(body).hexdigest() != artifact['sha256']:
        raise ValueError('Downloaded PDF size or SHA-256 does not match the approval')
    if not body.startswith(b'%PDF-'):
        raise ValueError('Release asset is not a PDF')
    destination.write_bytes(body)

def build(offline_build=None):
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    source_status = 'ok'
    source_hash = None
    error = None
    try:
        if offline_build:
            source_status = 'offline-preview'
            version = offline_build
        else:
            version, source_hash = current_build()
    except Exception as exc:
        version = None
        source_status = 'unavailable'
        error = type(exc).__name__
        print('::warning::DCS build unavailable; publishing an empty download list.')
    output = ROOT/'_site'
    if output.is_symlink() or output.resolve() != ROOT.resolve()/'_site':
        raise ValueError('Unsafe output directory')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    for name in ['index.html','style.css','app.js']:
        asset=ROOT/'site'/name
        if asset.is_symlink() or not asset.is_file():
            raise ValueError('Invalid static site asset')
        shutil.copyfile(asset,output/name)
    (output/'.nojekyll').write_text('',encoding='utf-8')
    try:
        catalog = json.loads((ROOT/'catalog/releases.json').read_text(encoding='utf-8'))
        selected, excluded = eligible_releases(catalog, version if source_status == 'ok' else None, ROOT)
    except Exception as exc:
        selected, excluded = [], [{'reason': 'Invalid catalog: '+type(exc).__name__}]
        error = 'catalog-invalid'
    public = []
    for release in selected:
        folder = output/'downloads'/release['guide_id']
        folder.mkdir(parents=True)
        artifacts = []
        try:
            for a in release['artifacts']:
                download_pdf(a, folder/a['filename'])
                artifacts.append({'label':a['label'], 'filename':a['filename'], 'bytes':a['bytes'], 'sha256':a['sha256'],
                                  'download':'downloads/'+release['guide_id']+'/'+a['filename']})
        except Exception as exc:
            shutil.rmtree(folder)
            excluded.append({'id':release['guide_id'], 'version':release['version'], 'reason':'asset check failed: '+type(exc).__name__})
            continue
        public.append({'guide_id':release['guide_id'], 'title':release['title'], 'version':release['version'], 'module':release['module'],
                       'tested_at':release['verification']['tested_at'], 'artifacts':artifacts})
    state = {'schema_version':1, 'checked_at':now, 'dcs_build':version, 'source_status':source_status,
             'source_url':SOURCE, 'source_sha256':source_hash, 'guides':public,
             'in_preparation':json.loads((ROOT/'catalog/in_preparation.json').read_text(encoding='utf-8'))}
    (output/'status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'dcs_build':version,'source_status':source_status,'published':len(public),'excluded':excluded,'error':error},ensure_ascii=False))
    summary = __import__('os').environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as f:
            f.write(f'## Guide-Portal\n\nDCS: {version or "unbekannt"}\n\nVeröffentlichte Guides: {len(public)}\n\nQuellenstatus: {source_status}\n')
            for item in excluded:
                f.write('\n- '+str(item.get('id','Katalog'))+': '+str(item['reason'])+'\n')
    return state

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline-build', help='Local preview only; always suppresses public downloads')
    build(parser.parse_args().offline_build)
