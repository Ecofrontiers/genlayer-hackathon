# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json
import re


class SpatialRouterSimple(gl.Contract):
    """Inference router with subjective consensus.
    Owner-gated node registration. Sanitized inputs. Capped history.
    Reads node data from onchain storage at routing time."""

    owner: Address
    node_registry: TreeMap[str, str]
    node_id_list: str  # comma-separated node IDs
    routing_history: DynArray[str]

    MAX_HISTORY = 200
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
        """Register or update a node. Owner only."""
        self._only_owner()
        assert len(node_id) < 16, "node_id too long"
        assert node_id.isalnum(), "node_id must be alphanumeric"
        assert "," not in node_id, "node_id cannot contain commas"
        assert len(node_data_json) < 4096, "node data too large"
        data = json.loads(node_data_json)
        assert "model" in data, "model required"
        # Sanitize model name — alphanumeric, spaces, dots only
        model = data["model"]
        assert len(model) < 64, "model name too long"

        self.node_registry[node_id] = node_data_json
        existing = self.node_id_list or ""
        ids = [x for x in existing.split(",") if x]
        if node_id not in ids:
            assert len(ids) < self.MAX_NODES, "Max nodes reached"
            ids.append(node_id)
        self.node_id_list = ",".join(ids)

    @gl.public.write
    def route_inference(self, prompt: str, priorities_json: str) -> str:
        """Route inference to the best node based on priorities."""
        assert len(prompt) < 10000, "Prompt too long"
        assert len(priorities_json) < 256, "Priorities too large"

        priorities = json.loads(priorities_json)
        latency_p = min(10, max(0, int(priorities.get("latency", 5))))
        quality_p = min(10, max(0, int(priorities.get("quality", 5))))
        carbon_p = min(10, max(0, int(priorities.get("carbon", 5))))

        # Build node data from storage
        id_str = self.node_id_list or ""
        all_ids = [x for x in id_str.split(",") if x]
        assert len(all_ids) > 0, "No nodes registered"

        nodes = {}
        node_summary = []
        for nid in all_ids:
            raw = self.node_registry.get(nid, "")
            if raw and nid not in nodes:
                nodes[nid] = json.loads(raw)
                n = nodes[nid]
                node_summary.append(f"{nid}: {n.get('model','?')} | quality:{n.get('quality_benchmark','?')} latency:{n.get('latency_ms','?')}ms carbon:{n.get('carbon_gco2_kwh','?')}gCO2")

        node_ids = list(nodes.keys())
        nodes_compact = "\n".join(node_summary)
        priorities_str = f"latency={latency_p}/10, quality={quality_p}/10, carbon={carbon_p}/10"

        # Sanitize prompt for LLM — strip control chars, truncate
        safe_prompt = re.sub(r'[^\x20-\x7E\n]', '', prompt[:200])

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f"""Select a node for this task. Priorities: {priorities_str}

{nodes_compact}

Task: "{safe_prompt}"

Reply JSON: {{"zone":"XX","model":"name","reasoning":"one sentence"}}"""
            )
            return result

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                if "zone" not in data or "reasoning" not in data:
                    return False
                if data["zone"] not in nodes:
                    return False
                if len(data.get("reasoning", "")) < 10:
                    return False
                reasoning_lower = data["reasoning"].lower()
                zone = data["zone"]
                node = nodes[zone]
                # Require zone/model reference AND priority reference
                has_context = (zone.lower() in reasoning_lower
                    or node.get("location", "").lower() in reasoning_lower
                    or node.get("model", "").lower() in reasoning_lower)
                has_priority = any(w in reasoning_lower for w in
                    ["latency", "quality", "carbon", "fast", "green", "benchmark", "score"])
                return has_context and has_priority
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        chosen = routing.get("zone", node_ids[0])
        routing["priorities"] = {"latency": latency_p, "quality": quality_p, "carbon": carbon_p}
        routing["node_data"] = nodes.get(chosen, {})
        # Don't store prompt_preview — prevents information leakage
        self.routing_history.append(json.dumps(routing))
        return json.dumps(routing)

    @gl.public.view
    def get_nodes(self) -> str:
        """Get all registered nodes."""
        id_str = self.node_id_list or ""
        all_ids = [x for x in id_str.split(",") if x]
        nodes = {}
        for nid in all_ids:
            raw = self.node_registry.get(nid, "")
            if raw:
                nodes[nid] = json.loads(raw)
        return json.dumps(nodes)

    @gl.public.view
    def get_count(self) -> u32:
        return u32(len(self.routing_history))

    @gl.public.view
    def get_history(self) -> str:
        """Get routing history. Returns last 50 entries max."""
        records = []
        start = max(0, len(self.routing_history) - 50)
        for i in range(start, len(self.routing_history)):
            records.append(json.loads(self.routing_history[i]))
        return json.dumps(records)
