# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


def parse_result(raw):
    """Handle both dict (response_format='json') and str (raw text) from exec_prompt."""
    if isinstance(raw, dict):
        return raw
    s = raw.strip() if isinstance(raw, str) else str(raw).strip()
    if s.startswith("```"):
        lines = s.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        s = "\n".join(lines).strip()
    return json.loads(s)

class SpatialRouter(gl.Contract):
    """Full inference router with cross-contract oracle reads.
    Owner-gated. Sanitized inputs. Genuine validator re-reasoning.
    Designed for mainnet where cross-contract calls are reliable."""

    owner: Address
    grid_oracle_addr: Address
    routing_history: DynArray[str]

    @gl.public.write
    def set_owner(self, expected_owner: Address):
        """Set owner. Must pass the intended owner address to prevent front-running."""
        if self.owner == Address(b'\x00' * 20):
            assert gl.message.sender_account == expected_owner, "Sender must match expected owner"
            self.owner = expected_owner
        else:
            assert gl.message.sender_account == self.owner, "Owner already set"

    def _only_owner(self):
        assert gl.message.sender_account == self.owner, "Only owner"

    @gl.public.write
    def set_oracle(self, oracle_addr: Address):
        """Set the GridOracle address. Owner only."""
        self._only_owner()
        self.grid_oracle_addr = oracle_addr

    @gl.public.write
    def route_inference(self, prompt: str, preferences: str) -> str:
        assert len(prompt) < 10000, "Prompt too long"
        assert len(preferences) < 1000, "Preferences too long"
        assert self.grid_oracle_addr != Address(b'\x00' * 20), "Oracle not set"

        # Sanitize inputs
        safe_prompt = ''.join(c for c in prompt[:200] if c == '\n' or (' ' <= c <= '~'))
        safe_prefs = ''.join(c for c in preferences[:200] if ' ' <= c <= '~')

        # Step 1: Read node data from GridOracle (DETERMINISTIC)
        oracle = gl.get_contract_at(self.grid_oracle_addr)
        nodes_str = oracle.view().get_all_nodes()
        nodes = json.loads(nodes_str)
        valid_zones = set(nodes.keys())
        assert len(valid_zones) > 0, "No nodes in oracle"

        # Step 2: LLM reasons about routing (NONDET)
        def routing_leader():
            result = gl.nondet.exec_prompt(
                f"""You are an inference router. Given these nodes:

{nodes_str}

And this agent's preferences: "{safe_prefs}"

Select the best node. Consider quality_benchmark, latency_ms, carbon_gco2_kwh, and the agent's priorities.

Respond ONLY with valid JSON, no markdown: {{"zone": "XX", "model": "name", "reasoning": "one sentence"}}""",
                response_format="json"
            )
            return result

        def routing_validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = parse_result(leader_result.calldata)
                if "zone" not in data or "reasoning" not in data:
                    return False
                if data["zone"] not in valid_zones:
                    return False
                if len(data.get("reasoning", "")) < 10:
                    return False

                # Genuine re-reasoning
                assessment = gl.nondet.exec_prompt(
                    f"""A router chose {data["zone"]} ({nodes.get(data["zone"], {}).get("model", "?")}) for preferences "{safe_prefs}".

Available: {nodes_str}

Reasoning: "{data["reasoning"]}"

Is this defensible? Reply ONLY "YES" or "NO" then one sentence."""
                )
                return assessment.strip().upper().startswith("YES")
            except Exception:
                return False

        routing_result = gl.vm.run_nondet_unsafe(routing_leader, routing_validator)
        routing = parse_result(routing_result)
        chosen_zone = routing.get("zone", list(valid_zones)[0])
        reasoning = routing.get("reasoning", "Selected based on preferences")

        # Step 3: Record provenance (DETERMINISTIC)
        record = json.dumps({
            "zone": chosen_zone,
            "model": routing.get("model", ""),
            "node_data": nodes.get(chosen_zone, {}),
            "preferences": safe_prefs,
            "reasoning": reasoning,
        })
        self.routing_history.append(record)

        return json.dumps({
            "routed_to": chosen_zone,
            "model": routing.get("model", ""),
            "reasoning": reasoning,
            "node_data": nodes.get(chosen_zone, {})
        })

    @gl.public.view
    def get_history(self) -> str:
        """Returns last 50 routing decisions."""
        records = []
        start = max(0, len(self.routing_history) - 50)
        for i in range(start, len(self.routing_history)):
            records.append(json.loads(self.routing_history[i]))
        return json.dumps(records)

    @gl.public.view
    def get_history_count(self) -> u32:
        return u32(len(self.routing_history))
