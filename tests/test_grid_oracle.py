"""Tests for GridOracle contract.

Run with: pytest tests/test_grid_oracle.py -v
Requires: pip install genlayer-test
"""
import json
import pytest


def test_update_zone_gb(direct_vm, direct_deploy, direct_alice):
    """GridOracle fetches UK Carbon Intensity data and stores it."""
    contract = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice

    # Mock the UK Carbon Intensity API
    direct_vm.mock_web(
        r".*api\.carbonintensity\.org\.uk/intensity.*",
        {
            "status": 200,
            "body": json.dumps({
                "data": [{
                    "from": "2026-03-23T12:00Z",
                    "to": "2026-03-23T12:30Z",
                    "intensity": {
                        "forecast": 266,
                        "actual": 263,
                        "index": "moderate"
                    }
                }]
            })
        },
    )

    contract.update_zone_gb()
    zone_data = json.loads(contract.get_zone_data())
    assert zone_data["GB"]["carbon"] == 263
    assert zone_data["GB"]["index"] == "moderate"
    direct_vm.clear_mocks()


def test_update_zone_windfall(direct_vm, direct_deploy, direct_alice):
    """GridOracle fetches Windfall energy data and stores it."""
    contract = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice

    # Mock the Windfall energy endpoint
    direct_vm.mock_web(
        r".*windfall\.ecofrontiers\.xyz/v1/energy.*",
        {
            "status": 200,
            "body": json.dumps({
                "nodes": [
                    {"zone": "FI", "carbonIntensity": 45, "renewablePercentage": 82},
                    {"zone": "DE", "carbonIntensity": 302, "renewablePercentage": 55},
                ]
            })
        },
    )

    contract.update_zone_windfall("FI")
    zone_data = json.loads(contract.get_zone_data())
    assert zone_data["FI"]["carbon"] == 45
    assert zone_data["FI"]["renewable"] == 82
    direct_vm.clear_mocks()


def test_update_zone_hardcoded(direct_vm, direct_deploy, direct_alice):
    """GridOracle accepts hardcoded data as fallback."""
    contract = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice

    contract.update_zone_hardcoded("DE", 302, 55)
    zone_data = json.loads(contract.get_zone_data())
    assert zone_data["DE"]["carbon"] == 302
    assert zone_data["DE"]["renewable"] == 55


def test_get_zone_single(direct_vm, direct_deploy, direct_alice):
    """GridOracle returns single zone data."""
    contract = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice

    contract.update_zone_hardcoded("GB", 263, 40)
    zone = json.loads(contract.get_zone("GB"))
    assert zone["zone"] == "GB"
    assert zone["carbon"] == 263


def test_empty_zones_return_zero(direct_vm, direct_deploy, direct_alice):
    """Zones with no data return zeroes, not errors."""
    contract = direct_deploy("contracts/grid_oracle.py")
    direct_vm.sender = direct_alice

    zone_data = json.loads(contract.get_zone_data())
    assert zone_data["GB"]["carbon"] == 0
    assert zone_data["FI"]["carbon"] == 0
    assert zone_data["DE"]["carbon"] == 0
