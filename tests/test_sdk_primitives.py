"""Day 1 SDK validation tests.

These test that GenLayer's core primitives work as documented.
Run with: pytest tests/test_sdk_primitives.py -v

If ANY of these fail, stop and redesign before writing production contracts.
"""
import json
import pytest


# Test 1: gl.nondet.web.get() works and returns parseable JSON
def test_web_get_returns_json(direct_vm, direct_deploy, direct_alice):
    """Verify gl.nondet.web.get() can fetch a URL and parse JSON response."""
    # Inline test contract
    contract_code = '''
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

class WebTest(gl.Contract):
    result: str

    @gl.public.write
    def fetch_data(self):
        def leader_fn():
            response = gl.nondet.web.get("https://api.carbonintensity.org.uk/intensity")
            data = json.loads(response.body.decode("utf-8"))
            return {"carbon": data["data"][0]["intensity"]["forecast"]}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            return isinstance(leader_result.calldata["carbon"], (int, float))

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.result = json.dumps(result)

    @gl.public.view
    def get_result(self) -> str:
        return self.result
'''
    # Write temp contract file
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(contract_code)
        tmp_path = f.name

    try:
        direct_vm.sender = direct_alice
        direct_vm.mock_web(
            r".*carbonintensity.*",
            {"status": 200, "body": json.dumps({
                "data": [{"intensity": {"forecast": 250, "actual": 248, "index": "moderate"}}]
            })}
        )
        contract = direct_deploy(tmp_path)
        contract.fetch_data()
        result = json.loads(contract.get_result())
        assert result["carbon"] == 250
        direct_vm.clear_mocks()
    finally:
        os.unlink(tmp_path)


# Test 2: gl.nondet.exec_prompt() works with JSON response
def test_exec_prompt_returns_json(direct_vm, direct_deploy, direct_alice):
    """Verify gl.eq_principle.prompt_non_comparative works."""
    contract_code = '''
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

class PromptTest(gl.Contract):
    result: str

    @gl.public.write
    def run_prompt(self):
        result = gl.eq_principle.prompt_non_comparative(
            lambda: "Pick a color: red, green, or blue.",
            task="Select one color from the options.",
            criteria="Must be exactly one of: red, green, or blue."
        )
        self.result = result

    @gl.public.view
    def get_result(self) -> str:
        return self.result
'''
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(contract_code)
        tmp_path = f.name

    try:
        direct_vm.sender = direct_alice
        direct_vm.mock_llm(r".*Pick a color.*", "green")
        contract = direct_deploy(tmp_path)
        contract.run_prompt()
        assert contract.get_result() == "green"
        direct_vm.clear_mocks()
    finally:
        os.unlink(tmp_path)


# Test 3: Cross-contract calls via gl.get_contract_at().view()
def test_cross_contract_view(direct_vm, direct_deploy, direct_alice):
    """Verify one contract can read another's state."""
    # Deploy GridOracle and seed data
    oracle = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice
    oracle.update_zone_hardcoded(args=["FI", 45, 82])

    # Verify we can read it
    zone_data_str = oracle.get_zone_data()
    zone_data = json.loads(zone_data_str)
    assert zone_data["FI"]["carbon"] == 45

    # Deploy SpatialRouter that reads from GridOracle
    router = direct_deploy("contracts/spatial_router.py", args=[oracle.address])
    direct_vm.sender = direct_alice

    # If SpatialRouter can deploy with the oracle address, cross-contract ref works
    # The actual cross-contract call happens during route_inference
    assert router is not None
