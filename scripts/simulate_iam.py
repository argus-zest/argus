import json,subprocess
from pathlib import Path
account='262952461520';region='ap-southeast-2';bucket='argus-'+account+'-'+region
base=Path('.cache/iam-review');sender='chauhanansh1046@gmail.com'
context=lambda k,v,t='string':{'ContextKeyName':k,'ContextKeyValues':v if isinstance(v,list) else [v],'ContextKeyType':t}
mail=[context('ses:FromAddress',sender),context('ses:Recipients',[sender],'stringList')]
sesarn=f'arn:aws:ses:{region}:{account}:identity/{sender}'
checks=[
 ('mail-selected','NoticeAgentFunctionRole','ses:SendEmail',sesarn,mail,'allowed'),
 ('mail-external-recipient','NoticeAgentFunctionRole','ses:SendEmail',sesarn,[mail[0],context('ses:Recipients',[sender,'external@test.invalid'],'stringList')],'implicitDeny'),
 ('mail-missing-recipient','NoticeAgentFunctionRole','ses:SendEmail',sesarn,[mail[0]],'implicitDeny'),
 ('mail-other-sender','NoticeAgentFunctionRole','ses:SendEmail',sesarn,[context('ses:FromAddress','other@test.invalid'),mail[1]],'implicitDeny'),
 ('upload-put','PresignFunctionRole','s3:PutObject',f'arn:aws:s3:::{bucket}/uploads/test.jpg',[],'allowed'),
 ('upload-tender-denied','PresignFunctionRole','s3:PutObject',f'arn:aws:s3:::{bucket}/tenders/test.txt',[],'implicitDeny'),
 ('case-photo-read','CasesFunctionRole','s3:GetObject',f'arn:aws:s3:::{bucket}/uploads/test.jpg',[],'allowed'),
 ('case-eval-denied','CasesFunctionRole','s3:GetObject',f'arn:aws:s3:::{bucket}/eval/test.json',[],'implicitDeny'),
 ('nova-only','AnalyzeFunctionRole','bedrock:InvokeModel',f'arn:aws:bedrock:{region}::foundation-model/amazon.nova-lite-v1:0',[],'allowed'),
 ('nova-other-model-denied','AnalyzeFunctionRole','bedrock:InvokeModel',f'arn:aws:bedrock:{region}::foundation-model/amazon.nova-pro-v1:0',[],'implicitDeny'),
 ('case-update','CasesFunctionRole','dynamodb:UpdateItem',f'arn:aws:dynamodb:{region}:{account}:table/argus-Cases',[],'allowed'),
 ('case-assets-denied','CasesFunctionRole','dynamodb:UpdateItem',f'arn:aws:dynamodb:{region}:{account}:table/argus-Assets',[],'implicitDeny'),
 ('health-own-logs','HealthFunctionRole','logs:PutLogEvents',f'arn:aws:logs:{region}:{account}:log-group:/aws/lambda/argus-HealthFunction-CHECK:log-stream:CHECK',[],'allowed'),
 ('health-other-logs-denied','HealthFunctionRole','logs:PutLogEvents',f'arn:aws:logs:{region}:{account}:log-group:/aws/lambda/other-project:log-stream:CHECK',[],'implicitDeny'),
 ('workflow-notice','EscalationStateMachineRole','lambda:InvokeFunction',f'arn:aws:lambda:{region}:{account}:function:argus-NoticeAgentFunction-CHECK',[],'allowed'),
 ('workflow-analyze-denied','EscalationStateMachineRole','lambda:InvokeFunction',f'arn:aws:lambda:{region}:{account}:function:argus-AnalyzeFunction-CHECK',[],'implicitDeny'),
]
results=[]
for name,role,action,resource,entries,expected in checks:
 args=['aws','iam','simulate-custom-policy','--policy-input-list',(base/(role+'.json')).read_text(),'--action-names',action,'--resource-arns',resource,'--profile','hackathon','--region',region,'--output','json']
 if entries:args+=['--context-entries',json.dumps(entries)]
 r=subprocess.run(args,capture_output=True,text=True,timeout=30)
 if r.returncode:
  results.append({'name':name,'error':r.stderr.strip()});print(name,'ERROR',r.stderr.strip());break
 actual=json.loads(r.stdout)['EvaluationResults'][0]['EvalDecision'];print(name,actual);results.append({'name':name,'actual':actual,'expected':expected})
(base/'simulation-results.json').write_text(json.dumps(results,indent=2))

if len(results) != len(checks) or any(r.get("actual") != r.get("expected") for r in results):
    raise SystemExit(1)
