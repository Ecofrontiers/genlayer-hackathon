# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class SpatialRouterSimple(gl.Contract):
    """Production inference router with genuine subjective consensus.
    Routes based on model capability, cost, latency, and carbon impact.
    Validators independently re-reason about defensibility."""

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
    def route_inference(self, prompt: str, preferences: str) -> str:
        assert len(preferences) < 1000, "Preferences too long"
        assert len(prompt) < 10000, "Prompt too long"

        nodes = {
            "FI": {
                "location": "Helsinki",
                "model": "DeepSeek V3",
                "model_strengths": "code, math, structured output",
                "cost_per_1k_tokens": 0.0004,
                "latency_ms": 145,
                "carbon_gco2_kwh": 45,
                "renewable_pct": 82
            },
            "DE": {
                "location": "Nuremberg",
                "model": "Llama 3.3 70B",
                "model_strengths": "general purpose, multilingual, fast",
                "cost_per_1k_tokens": 0.0008,
                "latency_ms": 89,
                "carbon_gco2_kwh": 302,
                "renewable_pct": 55
            },
            "US": {
                "location": "Ashburn, VA",
                "model": "Claude Sonnet 4",
                "model_strengths": "reasoning, analysis, writing, complex tasks",
                "cost_per_1k_tokens": 0.003,
                "latency_ms": 45,
                "carbon_gco2_kwh": 420,
                "renewable_pct": 22
            }
        }

        nodes_str = json.dumps(nodes)

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f"""You are an inference router. You must select which node should handle this request.

AVAILABLE NODES:
{nodes_str}

AGENT'S TASK: "{prompt}"

AGENT'S ROUTING PREFERENCES: "{preferences}"

Select the best node by weighing:
1. Model fit — does the model's strengths match the task?
2. Cost — per 1k tokens (lower = cheaper)
3. Latency — response time in ms (lower = faster)
4. Carbon — gCO2/kWh of the zone's grid (lower = greener)

The agent's preferences tell you how to weigh these factors.

Respond ONLY with valid JSON: {{"zone": "XX", "model": "model name", "reasoning": "one sentence explaining the tradeoff you made"}}"""
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

                assessment = gl.nondet.exec_prompt(
                    f"""An inference router chose {data.get("model", "unknown")} in zone {data["zone"]} for this task:

Task: "{prompt}"
Preferences: "{preferences}"
Reasoning: "{data["reasoning"]}"

Available nodes: {nodes_str}

Is this a defensible routing choice? Consider whether the model fits the task, and whether the cost/latency/carbon tradeoff respects the agent's preferences.

Reply with ONLY "YES" or "NO" followed by one sentence."""
                )
                return "YES" in assessment.upper()
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        routing["preferences"] = preferences
        routing["prompt_preview"] = prompt[:100]
        routing["node_data"] = nodes.get(routing.get("zone", "FI"), {})
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
