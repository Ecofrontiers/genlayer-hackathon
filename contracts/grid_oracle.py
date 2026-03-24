# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class GridOracle(gl.Contract):
    """Decentralized energy data oracle for spatial inference routing.
    Fetches live carbon intensity and renewable % from multiple sources,
    reaches consensus via Optimistic Democracy with 5% tolerance."""

    owner: Address
    zone_carbon: TreeMap[str, u32]       # gCO2/kWh
    zone_renewable: TreeMap[str, u32]    # renewable %
    zone_intensity_index: TreeMap[str, str]  # "very low" / "low" / "moderate" / "high" / "very high"

    def _get_zones(self):
        return ["FI", "DE", "US", "GB"]

    def _only_owner(self):
        assert gl.message.sender_account == self.owner, "Only owner can call this"

    @gl.public.write
    def set_owner(self):
        """Set owner on first call (no constructor args on studionet)."""
        if self.owner == Address(b'\x00' * 20):
            self.owner = gl.message.sender_account
        else:
            assert gl.message.sender_account == self.owner, "Owner already set"

    @gl.public.write
    def update_zone_gb(self):
        """Update Great Britain zone from UK Carbon Intensity API (no auth, no rate limit)."""
        api_url = "https://api.carbonintensity.org.uk/intensity"

        def leader_fn():
            response = gl.nondet.web.get(api_url)
            data = json.loads(response.body.decode("utf-8"))
            entry = data["data"][0]
            return {
                "carbon": entry["intensity"]["actual"] if entry["intensity"]["actual"] is not None else entry["intensity"]["forecast"],
                "index": entry["intensity"]["index"],
                "zone": "GB"
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            my_response = gl.nondet.web.get(api_url)
            my_data = json.loads(my_response.body.decode("utf-8"))
            my_entry = my_data["data"][0]
            my_carbon = my_entry["intensity"]["actual"] if my_entry["intensity"]["actual"] is not None else my_entry["intensity"]["forecast"]
            leader_carbon = leader_result.calldata["carbon"]
            if leader_carbon == 0:
                return my_carbon == 0
            return abs(leader_carbon - my_carbon) / abs(leader_carbon) <= 0.05

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.zone_carbon["GB"] = u32(result["carbon"])
        self.zone_intensity_index["GB"] = result["index"]
        # UK API doesn't provide renewable %, estimate from intensity index
        index_to_renewable = {"very low": 85, "low": 65, "moderate": 45, "high": 25, "very high": 10}
        self.zone_renewable["GB"] = u32(index_to_renewable.get(result["index"], 40))

    @gl.public.write
    def update_zone_windfall(self, zone_id: str):
        """Update any zone from Windfall energy endpoint (no auth, no rate limit).
        Windfall returns multi-zone data from its energy oracle."""
        api_url = "https://windfall.ecofrontiers.xyz/v1/energy"

        def leader_fn():
            response = gl.nondet.web.get(api_url)
            data = json.loads(response.body.decode("utf-8"))
            # Find the requested zone in Windfall's response
            for node in data.get("nodes", []):
                if node.get("zone") == zone_id:
                    return {
                        "carbon": int(node.get("carbonIntensity", 0)),
                        "renewable": int(node.get("renewablePercentage", 0)),
                        "zone": zone_id
                    }
            # Zone not found in Windfall data — return zeros
            return {"carbon": 0, "renewable": 0, "zone": zone_id}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            my_response = gl.nondet.web.get(api_url)
            my_data = json.loads(my_response.body.decode("utf-8"))
            for node in my_data.get("nodes", []):
                if node.get("zone") == leader_result.calldata["zone"]:
                    my_carbon = int(node.get("carbonIntensity", 0))
                    leader_carbon = leader_result.calldata["carbon"]
                    if leader_carbon == 0:
                        return my_carbon == 0
                    return abs(leader_carbon - my_carbon) / abs(leader_carbon) <= 0.05
            # Zone not found — accept if leader also returned 0
            return leader_result.calldata["carbon"] == 0

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.zone_carbon[zone_id] = u32(result["carbon"])
        self.zone_renewable[zone_id] = u32(result["renewable"])

    @gl.public.write
    def update_zone_hardcoded(self, zone_id: str, carbon: u32, renewable: u32):
        """Fallback: manually set zone data for demo reliability.
        Use when APIs are unavailable or rate-limited during consensus."""
        self._only_owner()
        self.zone_carbon[zone_id] = carbon
        self.zone_renewable[zone_id] = renewable

    @gl.public.view
    def get_zone_data(self) -> str:
        """Returns JSON string of all zone data. Called by SpatialRouter."""
        zones = {}
        for zone_id in self._get_zones():
            zones[zone_id] = {
                "carbon": int(self.zone_carbon.get(zone_id, u32(0))),
                "renewable": int(self.zone_renewable.get(zone_id, u32(0))),
                "index": self.zone_intensity_index.get(zone_id, "unknown")
            }
        return json.dumps(zones)

    @gl.public.view
    def get_zone(self, zone_id: str) -> str:
        """Returns JSON string of a single zone's data."""
        return json.dumps({
            "zone": zone_id,
            "carbon": int(self.zone_carbon.get(zone_id, u32(0))),
            "renewable": int(self.zone_renewable.get(zone_id, u32(0))),
            "index": self.zone_intensity_index.get(zone_id, "unknown")
        })
