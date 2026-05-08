# Copyright (c) 2025 GenOrca. All Rights Reserved.

import unreal
import json
import traceback


def _load_asset(asset_path, expected_class=None):
    """Load an asset and optionally verify its class. Returns (asset, error_json_str)."""
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        return None, json.dumps({
            "success": False,
            "message": f"Asset not found or failed to load: {asset_path}"
        })
    if expected_class is not None and not isinstance(asset, expected_class):
        return None, json.dumps({
            "success": False,
            "message": f"Asset at '{asset_path}' is {type(asset).__name__}, expected {expected_class.__name__}."
        })
    return asset, None


# ─── Read Actions ─────────────────────────────────────────────────────────────

def ue_get_selected_bp_nodes() -> str:
    """Returns information about currently selected blueprint nodes in the editor."""
    try:
        nodes = unreal.MCPythonHelper.get_selected_blueprint_nodes()
        node_infos = []
        for node in nodes:
            node_info = {
                "name": node.get_name() if hasattr(node, 'get_name') else str(node),
                "class": node.get_class().get_name() if hasattr(node, 'get_class') else str(type(node)),
                "object_path": node.get_path_name() if hasattr(node, 'get_path_name') else None
            }
            node_infos.append(node_info)
        return json.dumps({
            "success": True,
            "selected_nodes_count": len(node_infos),
            "selected_nodes": node_infos
        })
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_get_selected_bp_node_infos() -> str:
    """Returns compact blueprint node info optimized for LLM token efficiency."""
    try:
        node_infos = unreal.MCPythonHelper.get_selected_blueprint_node_infos()

        name_to_id = {}
        for i, n in enumerate(node_infos):
            name_to_id[n.node_name] = i

        def link_to_dict(link):
            d = {}
            if link.node_name in name_to_id:
                d["node"] = name_to_id[link.node_name]
            else:
                d["node"] = link.node_title
            if link.pin_name:
                d["pin"] = link.pin_name
            return d

        def pin_to_dict(pin):
            name = pin.friendly_name if pin.friendly_name else pin.pin_name
            d = {"name": name, "dir": pin.direction}
            ptype = pin.pin_type
            if pin.pin_sub_type:
                ptype += ":" + pin.pin_sub_type
            d["type"] = ptype
            if pin.default_value:
                d["default"] = pin.default_value
            linked = list(pin.linked_to)
            if linked:
                d["linked"] = [link_to_dict(l) for l in linked]
            return d

        def node_to_dict(node, idx):
            d = {"id": idx, "title": node.node_title}
            if node.node_comment:
                d["comment"] = node.node_comment
            d["pins"] = [pin_to_dict(p) for p in node.pins]
            return d

        nodes = [node_to_dict(n, i) for i, n in enumerate(node_infos)]
        return json.dumps({
            "success": True,
            "nodes": nodes
        })
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_get_blueprint_graph_info(asset_path: str = None, graph_name: str = "EventGraph") -> str:
    """Returns the full graph info for a Blueprint graph."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.get_blueprint_graph_info(bp, graph_name)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_list_callable_functions(asset_path: str = None, filter: str = "") -> str:
    """Lists callable functions available in a Blueprint context."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.list_callable_functions(bp, filter)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_list_blueprint_variables(asset_path: str = None) -> str:
    """Lists all variables defined in a Blueprint."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.list_blueprint_variables(bp)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


# ─── Write Actions ────────────────────────────────────────────────────────────

def ue_add_blueprint_node(asset_path: str = None, graph_name: str = "EventGraph",
                          node_json: dict = None) -> str:
    """Adds a single node to a Blueprint graph."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if node_json is None:
        return json.dumps({"success": False, "message": "Required parameter 'node_json' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        node_json_str = json.dumps(node_json)
        result_json = unreal.MCPythonHelper.add_blueprint_node(bp, graph_name, node_json_str)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_connect_blueprint_pins(asset_path: str = None, graph_name: str = "EventGraph",
                              source_node: str = None, source_pin: str = None,
                              target_node: str = None, target_pin: str = None) -> str:
    """Connects two pins in a Blueprint graph."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    for name, val in [("source_node", source_node), ("source_pin", source_pin),
                      ("target_node", target_node), ("target_pin", target_pin)]:
        if val is None:
            return json.dumps({"success": False, "message": f"Required parameter '{name}' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.connect_blueprint_pins(
            bp, graph_name, source_node, source_pin, target_node, target_pin)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_remove_blueprint_node(asset_path: str = None, graph_name: str = "EventGraph",
                             node_name: str = None) -> str:
    """Removes a node from a Blueprint graph."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if node_name is None:
        return json.dumps({"success": False, "message": "Required parameter 'node_name' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.remove_blueprint_node(bp, graph_name, node_name)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_build_blueprint_graph(asset_path: str = None, graph_name: str = "EventGraph",
                             graph_structure: dict = None) -> str:
    """Builds a Blueprint graph from JSON adjacency list."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if graph_structure is None:
        return json.dumps({"success": False, "message": "Required parameter 'graph_structure' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        graph_json_str = json.dumps(graph_structure)
        result_json = unreal.MCPythonHelper.build_blueprint_graph(bp, graph_name, graph_json_str)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_compile_blueprint(asset_path: str = None) -> str:
    """Compiles a Blueprint and returns the result."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        result_json = unreal.MCPythonHelper.compile_blueprint(bp)
        return result_json
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_set_blueprint_node_position(asset_path: str = None, graph_name: str = "EventGraph",
                                    node_name: str = None, pos_x: float = 0.0, pos_y: float = 0.0) -> str:
    """Sets the canvas position of a node in a Blueprint graph."""
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if node_name is None:
        return json.dumps({"success": False, "message": "Required parameter 'node_name' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err
        return unreal.MCPythonHelper.set_blueprint_node_position(bp, graph_name, node_name, pos_x, pos_y)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_auto_layout_graph(asset_path: str = None, graph_name: str = "EventGraph",
                          x_step: float = 380.0, y_step: float = 200.0) -> str:
    """
    Auto-lays out all nodes in a Blueprint graph using DAG topological sort.

    Entry nodes (BeginPlay, Tick, custom events, input events) are placed at column 0.
    Each node's column = max(predecessor columns) + 1.
    Within each column, nodes are stacked vertically by row.
    x_step / y_step control the pixel spacing between columns and rows.
    """
    if asset_path is None:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp, err = _load_asset(asset_path, unreal.Blueprint)
        if err:
            return err

        graph_info_str = unreal.MCPythonHelper.get_blueprint_graph_info(bp, graph_name)
        graph_info = json.loads(graph_info_str)
        if not graph_info.get("success"):
            return graph_info_str

        nodes = graph_info.get("nodes", [])
        if not nodes:
            return json.dumps({"success": True, "message": "No nodes to lay out.", "positioned": 0})

        # Build name → node map and adjacency list (execution flow: source → target)
        node_names = [n["node_name"] for n in nodes]
        name_set = set(node_names)

        # in_degree tracks how many execution predecessors each node has
        in_degree = {n: 0 for n in node_names}
        successors = {n: [] for n in node_names}  # execution successors

        ENTRY_TYPES = {"K2Node_Event", "K2Node_CustomEvent", "K2Node_InputKey",
                       "K2Node_InputAction", "K2Node_FunctionEntry"}

        for node in nodes:
            node_name = node["node_name"]
            for pin in node.get("pins", []):
                if pin.get("direction") != "Output":
                    continue
                pin_type = pin.get("type", "")
                if pin_type not in ("exec", ""):
                    continue
                for link in pin.get("linked_to", []):
                    target = link.get("node_name", "")
                    if target in name_set and target != node_name:
                        if target not in successors[node_name]:
                            successors[node_name].append(target)
                            in_degree[target] += 1

        # Force entry nodes to column 0 (override in_degree)
        forced_entry = set()
        for node in nodes:
            node_class = node.get("node_class", node.get("node_name", ""))
            for et in ENTRY_TYPES:
                if et in node_class or et in node.get("node_name", ""):
                    forced_entry.add(node["node_name"])
                    break
        # Also: any node with in_degree == 0 that has exec output pins
        for node in nodes:
            n = node["node_name"]
            if in_degree[n] == 0:
                for pin in node.get("pins", []):
                    if pin.get("direction") == "Output" and pin.get("type") in ("exec", ""):
                        forced_entry.add(n)
                        break

        # Kahn's BFS topological sort
        from collections import deque
        column = {}
        queue = deque()
        for n in node_names:
            if in_degree[n] == 0 or n in forced_entry:
                column[n] = 0
                queue.append(n)

        # Any unreachable nodes default to column 0
        while queue:
            n = queue.popleft()
            for s in successors[n]:
                if column.get(s, -1) < column[n] + 1:
                    column[s] = column[n] + 1
                in_degree[s] -= 1
                if in_degree[s] <= 0 and s not in column:
                    queue.append(s)

        # Ensure all nodes have a column
        for n in node_names:
            if n not in column:
                column[n] = 0

        # Assign rows within each column (preserve original order for stability)
        col_row = {}
        positions = {}
        for node in nodes:
            n = node["node_name"]
            c = column[n]
            r = col_row.get(c, 0)
            positions[n] = (c * x_step, r * y_step)
            col_row[c] = r + 1

        # Apply positions
        errors = []
        positioned = 0
        for n, (px, py) in positions.items():
            result_str = unreal.MCPythonHelper.set_blueprint_node_position(bp, graph_name, n, px, py)
            result = json.loads(result_str)
            if result.get("success"):
                positioned += 1
            else:
                errors.append(f"{n}: {result.get('message', '?')}")

        return json.dumps({
            "success": True,
            "positioned": positioned,
            "total": len(node_names),
            "errors": errors,
            "message": f"Auto-layout complete: {positioned}/{len(node_names)} nodes positioned.",
        })
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})
