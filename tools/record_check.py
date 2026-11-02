"""Record successful checks weekly or on a DCS change, keeping the schedule active."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, re

root=Path(__file__).resolve().parents[1]
build=os.environ['DCS_BUILD']
digest=os.environ['SOURCE_SHA256']
assert re.fullmatch(r'\d+\.\d+\.\d+\.\d+',build)
assert re.fullmatch(r'[a-f0-9]{64}',digest)
now=datetime.now(timezone.utc)
week=now.strftime('%G-W%V')
path=root/'status/last-successful-check.json'
prior=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
if prior.get('week') != week or prior.get('dcs_build') != build:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({'week':week,'checked_at':now.isoformat(timespec='seconds'),'dcs_build':build,
        'source':'https://updates.digitalcombatsimulator.com/','source_sha256':digest},indent=2)+'\n',encoding='utf-8')
    print('New version-check receipt written.')
else:
    print('This week and DCS build are already recorded.')
