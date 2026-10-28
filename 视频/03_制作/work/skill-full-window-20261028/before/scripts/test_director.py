import copy,json,tempfile,unittest
from pathlib import Path
from director import validate_plan,export_requests,resolve_assets,sha,write,ids,validate_effect,material_mix_report
class DirectorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
  n={'schema_version':'1.0','project_id':'test','brand':'ai-coach','status':'draft','title':'实操测试','scenes':[{'id':i,'narration':'看清结果与出处','intent':'核对','evidence_needed':[]} for i in ids()]};write(self.p/'n.json',n)
  self.plan={'schema_version':'1.0','project_id':'test','narration_path':str(self.p/'n.json'),'narration_sha256':sha(self.p/'n.json'),'scenes':[{'id':i,'narration':'看清结果与出处','audience_takeaway':'核对','selection_reason':'演示核对','content_description':'完整结果','framing':'含标题','timing':'口播对应','visual_type':'ai_image','image_brief':dict(claim='核对',subject='文档',action='查找',relationship='来源连接结论',composition='左右对照')} for i in ids()]}
  self.set_mix(22,13)
 def tearDown(self):self.tmp.cleanup()
 def set_mix(self,real,motion):
  for i,s in enumerate(self.plan['scenes']):
   if i<real:s.update(visual_type='real_screenshot',capture_request_id=s['id'],capture_request=dict(purpose='核对',required_events=['结果'],framing='完整区块',readability_requirements='标题可读'))
   elif i<real+motion:s.update(visual_type='motion_effect',effect={'id':'list','params':{'title':'结构测试','items':[{'label':str(k)} for k in range(3)]}})
   else:s['visual_type']='ai_image'
 def save(self):write(self.p/'v.json',self.plan);return self.p/'v.json'
 def test_35_and_immutable_narration(self):
  validate_plan(self.save());self.plan['scenes'][1]['narration']='偷偷改稿'
  with self.assertRaisesRegex(ValueError,'narration changed'):validate_plan(self.save())
 def test_no_draft_formal(self):
  with self.assertRaisesRegex(ValueError,'confirmed'):validate_plan(self.save(),True)
 def test_mix_default_and_flexible_allocation(self):
  validate_plan(self.save())
  self.assertEqual(material_mix_report(self.plan)['counts'],{'real':22,'motion':13,'ai':0})
  self.set_mix(20,15);self.plan['material_mix_rationale']='解释段较多，增加语义动态'
  validate_plan(self.save());report=material_mix_report(self.plan)
  self.assertEqual(report['counts'],{'real':20,'motion':15,'ai':0})
  self.assertEqual(len(report['notes']),1)
  self.set_mix(21,14);validate_plan(self.save())
  self.assertEqual(material_mix_report(self.plan)['counts']['ai'],0)
 def test_real_minimum_and_material_priority(self):
  self.set_mix(19,16)
  with self.assertRaisesRegex(ValueError,'at least 20'):validate_plan(self.save())
  self.set_mix(35,0)
  with self.assertRaisesRegex(ValueError,'Remotion explanation'):validate_plan(self.save())
 def test_builtin_capacity_and_open_custom_effect(self):
  with self.assertRaises(ValueError):validate_effect({'id':'list','params':{'title':'孤零零一项','items':[{'label':'x'}]}})
  e={'id':'narration-specific-flow','params':{'inputs':['evidence','method'],'progress':{'reveal':0.5}}}
  self.plan['scenes'][22]['effect']=e
  validate_plan(self.save())
  self.assertEqual(resolve_assets({'scenes':[self.plan['scenes'][22]]},None,None)['scene_23']['effect'],e)
  validate_effect({'id':'list','renderer':'custom','params':{'nodes':['a','b']}})
  for invalid in [{'id':'','params':{}},{'id':'new','params':[]},{'id':'new','renderer':'builtin','params':{}}]:
   with self.assertRaises(ValueError):validate_effect(invalid)
 def test_no_image_generation_requests(self):
  r=export_requests(self.save(),self.p/'out');self.assertEqual(r['image_requests'],0)
  self.assertFalse((self.p/'out/codex_image_manifest.json').exists())
  report=json.loads((self.p/'out/material_mix_report.json').read_text());self.assertEqual(report['counts'],{'real':22,'motion':13,'ai':0})
 def test_ai_images_rejected_and_device_surface_validated(self):
  self.plan['scenes'][22]['visual_type']='ai_image'
  with self.assertRaisesRegex(ValueError,'invalid visual type'):validate_plan(self.save())
  self.set_mix(22,13)
  for surface in ['desktop','phone']:
   self.plan['scenes'][0]['media_surface']=surface;validate_plan(self.save())
  self.plan['scenes'][0]['media_surface']='auto'
  with self.assertRaisesRegex(ValueError,'media_surface'):validate_plan(self.save())
 def test_rejected_real_asset_never_binds(self):
  s=self.plan['scenes'][0];s.update(visual_type='real_screenshot',capture_request_id='r');self.plan['scenes']=self.plan['scenes'][:1]
  a={'asset_id':'a','request_id':'r','scene_ids':[s['id']],'type':'screenshot','path':str(self.p/'actual.png'),'qa':{'status':'rejected'}}
  with self.assertRaisesRegex(ValueError,'not passed QA'):resolve_assets(self.plan,{'project_id':'test','assets':[a]},None)
 def test_source_change_requires_recheck(self):
  s=self.plan['scenes'][0];s.update(visual_type='real_screenshot',capture_request_id='r');self.plan['scenes']=[s];f=self.p/'a.png';f.write_bytes(b'changed')
  a={'request_id':'r','scene_ids':[s['id']],'type':'screenshot','path':str(f),'semantic_support':'实际内容','qa':{'status':'accepted'},'sha256':'old'}
  with self.assertRaisesRegex(ValueError,'changed after QA'):resolve_assets(self.plan,{'project_id':'test','assets':[a]},None)
 def test_two_recordings_select_explicit_asset(self):
  s=self.plan['scenes'][0];s.update(visual_type='real_recording',capture_request_id='r');self.plan['scenes']=[s]
  f=self.p/'clip.mp4';f.write_bytes(b'fixture')
  assets=[{'asset_id':k,'request_id':'r','scene_ids':[s['id']],'type':'recording','path':str(f),'semantic_support':k,'qa':{'status':'accepted'}} for k in ['start','result']]
  capture={'project_id':'test','assets':assets}
  with self.assertRaisesRegex(ValueError,'exactly one'):resolve_assets(self.plan,capture,None)
  s['capture_asset_id']='result'
  self.assertEqual(resolve_assets(self.plan,capture,None)[s['id']]['asset_id'],'result')
  s['capture_asset_id']='missing'
  with self.assertRaisesRegex(ValueError,'exactly one'):resolve_assets(self.plan,capture,None)
 def test_article_reuse_exports_only_capture_gaps(self):
  source=self.p/'original-article-screenshot.png';source.write_bytes(b'original')
  asset={'asset_id':'article-result','request_id':'scene_01','scene_ids':['scene_01'],'type':'screenshot','path':str(source),'sha256':sha(source),'semantic_support':'本期结果','qa':{'status':'accepted'},'provenance':{'source_project_id':'article','source_asset_id':'original-result'}}
  manifest=self.p/'reuse.json';write(manifest,{'project_id':'test','assets':[asset]})
  result=export_requests(self.save(),self.p/'out',manifest)
  self.assertEqual(result['capture_requests'],21);self.assertEqual(result['reused_assets'],1)
  requests=json.loads((self.p/'out/capture_request.json').read_text())['requests']
  self.assertNotIn('scene_01',[r['id'] for r in requests])
  reused=json.loads((self.p/'out/reused_capture_manifest.json').read_text())['assets'][0]
  self.assertEqual(reused,asset);self.assertEqual(source.read_bytes(),b'original')
  asset['qa']['status']='pending';write(manifest,{'project_id':'test','assets':[asset]})
  with self.assertRaisesRegex(ValueError,'not passed QA'):export_requests(self.save(),self.p/'out',manifest)
 def test_reuse_rejects_wrong_project_and_changed_original(self):
  source=self.p/'original.png';source.write_bytes(b'new')
  asset={'request_id':'scene_01','scene_ids':['scene_01'],'type':'screenshot','path':str(source),'sha256':'old','semantic_support':'本期结果','qa':{'status':'accepted'}}
  manifest=self.p/'reuse.json';write(manifest,{'project_id':'article','assets':[asset]})
  with self.assertRaisesRegex(ValueError,'mapped to this video'):export_requests(self.save(),self.p/'out',manifest)
  write(manifest,{'project_id':'test','assets':[asset]})
  with self.assertRaisesRegex(ValueError,'changed after QA'):export_requests(self.save(),self.p/'out',manifest)
if __name__=='__main__':unittest.main()
