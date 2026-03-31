# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

def parse_result(raw):
    """Handle both dict (response_format='json') and str (raw text) from exec_prompt."""
    if isinstance(raw, dict):
        return raw
    s = raw.strip() if isinstance(raw, str) else str(raw).strip()
    # Strip markdown fences if present
    if s.startswith("```"):
        lines = s.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        s = "\n".join(lines).strip()
    return json.loads(s)

class SpatialRouterSimple(gl.Contract):
    node_registry: TreeMap[str, str]
    node_id_list: str
    routing_history: DynArray[str]

    @gl.public.write
    def register_node(self, node_id: str, node_data_json: str):
        assert len(node_id) < 16
        assert len(node_data_json) < 4096
        data = json.loads(node_data_json)
        assert "location" in data
        self.node_registry[node_id] = node_data_json
        existing = self.node_id_list or ""
        ids = [x for x in existing.split(",") if x]
        if node_id not in ids:
            ids.append(node_id)
        self.node_id_list = ",".join(ids)

    @gl.public.write
    def route_inference(self, prompt: str, priorities_json: str) -> str:
        assert len(prompt) < 10000
        priorities = json.loads(priorities_json)
        latency_p = min(10, max(0, int(priorities.get("latency", 5))))
        quality_p = min(10, max(0, int(priorities.get("quality", 5))))
        carbon_p = min(10, max(0, int(priorities.get("carbon", 5))))
        id_str = self.node_id_list or ""
        all_ids = [x for x in id_str.split(",") if x]
        assert len(all_ids) > 0
        nodes = {}
        node_summary = []
        for nid in all_ids:
            raw = self.node_registry.get(nid, "")
            if raw and nid not in nodes:
                nodes[nid] = json.loads(raw)
                n = nodes[nid]
                node_summary.append(nid + " (" + str(n.get("location","?")) + "): latency " + str(n.get("latency_ms","?")) + "ms, carbon " + str(n.get("carbon_gco2_kwh","?")) + "gCO2")
        node_ids = list(nodes.keys())
        nodes_compact = "\n".join(node_summary)
        priorities_str = "latency=" + str(latency_p) + "/10, quality=" + str(quality_p) + "/10, carbon=" + str(carbon_p) + "/10"

        def leader_fn():
            return gl.nondet.exec_prompt("Pick node+model.\nNodes: " + nodes_compact + "\nModels: DeepSeek V3 (code/math), Llama 70B (general), Claude Sonnet 4 (reasoning)\nPriorities: " + priorities_str + "\nReply JSON: {\"node\":\"XX\",\"model\":\"name\",\"reasoning\":\"why\"}", response_format="json")

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = parse_result(leader_result.calldata)
                if "node" not in data or "reasoning" not in data:
                    return False
                if data["node"] not in nodes:
                    return False
                rl = data["reasoning"].lower()
                return len(rl) > 10
            except Exception:
                return False

        routing = parse_result(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        chosen_node = routing.get("node", node_ids[0])
        routing["priorities"] = {"latency": latency_p, "quality": quality_p, "carbon": carbon_p}
        routing["node_data"] = nodes.get(chosen_node, {})
        self.routing_history.append(json.dumps(routing))
        return json.dumps(routing)

    @gl.public.view
    def get_nodes(self) -> str:
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
        start = max(0, len(self.routing_history) - 50)
        for i in range(start, len(self.routing_history)):
            records.append(json.loads(self.routing_history[i]))
        return json.dumps(records)
