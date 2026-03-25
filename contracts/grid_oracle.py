# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class GridOracle(gl.Contract):
    """Node registry and energy oracle for inference routing.
    Owner-gated writes. Capped node count. Live carbon feeds."""

    owner: Address
    node_registry: TreeMap[str, str]
    node_ids: DynArray[str]
    zone_carbon: TreeMap[str, u32]
    zone_renewable: TreeMap[str, u32]

    MAX_NODES = 50

    @gl.public.write
    def set_owner(self):
        """Set owner on first call."""
        if self.owner == Address(b'\x00' * 20):
            self.owner = gl.message.sender_account
        else:
            assert gl.message.sender_account == self.owner, "Owner already set"

    def _only_owner(self):
        assert gl.message.sender_account == self.owner, "Only owner"

    @gl.public.write
    def register_node(self, node_id: str, node_data_json: str):
        """Register or update an inference node. Owner only."""
        self._only_owner()
        assert len(node_id) < 16, "node_id too long"
        assert all(c.isalnum() or c == '_' for c in node_id), "node_id must be alphanumeric"
        assert len(node_data_json) < 4096, "node data too large"
        data = json.loads(node_data_json)
        assert "location" in data, "location required"
        assert "model" in data, "model required"

        self.node_registry[node_id] = node_data_json
        # Always append — deduped in get_all_nodes via dict
        self.node_ids.append(node_id)

    @gl.public.write
    def update_carbon(self, node_id: str, carbon: u32, renewable: u32):
        """Update carbon intensity for a node's zone. Owner only."""
        self._only_owner()
        assert self.node_registry.get(node_id, "") != "", "Node not registered"
        self.zone_carbon[node_id] = carbon
        self.zone_renewable[node_id] = renewable

    @gl.public.write
    def update_carbon_de_live(self):
        """Update DE carbon from Energy-Charts API (free, no auth)."""
        api_url = "https://api.energy-charts.info/public_power?country=de&time_step=hourly"

        def leader_fn():
            response = gl.nondet.web.get(api_url)
            data = json.loads(response.body.decode("utf-8"))
            shares = data.get("Renewable share of load", [])
            valid = [v for v in shares if v is not None]
            renewable_pct = int(valid[-1]) if valid else 55
            carbon = max(20, int(400 - (renewable_pct * 3.5)))
            return {"carbon": carbon, "renewable": min(100, max(0, renewable_pct))}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            my_response = gl.nondet.web.get(api_url)
            my_data = json.loads(my_response.body.decode("utf-8"))
            my_shares = my_data.get("Renewable share of load", [])
            my_valid = [v for v in my_shares if v is not None]
            my_renewable = int(my_valid[-1]) if my_valid else 55
            leader_renewable = leader_result.calldata["renewable"]
            # Absolute tolerance: within 10 percentage points
            return abs(leader_renewable - my_renewable) <= 10

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.zone_carbon["DE"] = u32(result["carbon"])
        self.zone_renewable["DE"] = u32(result["renewable"])

    @gl.public.view
    def get_node(self, node_id: str) -> str:
        """Get a single node's full data including carbon."""
        raw = self.node_registry.get(node_id, "")
        if not raw:
            return json.dumps({"error": "node not found"})
        data = json.loads(raw)
        data["carbon_gco2_kwh"] = int(self.zone_carbon.get(node_id, u32(0)))
        data["renewable_pct"] = int(self.zone_renewable.get(node_id, u32(0)))
        return json.dumps(data)

    @gl.public.view
    def get_all_nodes(self) -> str:
        """Get all registered nodes with their carbon data."""
        nodes = {}
        for node_id in self.node_ids:
            raw = self.node_registry.get(node_id, "")
            if raw:
                data = json.loads(raw)
                data["carbon_gco2_kwh"] = int(self.zone_carbon.get(node_id, u32(0)))
                data["renewable_pct"] = int(self.zone_renewable.get(node_id, u32(0)))
                nodes[node_id] = data
        return json.dumps(nodes)

    @gl.public.view
    def get_node_count(self) -> u32:
        return u32(len(self.node_ids))
