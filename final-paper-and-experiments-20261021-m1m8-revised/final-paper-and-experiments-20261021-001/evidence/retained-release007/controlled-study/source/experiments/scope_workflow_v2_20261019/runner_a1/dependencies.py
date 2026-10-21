"""Read-only reuse of contained transport/identity primitives. No calls on import."""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
OLD = ROOT / 'experiments/scope_efficacy_direct_20261019'
sys.path.insert(0, str(STUDY))
import offline as battery
sys.path.insert(0, str(OLD))
import interface_probe as core
import interface_probe_v3 as compatible
import study_transport as old_transport
spec = importlib.util.spec_from_file_location('workflow_prior_identity', OLD / 'recovery_a1_20261019/identity_watchdog.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

PACK = STUDY / 'casepack-001'
MODEL, EFFORT = 'gpt-6-luna', 'low'
FREEZE_SHA = '9caf53e0c5f999754827d36b0aa337839ae5530847a6d592c6b8ec5577c96c60'


def inherited_files():
    return [Path(x.__file__).resolve() for x in
            (battery, core, compatible, old_transport, core.tr, core.watchdog, prior, prior.identity)]
