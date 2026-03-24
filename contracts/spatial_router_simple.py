# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class SpatialRouterSimple(gl.Contract):
    """LLM-powered subjective routing with genuine validator re-reasoning.
    Validators independently assess whether the leader's routing choice is
    defensible — not just structurally valid. This is real subjective consensus."""

    owner: Address
    routing_history: DynArray[str]

    VALID_ZONES = {"FI", "DE", "US"}

    @gl.public.write
    def set_owner(self):
        """Set owner on first call."""
        if self.owner == Address(b'\x00' * 20):
            self.owner = gl.message.sender_account
        else:
            assert gl.message.sender_account == self.owner, "Owner already set"

    @gl.public.write
    def route_simple(self, preferences: str) -> str:
        assert len(preferences) < 1000, "Preferences too long"

        zone_data = {
            "FI": {"carbon": 45, "renewable": 82, "location": "Helsinki"},
            "DE": {"carbon": 302, "renewable": 55, "location": "Nuremberg"},
            "US": {"carbon": 420, "renewable": 22, "location": "Ashburn, VA"}
        }

        zone_data_str = json.dumps(zone_data)

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f"""You are a spatial inference router. Given these energy zone conditions:

{zone_data_str}

And this agent's preferences: "{preferences}"

Select the best zone for routing AI inference. Consider:
- Carbon intensity (lower = greener)
- Renewable percentage (higher = greener)
- The agent's stated priority

Respond ONLY with valid JSON: {{"zone": "XX", "reasoning": "one clear sentence explaining your choice"}}"""
            )
            return result

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                if "zone" not in data or "reasoning" not in data:
                    return False
                if data["zone"] not in {"FI", "DE", "US"}:
                    return False

                # GENUINE SUBJECTIVE CONSENSUS: validator independently reasons
                # about whether the leader's choice is defensible
                assessment = gl.nondet.exec_prompt(
                    f"""A routing system chose zone {data["zone"]} for an agent with preferences "{preferences}".

Zone data: {zone_data_str}

The system's reasoning: "{data["reasoning"]}"

Is this a defensible routing choice given the agent's preferences and the zone data?
Consider whether a reasonable person could reach this conclusion, even if you might choose differently.

Reply with ONLY "YES" or "NO" followed by one sentence explaining why."""
                )
                return "YES" in assessment.upper()
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        routing["preferences"] = preferences
        routing["zone_data"] = zone_data.get(routing.get("zone", "FI"), {})
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
