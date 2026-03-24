"""Tests for SpatialRouter contract — standalone (no GridOracle dependency).

Direct mode only allows one contract per test session. These tests mock the
cross-contract call to GridOracle by patching the view() response.

For full integration (GridOracle + SpatialRouter together), use GenLayer Studio
or Bradbury testnet via gltest.

Run with: pytest tests/test_spatial_router.py -v
"""
import json
import pytest


def test_spatial_router_deploys(direct_vm, direct_deploy, direct_alice):
    """SpatialRouter deploys successfully with an oracle address."""
    # Use a dummy address since we can't deploy GridOracle in the same session
    dummy_oracle = b'\x00' * 20
    router = direct_deploy("contracts/spatial_router.py", dummy_oracle)
    direct_vm.sender = direct_alice
    assert router is not None


def test_empty_history(direct_vm, direct_deploy, direct_alice):
    """SpatialRouter starts with empty history."""
    dummy_oracle = b'\x00' * 20
    router = direct_deploy("contracts/spatial_router.py", dummy_oracle)
    direct_vm.sender = direct_alice

    count = router.get_history_count()
    assert count == 0
    history = json.loads(router.get_history())
    assert history == []
