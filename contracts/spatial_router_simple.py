# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class SpatialRouterSimple(gl.Contract):
    """Inference router with subjective consensus.
    Node registry is stored onchain (mirrored from GridOracle).
    Router reads its own storage at routing time — no hardcoded data,
    no cross-contract calls (which timeout on Bradbury)."""

    node_registry: TreeMap[str, str]  # node_id -> JSON node data
    node_id_list: str  # comma-separated node IDs
    routing_history: DynArray[str]

    @gl.public.write
    def register_node(self, node_id: str, node_data_json: str):
        """Register or update a node. Mirrors GridOracle.register_node."""
        assert len(node_id) < 16, "node_id too long"
        assert "," not in node_id, "node_id cannot contain commas"
        assert len(node_data_json) < 4096, "node data too large"
        data = json.loads(node_data_json)
        assert "model" in data, "model required"
        self.node_registry[node_id] = node_data_json
        # Maintain comma-separated ID list
        existing = self.node_id_list or ""
        ids = [x for x in existing.split(",") if x]
        if node_id not in ids:
            ids.append(node_id)
        self.node_id_list = ",".join(ids)

    @gl.public.write
    def route_inference(self, prompt: str, priorities_json: str) -> str:
        """Route inference to the best node based on priorities.
        Reads node data from onchain storage, not from arguments."""
        assert len(prompt) < 10000, "Prompt too long"

        priorities = json.loads(priorities_json)
        latency_p = priorities.get("latency", 5)
        quality_p = priorities.get("quality", 5)
        carbon_p = priorities.get("carbon", 5)

        # Build node data from storage
        id_str = self.node_id_list or ""
        all_ids = [x for x in id_str.split(",") if x]
        assert len(all_ids) > 0, "No nodes registered"

        nodes = {}
        node_summary = []
        for nid in all_ids:
            raw = self.node_registry.get(nid, "")
            if raw:
                nodes[nid] = json.loads(raw)
                n = nodes[nid]
                node_summary.append(f"{nid}: {n.get('model','?')} | quality:{n.get('quality_benchmark','?')} latency:{n.get('latency_ms','?')}ms carbon:{n.get('carbon_gco2_kwh','?')}gCO2")

        node_ids = list(nodes.keys())
        nodes_compact = "\n".join(node_summary)
        priorities_str = f"latency={latency_p}/10, quality={quality_p}/10, carbon={carbon_p}/10"

        def leader_fn():
            result = gl.nondet.exec_prompt(
                f"""Select a node for this task. Priorities: {priorities_str}

{nodes_compact}

Task: "{prompt[:200]}"

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
                reasoning_lower = data["reasoning"].lower()
                zone = data["zone"]
                node = nodes[zone]
                has_zone_ref = zone.lower() in reasoning_lower or node.get("location", "").lower() in reasoning_lower
                has_model_ref = node.get("model", "").lower() in reasoning_lower
                has_priority_ref = any(w in reasoning_lower for w in ["latency", "quality", "carbon", "fast", "green", "smart", "benchmark"])
                return has_zone_ref or has_model_ref or has_priority_ref
            except Exception:
                return False

        routing = json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        chosen = routing.get("zone", node_ids[0])
        routing["priorities"] = {"latency": int(latency_p), "quality": int(quality_p), "carbon": int(carbon_p)}
        routing["prompt_preview"] = prompt[:100]
        routing["node_data"] = nodes.get(chosen, {})
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
        records = []
        for r in self.routing_history:
            records.append(json.loads(r))
        return json.dumps(records)
