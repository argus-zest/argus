import sys,json,re,subprocess,concurrent.futures
from pathlib import Path
sys.path.insert(0,'tests')
from test_infrastructure_guards import load_template
root=Path.cwd();out=root/'.cache/iam-review';out.mkdir(exist_ok=True)
t=load_template();account='262952461520';region='ap-southeast-2';bucket='argus-'+account+'-'+region
refs={'AWS::AccountId':account,'AWS::StackName':'argus','AWS::Region':region,'SesFrom':'chauhanansh1046@gmail.com','DryRunInbox':'chauhanansh1046@gmail.com','EscalationStateMachine':f'arn:aws:states:{region}:{account}:stateMachine:argus-EscalationStateMachine-CHECK'}
for n in ['AssetsTable','CasesTable','CaseEventsTable']:
 table={'AssetsTable':'Assets','CasesTable':'Cases','CaseEventsTable':'CaseEvents'}[n];refs[n+'.Arn']=f'arn:aws:dynamodb:{region}:{account}:table/argus-{table}'
refs['StorageBucket.Arn']='arn:aws:s3:::'+bucket
for n,v in t['Resources'].items():
 if v['Type']=='AWS::Serverless::Function':refs[n+'.Arn']=f'arn:aws:lambda:{region}:{account}:function:argus-{n}-CHECK'
def resolve(x):
 if isinstance(x,list):return [resolve(v) for v in x]
 if not isinstance(x,dict):return x
 if 'Ref' in x:return refs[x['Ref']]
 for key in ['Sub','Fn::Sub']:
  if key in x:return re.sub(r'\$\{([^}]+)\}',lambda m:refs[m[1]],x[key])
 for key in ['GetAtt','Fn::GetAtt']:
  if key in x:return refs[x[key] if isinstance(x[key],str) else '.'.join(x[key])]
 return {k:resolve(v) for k,v in x.items()}
policies={}
for name,v in t['Resources'].items():
 if v['Type']=='AWS::IAM::Role':
  policies[name]=resolve(v['Properties']['Policies'][0]['PolicyDocument']);(out/(name+'.json')).write_text(json.dumps(policies[name],indent=2))
if '--materialize-only' in sys.argv:
    print('Materialized', len(policies), 'proposed policies; no AWS requests')
    raise SystemExit(0)
def validate(name):
 r=subprocess.run(['aws','accessanalyzer','validate-policy','--policy-document','file://'+str(out/(name+'.json')),'--policy-type','IDENTITY_POLICY','--profile','hackathon','--region',region,'--output','json'],capture_output=True,text=True,timeout=40)
 return name,{'error':r.stderr.strip()} if r.returncode else json.loads(r.stdout)
results={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for name,result in pool.map(validate,policies):results[name]=result;print(name, result.get('error') or [(f['findingType'],f['issueCode']) for f in result.get('findings',[])])
(out/'validation-results.json').write_text(json.dumps(results,indent=2))

if any('error' in r or r.get('findings') for r in results.values()):
    raise SystemExit(1)
