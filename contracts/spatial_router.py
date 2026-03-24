# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class SpatialRouter(gl.Contract):
    """LLM-powered subjective inference routing with consensus verification."""

    owner: Address
    grid_oracle_addr: Address
    routing_history: DynArray[str]

    VALID_ZONES = {"FI", "DE", "US", "GB"}

    @gl.public.write
    def set_owner(self):
        """Set owner on first call (no constructor args on studionet)."""
        if self.owner == Address(b'\x00' * 20):
            self.owner = gl.message.sender_account
        else:
            assert gl.message.sender_account == self.owner, "Owner already set"

    @gl.public.write
    def set_oracle(self, oracle_addr: Address):
        """Set the GridOracle address. Call once after deployment."""
        assert gl.message.sender_account == self.owner, "Only owner can set oracle"
        self.grid_oracle_addr = oracle_addr

    @gl.public.write
    def route_inference(self, prompt: str, preferences: str) -> str:
        assert len(prompt) < 10000, "Prompt too long"
        assert len(preferences) < 1000, "Preferences too long"
        assert self.grid_oracle_addr != Address(b'\x00' * 20), "Oracle not set"

        # Step 1: Read zone data from GridOracle (DETERMINISTIC)
        oracle = gl.get_contract_at(self.grid_oracle_addr)
        zone_data_str = oracle.view().get_zone_data()

        # Step 2: LLM reasons about routing (NONDET)
        def routing_leader():
            result = gl.nondet.exec_prompt(
                f"""You are a spatial inference router. Given these energy zone conditions:

{zone_data_str}

And this agent's preferences: "{preferences}"

Select the best zone. Consider carbon (lower=greener), renewable % (higher=greener), and the agent's priority.

Respond ONLY with valid JSON: {{"zone": "XX", "reasoning": "one sentence"}}"""
            )
            return result

        def routing_validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                return ("zone" in data and "reasoning" in data
                        and data["zone"] in {"FI", "DE", "US", "GB"})
            except Exception:
                return False

        routing_result = gl.vm.run_nondet_unsafe(routing_leader, routing_validator)
        routing = json.loads(routing_result)
        chosen_zone = routing.get("zone", "FI")
        reasoning = routing.get("reasoning", "Selected based on preferences")

        # Step 3: Execute inference (SECOND NONDET)
        def inference_leader():
            return gl.nondet.exec_prompt(prompt)

        def inference_validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            return len(str(leader_result.calldata)) > 0

        inference_result = gl.vm.run_nondet_unsafe(inference_leader, inference_validator)

        # Step 4: Record provenance (DETERMINISTIC)
        zone_data = json.loads(zone_data_str)
        record = json.dumps({
            "zone": chosen_zone,
            "zone_data": zone_data.get(chosen_zone, {}),
            "preferences": preferences,
            "reasoning": reasoning,
            "prompt_preview": prompt[:100]
        })
        self.routing_history.append(record)

        return json.dumps({
            "result": str(inference_result),
            "routed_to": chosen_zone,
            "reasoning": reasoning,
            "zone_carbon": zone_data.get(chosen_zone, {}).get("carbon", 0),
            "zone_renewable": zone_data.get(chosen_zone, {}).get("renewable", 0)
        })

    @gl.public.view
    def get_history(self) -> str:
        records = []
        for r in self.routing_history:
            records.append(json.loads(r))
        return json.dumps(records)

    @gl.public.view
    def get_history_count(self) -> u32:
        return u32(len(self.routing_history))
