#!/usr/bin/env python3
"""
Flappy Bird game creator for Unreal Engine via MCP.
Run this script while Unreal Engine is open with the UnrealMCPython plugin active.
"""

import socket
import json
import sys
import time

HOST = '127.0.0.1'
PORT = 12029
TIMEOUT = 60

FLAPPY_DIR = '/Game/FlappyBird'
BIRD_BP    = f'{FLAPPY_DIR}/BP_FlappyBird'
PIPE_BP    = f'{FLAPPY_DIR}/BP_FlappyPipe'
GM_BP      = f'{FLAPPY_DIR}/BP_FlappyGameMode'
IA_FLAP    = f'{FLAPPY_DIR}/Input/IA_Flap'
IMC_FLAPPY = f'{FLAPPY_DIR}/Input/IMC_Flappy'

# ─── TCP helpers ─────────────────────────────────────────────────────────────

def _send(cmd: dict) -> dict:
    data = json.dumps(cmd, ensure_ascii=False).encode('utf-8')
    with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as s:
        s.sendall(data)
        buf = b''
        while True:
            chunk = s.recv(16384)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode('utf-8'))


def exec_py(code: str) -> dict:
    return _send({"type": "python", "code": code})


def call_ue(module: str, fn: str, args: dict) -> dict:
    return _send({"type": "python_call", "module": module, "function": fn, "args": args})


def build_graph(asset_path: str, structure: dict, graph_name: str = "EventGraph") -> dict:
    return call_ue("UnrealMCPython.blueprint_actions", "ue_build_blueprint_graph",
                   {"asset_path": asset_path, "graph_name": graph_name, "graph_structure": structure})


def compile_bp(asset_path: str) -> dict:
    return call_ue("UnrealMCPython.blueprint_actions", "ue_compile_blueprint",
                   {"asset_path": asset_path})


def ok(label: str, result: dict):
    success = result.get('success', True)
    mark = 'OK' if success else 'FAIL'
    msg = result.get('message', '')
    if not success:
        errs = result.get('creation_errors', []) + result.get('connection_errors', [])
        if errs:
            msg += ' | ' + '; '.join(errs)
        err = result.get('error', '')
        if err:
            msg += ' | ' + err
    print(f"  [{mark}] {label}: {msg}")
    return success

# ─── Step 1: Create folder + Blueprint assets ─────────────────────────────────

CREATE_ASSETS_CODE = """
import unreal, json
results = {}
try:
    unreal.EditorAssetLibrary.make_directory('/Game/FlappyBird')
    unreal.EditorAssetLibrary.make_directory('/Game/FlappyBird/Input')
    at = unreal.AssetToolsHelpers.get_asset_tools()

    def make_bp(name, folder, parent):
        path = f'{folder}/{name}'
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            return path
        f = unreal.BlueprintFactory()
        f.parent_class = parent
        bp = at.create_asset(name, folder, unreal.Blueprint, f)
        return bp.get_path_name() if bp else None

    results['bird'] = make_bp('BP_FlappyBird',    '/Game/FlappyBird', unreal.Pawn)
    results['pipe'] = make_bp('BP_FlappyPipe',    '/Game/FlappyBird', unreal.Actor)
    results['gm']   = make_bp('BP_FlappyGameMode','/Game/FlappyBird', unreal.GameModeBase)
    results['success'] = True
except Exception as e:
    results['success'] = False
    results['error'] = str(e)
print(json.dumps(results))
"""

# ─── Step 2: Add variables ────────────────────────────────────────────────────

def add_variables_code(asset_path: str, variables: list) -> str:
    """Variables: list of (name, category, sub_category, default_val)"""
    vars_json = json.dumps(variables)
    return f"""
import unreal, json
results = []
try:
    bp = unreal.EditorAssetLibrary.load_asset('{asset_path}')
    if not bp:
        print(json.dumps({{'success': False, 'message': 'BP not found'}}))
    else:
        current = list(bp.get_editor_property('new_variables'))
        existing = {{v.get_editor_property('var_name') for v in current}}
        variables = {vars_json}
        for name, cat, sub, default in variables:
            if name in existing:
                results.append({{'name': name, 'status': 'exists'}})
                continue
            try:
                pt = unreal.EdGraphPinType()
                pt.set_editor_property('pin_category', cat)
                if sub:
                    pt.set_editor_property('pin_sub_category', sub)
                vd = unreal.BPVariableDescription()
                vd.set_editor_property('var_name', name)
                vd.set_editor_property('var_type', pt)
                if default:
                    vd.set_editor_property('default_value', default)
                current.append(vd)
                results.append({{'name': name, 'status': 'added'}})
            except Exception as e:
                results.append({{'name': name, 'status': 'error', 'error': str(e)}})
        bp.set_editor_property('new_variables', current)
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        print(json.dumps({{'success': True, 'results': results}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

# ─── Bird event graph ─────────────────────────────────────────────────────────

BIRD_GRAPH = {
    "nodes": [
        # ── Tick / Physics ──
        {"id": "tick",        "type": "Event",        "event_name": "ReceiveTick"},
        {"id": "get_dead",    "type": "VariableGet",  "variable_name": "bIsDead"},
        {"id": "dead_branch", "type": "Branch"},
        {"id": "seq",         "type": "Sequence"},

        # Physics chain
        {"id": "get_vel",     "type": "VariableGet",  "variable_name": "BirdVelocity"},
        {"id": "get_grav",    "type": "VariableGet",  "variable_name": "Gravity"},
        {"id": "mul_gd",      "type": "CallFunction", "function_name": "Multiply_FloatFloat",
         "target": "KismetMathLibrary"},
        {"id": "add_vg",      "type": "CallFunction", "function_name": "Add_FloatFloat",
         "target": "KismetMathLibrary"},
        {"id": "set_vel",     "type": "VariableSet",  "variable_name": "BirdVelocity"},
        {"id": "get_newvel",  "type": "VariableGet",  "variable_name": "BirdVelocity"},
        {"id": "mul_vd",      "type": "CallFunction", "function_name": "Multiply_FloatFloat",
         "target": "KismetMathLibrary"},
        {"id": "make_vec",    "type": "CallFunction", "function_name": "MakeVector",
         "target": "KismetMathLibrary",
         "pin_defaults": {"X": "0.0", "Y": "0.0"}},
        {"id": "move",        "type": "CallFunction", "function_name": "AddActorWorldOffset"},

        # Input check (Then 1 of Sequence)
        {"id": "get_pc",      "type": "CallFunction", "function_name": "GetPlayerController",
         "target": "GameplayStatics",
         "pin_defaults": {"PlayerIndex": "0"}},
        {"id": "was_pressed", "type": "CallFunction", "function_name": "WasInputKeyJustPressed",
         "target": "PlayerController",
         "pin_defaults": {"InKey": "SpaceBar"}},
        {"id": "inp_branch",  "type": "Branch"},
        {"id": "get_flap",    "type": "VariableGet",  "variable_name": "FlapStrength"},
        {"id": "set_flap",    "type": "VariableSet",  "variable_name": "BirdVelocity"},

        # ── Flap Custom Event ──
        {"id": "flap_ev",     "type": "CustomEvent",  "event_name": "Flap"},
        {"id": "flap_dead",   "type": "VariableGet",  "variable_name": "bIsDead"},
        {"id": "flap_branch", "type": "Branch"},
        {"id": "flap_str",    "type": "VariableGet",  "variable_name": "FlapStrength"},
        {"id": "flap_setv",   "type": "VariableSet",  "variable_name": "BirdVelocity"},

        # ── Die Custom Event ──
        {"id": "die_ev",      "type": "CustomEvent",  "event_name": "Die"},
        {"id": "set_dead",    "type": "VariableSet",  "variable_name": "bIsDead",
         "pin_defaults": {"bIsDead": "true"}},
    ],
    "connections": [
        # Tick execution
        {"source_node": "tick",        "source_pin": "execute",    "target_node": "dead_branch", "target_pin": "execute"},
        {"source_node": "dead_branch", "source_pin": "False",      "target_node": "seq",          "target_pin": "execute"},
        # Sequence Then 0 → physics
        {"source_node": "seq",         "source_pin": "Then 0",     "target_node": "set_vel",      "target_pin": "execute"},
        {"source_node": "set_vel",     "source_pin": "then",       "target_node": "move",         "target_pin": "execute"},
        # Sequence Then 1 → input
        {"source_node": "seq",         "source_pin": "Then 1",     "target_node": "inp_branch",   "target_pin": "execute"},
        {"source_node": "inp_branch",  "source_pin": "True",       "target_node": "set_flap",     "target_pin": "execute"},

        # Physics data
        {"source_node": "get_dead",    "source_pin": "bIsDead",    "target_node": "dead_branch",  "target_pin": "Condition"},
        {"source_node": "get_grav",    "source_pin": "Gravity",    "target_node": "mul_gd",       "target_pin": "A"},
        {"source_node": "tick",        "source_pin": "DeltaSeconds","target_node": "mul_gd",      "target_pin": "B"},
        {"source_node": "get_vel",     "source_pin": "BirdVelocity","target_node": "add_vg",      "target_pin": "A"},
        {"source_node": "mul_gd",      "source_pin": "ReturnValue", "target_node": "add_vg",      "target_pin": "B"},
        {"source_node": "add_vg",      "source_pin": "ReturnValue", "target_node": "set_vel",     "target_pin": "BirdVelocity"},
        {"source_node": "get_newvel",  "source_pin": "BirdVelocity","target_node": "mul_vd",      "target_pin": "A"},
        {"source_node": "tick",        "source_pin": "DeltaSeconds","target_node": "mul_vd",      "target_pin": "B"},
        {"source_node": "mul_vd",      "source_pin": "ReturnValue", "target_node": "make_vec",    "target_pin": "Z"},
        {"source_node": "make_vec",    "source_pin": "ReturnValue", "target_node": "move",        "target_pin": "DeltaLocation"},

        # Input data
        {"source_node": "get_pc",      "source_pin": "ReturnValue","target_node": "was_pressed",  "target_pin": "Target"},
        {"source_node": "was_pressed", "source_pin": "ReturnValue","target_node": "inp_branch",   "target_pin": "Condition"},
        {"source_node": "get_flap",    "source_pin": "FlapStrength","target_node": "set_flap",    "target_pin": "BirdVelocity"},

        # Flap event
        {"source_node": "flap_ev",     "source_pin": "execute",    "target_node": "flap_branch",  "target_pin": "execute"},
        {"source_node": "flap_dead",   "source_pin": "bIsDead",    "target_node": "flap_branch",  "target_pin": "Condition"},
        {"source_node": "flap_branch", "source_pin": "False",      "target_node": "flap_setv",    "target_pin": "execute"},
        {"source_node": "flap_str",    "source_pin": "FlapStrength","target_node": "flap_setv",   "target_pin": "BirdVelocity"},

        # Die event
        {"source_node": "die_ev",      "source_pin": "execute",    "target_node": "set_dead",     "target_pin": "execute"},
    ]
}

# ─── Pipe event graph ─────────────────────────────────────────────────────────

PIPE_GRAPH = {
    "nodes": [
        {"id": "tick",      "type": "Event",       "event_name": "ReceiveTick"},
        {"id": "get_speed", "type": "VariableGet", "variable_name": "MoveSpeed"},
        {"id": "mul_sd",    "type": "CallFunction","function_name": "Multiply_FloatFloat",
         "target": "KismetMathLibrary"},
        {"id": "negate",    "type": "CallFunction","function_name": "Multiply_FloatFloat",
         "target": "KismetMathLibrary",
         "pin_defaults": {"B": "-1.0"}},
        {"id": "make_delta","type": "CallFunction","function_name": "MakeVector",
         "target": "KismetMathLibrary",
         "pin_defaults": {"Y": "0.0", "Z": "0.0"}},
        {"id": "move",      "type": "CallFunction","function_name": "AddActorWorldOffset"},
        {"id": "get_loc",   "type": "CallFunction","function_name": "GetActorLocation"},
        {"id": "break_vec", "type": "CallFunction","function_name": "BreakVector",
         "target": "KismetMathLibrary"},
        {"id": "lt_check",  "type": "CallFunction","function_name": "Less_FloatFloat",
         "target": "KismetMathLibrary",
         "pin_defaults": {"B": "-2000.0"}},
        {"id": "dest_branch","type": "Branch"},
        {"id": "destroy",   "type": "CallFunction","function_name": "K2_DestroyActor"},
    ],
    "connections": [
        # Execution
        {"source_node": "tick",       "source_pin": "execute",     "target_node": "move",        "target_pin": "execute"},
        {"source_node": "move",       "source_pin": "then",        "target_node": "dest_branch",  "target_pin": "execute"},
        {"source_node": "dest_branch","source_pin": "True",        "target_node": "destroy",      "target_pin": "execute"},
        # Movement data
        {"source_node": "get_speed",  "source_pin": "MoveSpeed",   "target_node": "mul_sd",       "target_pin": "A"},
        {"source_node": "tick",       "source_pin": "DeltaSeconds","target_node": "mul_sd",       "target_pin": "B"},
        {"source_node": "mul_sd",     "source_pin": "ReturnValue", "target_node": "negate",       "target_pin": "A"},
        {"source_node": "negate",     "source_pin": "ReturnValue", "target_node": "make_delta",   "target_pin": "X"},
        {"source_node": "make_delta", "source_pin": "ReturnValue", "target_node": "move",         "target_pin": "DeltaLocation"},
        # Destruction check
        {"source_node": "get_loc",    "source_pin": "ReturnValue", "target_node": "break_vec",    "target_pin": "InVec"},
        {"source_node": "break_vec",  "source_pin": "X",           "target_node": "lt_check",     "target_pin": "A"},
        {"source_node": "lt_check",   "source_pin": "ReturnValue", "target_node": "dest_branch",  "target_pin": "Condition"},
    ]
}

# ─── GameMode event graph ─────────────────────────────────────────────────────

GM_GRAPH = {
    "nodes": [
        # BeginPlay: start spawn timer
        {"id": "begin",      "type": "Event",       "event_name": "ReceiveBeginPlay"},
        {"id": "set_timer",  "type": "CallFunction","function_name": "SetTimerByFunctionName",
         "target": "KismetSystemLibrary",
         "pin_defaults": {"FunctionName": "SpawnPipe", "Time": "2.0", "bLooping": "true"}},

        # SpawnPipe custom event
        {"id": "spawn_ev",   "type": "CustomEvent", "event_name": "SpawnPipe"},
        {"id": "rand_z",     "type": "CallFunction","function_name": "RandomFloatInRange",
         "target": "KismetMathLibrary",
         "pin_defaults": {"Min": "-250.0", "Max": "250.0"}},
        {"id": "make_loc",   "type": "CallFunction","function_name": "MakeVector",
         "target": "KismetMathLibrary",
         "pin_defaults": {"X": "2000.0", "Y": "0.0"}},
        {"id": "make_rot",   "type": "CallFunction","function_name": "MakeRotator",
         "target": "KismetMathLibrary",
         "pin_defaults": {"Roll": "0.0", "Pitch": "0.0", "Yaw": "0.0"}},
        {"id": "make_tf",    "type": "CallFunction","function_name": "MakeTransform",
         "target": "KismetMathLibrary",
         "pin_defaults": {"Scale": "1,1,1"}},
        {"id": "get_class",  "type": "VariableGet", "variable_name": "PipeClass"},
        {"id": "spawn",      "type": "CallFunction","function_name": "BeginSpawningActorFromClass",
         "target": "GameplayStatics"},
    ],
    "connections": [
        # BeginPlay
        {"source_node": "begin",     "source_pin": "execute",     "target_node": "set_timer", "target_pin": "execute"},
        # SpawnPipe execution
        {"source_node": "spawn_ev",  "source_pin": "execute",     "target_node": "spawn",     "target_pin": "execute"},
        # Location data
        {"source_node": "rand_z",    "source_pin": "ReturnValue", "target_node": "make_loc",  "target_pin": "Z"},
        {"source_node": "make_loc",  "source_pin": "ReturnValue", "target_node": "make_tf",   "target_pin": "Location"},
        {"source_node": "make_rot",  "source_pin": "ReturnValue", "target_node": "make_tf",   "target_pin": "Rotation"},
        {"source_node": "make_tf",   "source_pin": "ReturnValue", "target_node": "spawn",     "target_pin": "SpawnTransform"},
        {"source_node": "get_class", "source_pin": "PipeClass",   "target_node": "spawn",     "target_pin": "Class"},
    ]
}

# ─── Set PipeClass on GameMode CDO ────────────────────────────────────────────

SET_PIPE_CLASS_CODE = f"""
import unreal, json
try:
    gm_bp   = unreal.EditorAssetLibrary.load_asset('{GM_BP}')
    pipe_bp = unreal.EditorAssetLibrary.load_asset('{PIPE_BP}')
    if not gm_bp or not pipe_bp:
        print(json.dumps({{'success': False, 'message': 'BP not found'}}))
    else:
        pipe_cls = pipe_bp.generated_class()
        gm_cls   = gm_bp.generated_class()
        if pipe_cls and gm_cls:
            cdo = gm_cls.get_default_object()
            cdo.set_editor_property('PipeClass', pipe_cls)
            unreal.EditorAssetLibrary.save_asset(gm_bp.get_path_name(), only_if_is_dirty=False)
            print(json.dumps({{'success': True, 'message': 'PipeClass set on GameMode CDO'}}))
        else:
            print(json.dumps({{'success': False, 'message': 'Generated class not available, compile first'}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

# ─── Add components (SphereComponent for bird, Boxes for pipe) ───────────────

ADD_BIRD_COMPONENTS_CODE = f"""
import unreal, json
try:
    bp = unreal.EditorAssetLibrary.load_asset('{BIRD_BP}')
    if not bp:
        print(json.dumps({{'success': False, 'message': 'Bird BP not found'}}))
    else:
        # Access the SimpleConstructionScript to add components
        scs = bp.simple_construction_script
        all_nodes = list(scs.get_all_nodes())
        existing_names = [n.get_variable_name() for n in all_nodes]

        added = []
        if 'CollisionSphere' not in existing_names:
            try:
                node = scs.add_new_node_here(unreal.SphereComponent)
                if node:
                    node.set_editor_property('variable_name', 'CollisionSphere')
                    comp = node.component_template
                    if comp:
                        comp.set_editor_property('sphere_radius', 30.0)
                    added.append('CollisionSphere')
            except Exception as e:
                pass

        if 'BirdMesh' not in existing_names:
            try:
                node = scs.add_new_node_here(unreal.StaticMeshComponent)
                if node:
                    node.set_editor_property('variable_name', 'BirdMesh')
                    comp = node.component_template
                    if comp:
                        mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Sphere')
                        if mesh:
                            comp.set_editor_property('static_mesh', mesh)
                    added.append('BirdMesh')
            except Exception as e:
                pass

        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        print(json.dumps({{'success': True, 'added': added}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

ADD_PIPE_COMPONENTS_CODE = f"""
import unreal, json
try:
    bp = unreal.EditorAssetLibrary.load_asset('{PIPE_BP}')
    if not bp:
        print(json.dumps({{'success': False, 'message': 'Pipe BP not found'}}))
    else:
        scs = bp.simple_construction_script
        all_nodes = list(scs.get_all_nodes())
        existing_names = [n.get_variable_name() for n in all_nodes]

        added = []
        cube_mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')

        for name, z_offset, scale_z in [('TopPipe', 350.0, 5.0), ('BottomPipe', -350.0, 5.0)]:
            if name not in existing_names:
                try:
                    node = scs.add_new_node_here(unreal.StaticMeshComponent)
                    if node:
                        node.set_editor_property('variable_name', name)
                        comp = node.component_template
                        if comp and cube_mesh:
                            comp.set_editor_property('static_mesh', cube_mesh)
                            comp.set_editor_property('relative_location', unreal.Vector(0, 0, z_offset))
                            comp.set_editor_property('relative_scale3d', unreal.Vector(1, 1, scale_z))
                    added.append(name)
                except Exception as e:
                    pass

        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        print(json.dumps({{'success': True, 'added': added}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

# ─── Place bird and set game mode ─────────────────────────────────────────────

PLACE_BIRD_CODE = f"""
import unreal, json
try:
    bird_bp = unreal.EditorAssetLibrary.load_asset('{BIRD_BP}')
    if not bird_bp:
        print(json.dumps({{'success': False, 'message': 'Bird BP not found'}}))
    else:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actor = subsystem.spawn_actor_from_object(bird_bp, unreal.Vector(0, 0, 0))
        if actor:
            actor.set_actor_label('FlappyBird')
            print(json.dumps({{'success': True, 'actor': actor.get_actor_label()}}))
        else:
            print(json.dumps({{'success': False, 'message': 'Failed to spawn bird'}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

SET_GAMEMODE_CODE = f"""
import unreal, json
try:
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    gm_class = unreal.load_class(None, '{GM_BP}_C')
    if not gm_class:
        print(json.dumps({{'success': False, 'message': 'GameMode class not found'}}))
    else:
        for prop in ['default_game_mode', 'game_mode_override', 'GameModeOverride']:
            try:
                ws.set_editor_property(prop, gm_class)
                break
            except:
                pass
        print(json.dumps({{'success': True, 'message': 'GameMode set'}}))
except Exception as e:
    print(json.dumps({{'success': False, 'error': str(e)}}))
"""

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Flappy Bird Creator for Unreal Engine ===\n")

    # 1. Create Blueprint assets
    print("[1/10] Creating Blueprint assets...")
    r = exec_py(CREATE_ASSETS_CODE)
    ok("Create assets", r)

    # 2. Add variables to Bird
    print("[2/10] Adding variables...")
    bird_vars = [
        ("BirdVelocity", "real",  "float", "0.0"),
        ("bIsDead",      "bool",  "",      "false"),
        ("FlapStrength", "real",  "float", "800.0"),
        ("Gravity",      "real",  "float", "-2000.0"),
    ]
    r = exec_py(add_variables_code(BIRD_BP, bird_vars))
    ok("  Bird variables", r)

    pipe_vars = [("MoveSpeed", "real", "float", "400.0")]
    r = exec_py(add_variables_code(PIPE_BP, pipe_vars))
    ok("  Pipe variables", r)

    gm_vars = [
        ("Score",     "int",   "",  "0"),
        ("PipeClass", "class", "",  ""),
    ]
    r = exec_py(add_variables_code(GM_BP, gm_vars))
    ok("  GameMode variables", r)

    # 3. Add components
    print("[3/10] Adding components...")
    r = exec_py(ADD_BIRD_COMPONENTS_CODE)
    ok("  Bird components (SphereCollision + BirdMesh)", r)
    r = exec_py(ADD_PIPE_COMPONENTS_CODE)
    ok("  Pipe components (TopPipe + BottomPipe cubes)", r)

    # 4. Initial compile
    print("[4/10] Compiling Blueprints (pass 1)...")
    ok("  Bird compile", compile_bp(BIRD_BP))
    ok("  Pipe compile", compile_bp(PIPE_BP))
    ok("  GameMode compile", compile_bp(GM_BP))

    # 5. Build Bird event graph
    print("[5/10] Building Bird event graph...")
    r = build_graph(BIRD_BP, BIRD_GRAPH)
    ok("  Bird graph", r)

    # 6. Build Pipe event graph
    print("[6/10] Building Pipe event graph...")
    r = build_graph(PIPE_BP, PIPE_GRAPH)
    ok("  Pipe graph", r)

    # 7. Build GameMode event graph
    print("[7/10] Building GameMode event graph...")
    r = build_graph(GM_BP, GM_GRAPH)
    ok("  GameMode graph", r)

    # 8. Final compile
    print("[8/10] Compiling Blueprints (pass 2)...")
    ok("  Bird compile", compile_bp(BIRD_BP))
    ok("  Pipe compile", compile_bp(PIPE_BP))
    ok("  GameMode compile", compile_bp(GM_BP))

    # 9. Set PipeClass reference on GameMode CDO
    print("[9/10] Wiring up PipeClass reference...")
    r = exec_py(SET_PIPE_CLASS_CODE)
    ok("  PipeClass → GameMode CDO", r)

    # 10. Input setup + game mode + place bird
    print("[10/10] Final setup...")

    # Create IA_Flap
    r = call_ue("UnrealMCPython.game_actions", "ue_add_input_action",
                {"asset_path": IA_FLAP, "value_type": "Bool"})
    ok("  IA_Flap created", r)

    # Create IMC_Flappy with SpaceBar → IA_Flap
    r = call_ue("UnrealMCPython.game_actions", "ue_add_input_mapping",
                {"mapping_context_path": IMC_FLAPPY,
                 "action_path": IA_FLAP,
                 "key_name": "SpaceBar"})
    ok("  SpaceBar → IA_Flap mapping", r)

    # Set game mode on current level
    r = exec_py(SET_GAMEMODE_CODE)
    ok("  GameMode set on level", r)

    # Place bird
    r = exec_py(PLACE_BIRD_CODE)
    ok("  Bird placed in level", r)

    print("\n=== Done! ===")
    print("""
Next steps:
  1. Open BP_FlappyBird -> Class Defaults -> Auto Possess Player = Player 0
  2. Open BP_FlappyGameMode -> verify PipeClass is set to BP_FlappyPipe
  3. Add a Camera actor (Y=-500, looking +Y direction)
  4. Press Play -- Space to flap, avoid the pipes!

  If pipes don't spawn: open BP_FlappyGameMode EventGraph,
  manually set PipeClass variable default to BP_FlappyPipe.
""")


if __name__ == '__main__':
    try:
        main()
    except ConnectionRefusedError:
        print("ERROR: Cannot connect to Unreal Engine (port 12029).")
        print("Make sure UE is open with the UnrealMCPython plugin active.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
