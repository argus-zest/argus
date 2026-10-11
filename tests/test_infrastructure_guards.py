"""Local template safety gates, without AWS requests or resource creation."""
from pathlib import Path

import yaml


class TemplateLoader(yaml.SafeLoader):
    pass


def intrinsic(loader, tag, node):
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    else:
        value = loader.construct_mapping(node)
    return {tag: value}


TemplateLoader.add_multi_constructor('!', intrinsic)
ROOT = Path(__file__).resolve().parents[1]


def load_template():
    return yaml.load((ROOT / 'template.yaml').read_text(), Loader=TemplateLoader)


def role_statements(template):
    for name, resource in template['Resources'].items():
        if resource['Type'] == 'AWS::IAM::Role':
            for policy in resource['Properties'].get('Policies', []):
                for statement in policy['PolicyDocument']['Statement']:
                    yield name, statement


def test_bucket_denies_insecure_application_access_without_granting_public_access():
    resources = load_template()['Resources']
    policy = resources['StorageBucketPolicy']['Properties']
    assert policy['Bucket'] == {'Ref': 'StorageBucket'}
    statements = policy['PolicyDocument']['Statement']
    assert all(statement['Effect'] == 'Deny' for statement in statements)
    deny = statements[0]
    assert deny['Principal'] == '*'
    assert deny['Action'] == 's3:*'
    assert deny['Resource'] == [
        {'GetAtt': 'StorageBucket.Arn'}, {'Sub': '${StorageBucket.Arn}/*'},
    ]
    # Exempt direct AWS service principals whose network context can be redacted.
    assert deny['Condition']['Bool'] == {
        'aws:SecureTransport': 'false', 'aws:PrincipalIsAWSService': 'false',
    }


def test_case_evidence_remains_private_encrypted_and_retained():
    resources = load_template()['Resources']
    bucket = resources['StorageBucket']
    properties = bucket['Properties']
    assert properties['BucketName'] == {'Sub': 'argus-${AWS::AccountId}-ap-southeast-2'}
    assert all(properties['PublicAccessBlockConfiguration'].values())
    assert properties['BucketEncryption']['ServerSideEncryptionConfiguration'][0][
        'ServerSideEncryptionByDefault']['SSEAlgorithm'] == 'AES256'
    assert properties['VersioningConfiguration']['Status'] == 'Enabled'
    assert 'LifecycleConfiguration' not in properties
    for name in ('StorageBucket', 'AssetsTable', 'CasesTable', 'CaseEventsTable'):
        assert resources[name]['DeletionPolicy'] == 'Retain'
        assert resources[name]['UpdateReplacePolicy'] == 'Retain'


def test_all_inference_permissions_are_for_the_single_sydney_foundation_model():
    template = load_template()
    assert template['Parameters']['NovaModelId']['AllowedValues'] == ['amazon.nova-lite-v1:0']
    statements = [statement for _, statement in role_statements(template)]
    inference = [s for s in statements if 'bedrock:InvokeModel' in s['Action']]
    assert len(inference) == 4
    assert all(s['Resource'] == [
        'arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.nova-lite-v1:0',
    ] for s in inference)


def test_production_cannot_enable_local_mocks_or_default_example_email_identities():
    template = load_template()
    assert template['Globals']['Function']['Environment']['Variables']['USE_MOCKS'] == 'false'
    assert 'Default' not in template['Parameters']['SesFrom']
    assert 'Default' not in template['Parameters']['DryRunInbox']


def test_no_execution_role_can_delete_data_or_use_unrestricted_resources():
    roles = list(role_statements(load_template()))
    assert len({name for name, _ in roles}) == 15
    for name, statement in roles:
        assert statement['Effect'] == 'Allow'
        assert all('*' not in action for action in statement['Action'])
        assert not any('Delete' in action or 'Replication' in action for action in statement['Action'])
        if statement['Resource'] == '*':
            assert name == 'ClaimFixFunctionRole'
            assert set(statement['Action']) == {'states:SendTaskSuccess', 'states:SendTaskFailure'}
            assert statement['Condition']['StringEquals']['aws:RequestedRegion'] == 'ap-southeast-2'


def test_email_permissions_require_only_the_configured_sender_and_dry_run_recipients():
    emails = [(name, s) for name, s in role_statements(load_template()) if 'ses:SendEmail' in s['Action']]
    assert len(emails) == 1
    name, statement = emails[0]
    assert name == 'NoticeAgentFunctionRole'
    assert statement['Resource'] == [
        {'Fn::Sub': 'arn:aws:ses:ap-southeast-2:${AWS::AccountId}:identity/${SesFrom}'},
    ]
    assert statement['Condition'] == {
        'StringEquals': {'ses:FromAddress': {'Ref': 'SesFrom'}},
        'ForAllValues:StringEquals': {'ses:Recipients': [{'Ref': 'DryRunInbox'}]},
        'Null': {'ses:Recipients': 'false'},
    }


def test_presign_and_case_evidence_access_cannot_reach_other_bucket_prefixes():
    roles = list(role_statements(load_template()))
    for name, expected in [('PresignFunctionRole', 's3:PutObject'),
                           ('CasesFunctionRole', 's3:GetObject')]:
        s3 = [s for role, s in roles if role == name and any(a.startswith('s3:') for a in s['Action'])]
        assert len(s3) == 1
        assert s3[0]['Action'] == [expected]
        assert s3[0]['Resource'] == [{'Fn::Sub': '${StorageBucket.Arn}/uploads/*'}]


def test_workflow_role_only_invokes_its_three_functions_and_has_a_source_boundary():
    resource = load_template()['Resources']['EscalationStateMachineRole']['Properties']
    trust = resource['AssumeRolePolicyDocument']['Statement'][0]
    assert trust['Principal'] == {'Service': 'states.amazonaws.com'}
    assert trust['Condition']['StringEquals']['aws:SourceAccount'] == {'Ref': 'AWS::AccountId'}
    assert trust['Condition']['ArnLike']['aws:SourceArn'] == {
        'Fn::Sub': 'arn:aws:states:ap-southeast-2:${AWS::AccountId}:stateMachine:EscalationStateMachine-*',
    }
    statements = resource['Policies'][0]['PolicyDocument']['Statement']
    assert len(statements) == 1
    assert statements[0]['Action'] == ['lambda:InvokeFunction']
    assert statements[0]['Resource'] == [
        {'Fn::GetAtt': [name, 'Arn']}
        for name in ('NoticeAgentFunction', 'RegisterTokenFunction', 'MarkClosedFunction')
    ]


def test_api_and_bucket_cors_allow_exact_local_and_amplify_origins_once():
    template = load_template()
    resources = template['Resources']
    api = resources['HttpApi']['Properties']['CorsConfiguration']['AllowOrigins']
    bucket = resources['StorageBucket']['Properties']['CorsConfiguration']['CorsRules'][0]['AllowedOrigins']
    expected = [
        'http://localhost:5173',
        'https://demo.d1ygq6l84twsei.amplifyapp.com',
    ]
    assert api == expected
    assert bucket == expected
    assert len(api) == len(set(api))
    assert len(bucket) == len(set(bucket))
    assert 'FrontendOrigin' not in template['Parameters']
