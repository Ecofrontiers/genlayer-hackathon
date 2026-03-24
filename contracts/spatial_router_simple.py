# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class SpatialRouterSimple(gl.Contract):
    """Minimal test — no constructor args, no cross-contract calls."""

    routing_history: DynArray[str]

    @gl.public.write
    def route_simple(self, preferences: str) -> str:
        # Hardcoded zone data for testing
        zone_data = {
            "FI": {"carbon": 45, "renewable": 82},
            "DE": {"carbon": 302, "renewable": 55},
            "US": {"carbon": 420, "renewable": 22}
        }

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f'Given zones {json.dumps(zone_data)} and preference "{preferences}", pick the best zone. Reply with JSON: {{"zone": "XX", "reasoning": "why"}}'
            )
            return result

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                return "zone" in data
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        routing["preferences"] = preferences
        self.routing_history.append(json.dumps(routing))
        return json.dumps(routing)

    @gl.public.view
    def get_count(self) -> u32:
        return u32(len(self.routing_history))

    @gl.public.view
    def get_history(self) -> str:
        records = []
        for r in self.routing_history:
            records.append(json.loads(r))
        return json.dumps(records)
