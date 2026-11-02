from pathlib import Path
import hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_site

class Response:
    url='https://updates.digitalcombatsimulator.com/'
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,size):return self.body[:size]

class VersionTests(unittest.TestCase):
    def test_only_stable_build_not_updater(self):
        body=b'<h2>Latest stable version is <a>2.9.31.29434</a></h2><p>DCS_updater 2.17.3.11</p>'
        with patch.object(build_site,'urlopen',return_value=Response(body)):
            self.assertEqual(build_site.current_build()[0],'2.9.31.29434')
    def test_missing_or_ambiguous_source_rejected(self):
        for body in [b'DCS_updater 2.17.3.11',b'Latest stable version is 2.9.1.2 Latest stable version is 2.9.2.3']:
            with self.subTest(body=body),patch.object(build_site,'urlopen',return_value=Response(body)):
                with self.assertRaises(ValueError):build_site.current_build()

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.test-build-',dir=Path(__file__).resolve().parents[1]);self.root=Path(self.temp.name)
        for name in ['site','catalog']:(self.root/name).mkdir()
        for name in ['index.html','style.css','app.js']:(self.root/'site'/name).write_text('test',encoding='utf-8')
        (self.root/'catalog/releases.json').write_text('{"schema_version":1,"releases":[]}',encoding='utf-8')
        (self.root/'catalog/in_preparation.json').write_text('[]',encoding='utf-8')
        self.root_patch=patch.object(build_site,'ROOT',self.root);self.root_patch.start()
    def tearDown(self):self.root_patch.stop();self.temp.cleanup()
    def test_unavailable_dcs_removes_previous_downloads(self):
        previous=self.root/'_site/downloads/old.pdf';previous.parent.mkdir(parents=True);previous.write_bytes(b'%PDF-old')
        with patch.object(build_site,'current_build',side_effect=OSError('unavailable')):
            result=build_site.build()
        self.assertEqual(result['guides'],[]);self.assertEqual(result['source_status'],'unavailable');self.assertFalse(previous.exists())
    def test_offline_preview_never_publishes(self):
        with patch.object(build_site,'eligible_releases',return_value=([],[])) as gate:
            result=build_site.build('2.9.31.29434')
        self.assertIsNone(gate.call_args.args[1]);self.assertEqual(result['source_status'],'offline-preview')
    def test_stray_static_pdf_cannot_bypass_gate(self):
        (self.root/'site/draft.pdf').write_bytes(b'%PDF-unapproved')
        (self.root/'site/downloads').mkdir()
        (self.root/'site/downloads/draft.pdf').write_bytes(b'%PDF-unapproved')
        build_site.build('2.9.31.29434')
        self.assertEqual(list((self.root/'_site').rglob('*.pdf')),[])
    def test_bad_second_variant_removes_whole_guide(self):
        release={'guide_id':'hornet','title':'Hornet','module':'FA18','version':'1.0.0','verification':{'tested_at':'2026-01-01'},
                 'artifacts':[{'filename':'screen.pdf','label':'Screen','bytes':8,'sha256':'a'*64},{'filename':'print.pdf','label':'Print','bytes':8,'sha256':'b'*64}]}
        def fake_download(a,path):
            if a['filename']=='print.pdf':raise ValueError('bad hash')
            path.write_bytes(b'%PDF-ok')
        with patch.object(build_site,'current_build',return_value=('2.9.31.29434','a'*64)),patch.object(build_site,'eligible_releases',return_value=([release],[])),patch.object(build_site,'download_pdf',side_effect=fake_download):
            result=build_site.build()
        self.assertEqual(result['guides'],[]);self.assertFalse((self.root/'_site/downloads/hornet').exists())
    def test_bad_pdf_bytes_rejected(self):
        body=b'%PDF-mismatch';a={'url':'https://github.com/Wattl/Project-X-Guides/releases/download/test/file.pdf','bytes':len(body),'sha256':'a'*64}
        with patch.object(build_site,'urlopen',return_value=Response(body)):
            with self.assertRaises(ValueError):build_site.download_pdf(a,self.root/'file.pdf')
        self.assertFalse((self.root/'file.pdf').exists())
    def test_approved_pdf_copy_is_byte_identical(self):
        body=b'%PDF-1.7\nverified-test-fixture';a={'url':'https://github.com/Wattl/Project-X-Guides/releases/download/test/file.pdf','bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        with patch.object(build_site,'urlopen',return_value=Response(body)):build_site.download_pdf(a,self.root/'file.pdf')
        self.assertEqual((self.root/'file.pdf').read_bytes(),body)

if __name__=='__main__':unittest.main()
