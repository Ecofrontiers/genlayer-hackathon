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
        return ["FI", "DE", "US"]

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
    def update_zone_de(self):
        """Update Germany zone from Energy-Charts API (free, no auth).
        Returns current renewable share of load for Germany."""
        api_url = "https://api.energy-charts.info/public_power?country=de&time_step=hourly"

        def leader_fn():
            response = gl.nondet.web.get(api_url)
            data = json.loads(response.body.decode("utf-8"))
            # Get the most recent hour's renewable share
            renewable_shares = data.get("Renewable share of load", [])
            # Filter out None values from the end
            valid = [v for v in renewable_shares if v is not None]
            renewable_pct = int(valid[-1]) if valid else 55

            # Estimate carbon from renewable %
            # Germany baseline ~400 gCO2 at 0% renewable, ~50 at 100%
            carbon = max(20, int(400 - (renewable_pct * 3.5)))

            return {
                "carbon": carbon,
                "renewable": min(100, max(0, renewable_pct)),
                "zone": "DE"
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            my_response = gl.nondet.web.get(api_url)
            my_data = json.loads(my_response.body.decode("utf-8"))
            my_shares = my_data.get("Renewable share of load", [])
            my_valid = [v for v in my_shares if v is not None]
            my_renewable = int(my_valid[-1]) if my_valid else 55
            leader_renewable = leader_result.calldata["renewable"]
            # 10% tolerance on renewable share (it updates hourly)
            if leader_renewable == 0:
                return my_renewable == 0
            return abs(leader_renewable - my_renewable) / abs(leader_renewable) <= 0.10

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.zone_carbon["DE"] = u32(result["carbon"])
        self.zone_renewable["DE"] = u32(result["renewable"])

    @gl.public.write
    def update_all_live(self):
        """Update DE from live Energy-Charts API. FI and US use hardcoded values.
        Call this to refresh oracle with real-world data."""
        de_url = "https://api.energy-charts.info/public_power?country=de&time_step=hourly"

        def de_leader():
            response = gl.nondet.web.get(de_url)
            data = json.loads(response.body.decode("utf-8"))
            shares = data.get("Renewable share of load", [])
            valid = [v for v in shares if v is not None]
            renewable_pct = int(valid[-1]) if valid else 55
            carbon = max(20, int(400 - (renewable_pct * 3.5)))
            return {"carbon": carbon, "renewable": min(100, max(0, renewable_pct))}

        def de_validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            my_response = gl.nondet.web.get(de_url)
            my_data = json.loads(my_response.body.decode("utf-8"))
            my_shares = my_data.get("Renewable share of load", [])
            my_valid = [v for v in my_shares if v is not None]
            my_renewable = int(my_valid[-1]) if my_valid else 55
            leader_renewable = leader_result.calldata["renewable"]
            if leader_renewable == 0:
                return my_renewable == 0
            return abs(leader_renewable - my_renewable) / abs(leader_renewable) <= 0.10

        de = gl.vm.run_nondet_unsafe(de_leader, de_validator)
        self.zone_carbon["DE"] = u32(de["carbon"])
        self.zone_renewable["DE"] = u32(de["renewable"])

    @gl.public.write
    def update_zone_hardcoded(self, zone_id: str, carbon: u32, renewable: u32):
        """Fallback: manually set zone data for demo reliability."""
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
