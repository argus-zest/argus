"""Regression for the live timeout that discarded escalation input."""
import json
from pathlib import Path


def test_timeout_and_rejected_closure_preserve_escalation_context():
    workflow = json.loads(
        (Path(__file__).parents[1] / "statemachine/escalation.asl.json").read_text()
    )
    catches = workflow["States"]["WaitForFix"]["Catch"]
    assert {error for catch in catches for error in catch["ErrorEquals"]} == {
        "States.Timeout", "ClosureRejected"
    }
    for catch in catches:
        assert catch["ResultPath"] == "$.wait_error"
        assert catch["Next"] == "NextRung"
        case = {"case_id": "TEST", "rung": 1, "timers": [20] * 4}
        # ASL writes a caught error at ResultPath instead of replacing root input.
        case[catch["ResultPath"].removeprefix("$.")] = {"Error": catch["ErrorEquals"][0]}
        assert case["rung"] < 4
        assert case["case_id"] == "TEST"
        assert case["timers"] == [20] * 4
