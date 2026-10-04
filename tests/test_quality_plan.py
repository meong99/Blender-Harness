import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'harness'))
from quality_plan import validate,require_pass

class QualityPlanTests(unittest.TestCase):
 def setUp(self):
  self.plan={'schema_version':1,'intent':'Continuous vase, no separate parts','continuous':[{'name':'vase','objects':['Body'],'closed':True}],'separate':[],'views':[{'name':'joint','role':'joint','location':[0,-1,0],'target':[0,0,0],'type':'ORTHO','ortho_scale':1}]}
 def test_valid_and_reference_requires_comparison(self):
  validate(self.plan,0)
  with self.assertRaises(ValueError):validate(self.plan,1)
 def test_continuous_requires_closeup(self):
  self.plan['views']=[]
  with self.assertRaises(ValueError):validate(self.plan,0)
 def test_invalid_camera(self):
  self.plan['views'][0]['ortho_scale']=float('nan')
  with self.assertRaises(ValueError):validate(self.plan,0)
 def test_numeric_failure_cannot_pass(self):
  rev={'surface_reference_quality':{'passed':False}}
  with self.assertRaises(ValueError):require_pass(rev,'pass')
  require_pass(rev,'partial');require_pass(rev,'revise');require_pass({'surface_reference_quality':None},'pass')
 def test_reference_requires_provenance_and_tolerance(self):
  v=self.plan['views'][0];v.update(role='reference',reference_index=0,provenance='fixed test camera',landmarks=[{'name':'top','object':'Body','anchor':[.5,.5,1],'uv':[.5,.1],'tolerance_px':3}])
  self.plan['continuous']=[];validate(self.plan,1)
  v['landmarks'][0]['tolerance_px']=0
  with self.assertRaises(ValueError):validate(self.plan,1)

if __name__=='__main__':unittest.main()
