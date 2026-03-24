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
    def route_inference(self, prompt: str, priorities_json: str) -> str:
        """Route inference based on three verifiable dimensions.
        priorities_json: {"latency": 0-10, "quality": 0-10, "carbon": 0-10}"""
        assert len(prompt) < 10000, "Prompt too long"
        priorities = json.loads(priorities_json)
        latency_priority = priorities.get("latency", 5)
        quality_priority = priorities.get("quality", 5)
        carbon_priority = priorities.get("carbon", 5)

        nodes = {
            "FI": {
                "location": "Helsinki",
                "model": "DeepSeek V3",
                "quality_score": 7,
                "latency_ms": 145,
                "carbon_gco2_kwh": 45
            },
            "DE": {
                "location": "Nuremberg",
                "model": "Llama 3.3 70B",
                "quality_score": 6,
                "latency_ms": 89,
                "carbon_gco2_kwh": 302
            },
            "US": {
                "location": "Ashburn, VA",
                "model": "Claude Sonnet 4",
                "quality_score": 9,
                "latency_ms": 45,
                "carbon_gco2_kwh": 420
            }
        }

        priorities = f"latency={latency_priority}/10, quality={quality_priority}/10, carbon={carbon_priority}/10"
        nodes_str = json.dumps(nodes)

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f"""You are an inference router. Select which node handles this request.

NODES:
{nodes_str}

TASK: "{prompt}"

AGENT PRIORITIES: {priorities}

Each node has a model with a reasoning score (higher=smarter), latency (lower=faster), and carbon intensity (lower=greener). The agent's priorities tell you how to weigh these three dimensions.

Respond ONLY with valid JSON: {{"zone": "XX", "model": "model name", "reasoning": "one sentence explaining the tradeoff"}}"""
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
                    f"""An inference router chose {data.get("model", "unknown")} in zone {data["zone"]}.

Task: "{prompt}"
Agent priorities: {priorities}
Reasoning: "{data["reasoning"]}"

Nodes: {nodes_str}

Is this defensible given the agent's priorities? Reply ONLY "YES" or "NO" with one sentence."""
                )
                return "YES" in assessment.upper()
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        routing["priorities"] = {"latency": int(latency_priority), "quality": int(quality_priority), "carbon": int(carbon_priority)}
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
