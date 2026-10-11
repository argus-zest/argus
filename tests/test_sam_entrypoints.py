"""Import the actual deployed modules, avoiding ambiguous shared `app` aliases."""
from importlib import import_module

import pytest

from test_infrastructure_guards import load_template


FUNCTIONS = [
    (name, resource['Properties'])
    for name, resource in load_template()['Resources'].items()
    if resource['Type'] == 'AWS::Serverless::Function'
]


@pytest.mark.parametrize('name,properties', FUNCTIONS, ids=[name for name, _ in FUNCTIONS])
def test_actual_sam_entrypoint_imports_and_exists(name, properties):
    module, handler = properties['Handler'].rsplit('.', 1)
    package = properties['CodeUri'].strip('/').replace('/', '.')
    deployed_module = import_module(f'{package}.{module}')
    assert callable(getattr(deployed_module, handler))
