"""Deployment refusal tests; fake executables never contact AWS or deploy."""
import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize('override, expected', [
    ({'AWS_REGION': 'ap-southeast-1'}, 'AWS_REGION must'),
    ({'AWS_PROFILE': 'default'}, 'AWS_PROFILE must'),
    ({'NOVA_MODEL_ID': 'global.amazon.nova-2-lite-v1:0'}, 'regional Nova Lite'),
    ({'EXPECTED_AWS_ACCOUNT_ID': '222222222222'}, 'project does not match'),
    ({'SES_VERIFIED': 'False'}, 'SES email identity must be verified'),
])
def test_deployment_refuses_invalid_target(tmp_path, override, expected):
    log = tmp_path / 'commands'
    aws = tmp_path / 'aws'
    aws.write_text('''#!/usr/bin/env bash
echo "aws $*" >> "$TEST_LOG"
case "$1 $2" in
  "sts get-caller-identity") echo 111111111111 ;;
  "sesv2 get-email-identity") echo "${SES_VERIFIED:-True}" ;;
  "bedrock get-foundation-model") echo ON_DEMAND ;;
  *) exit 99 ;;
esac
''')
    aws.chmod(0o755)
    sam = tmp_path / 'sam'
    sam.write_text('#!/usr/bin/env bash\necho "sam $*" >> "$TEST_LOG"\nexit 99\n')
    sam.chmod(0o755)
    env = dict(os.environ, PATH=f'{tmp_path}:/usr/bin:/bin', TEST_LOG=str(log),
               AWS_PROFILE='hackathon', AWS_REGION='ap-southeast-2', STACK_NAME='argus',
               NOVA_MODEL_ID='amazon.nova-lite-v1:0',
               EXPECTED_AWS_ACCOUNT_ID='111111111111',
               SES_FROM='sender@test.invalid', DRYRUN_INBOX='inbox@test.invalid')
    env.update(override)
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'deploy.sh'
    result = subprocess.run(['bash', str(script)], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert expected in result.stderr
    commands = log.read_text() if log.exists() else ''
    assert 'sam deploy' not in commands
    assert 'sam build' not in commands
