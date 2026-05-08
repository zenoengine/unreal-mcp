# unreal-mcp Feature Roadmap

Five feature branches planned for implementation after Flappy Bird baseline.

---

## Branch 1: `feat/blueprint-component-mgmt`

**Goal:** Full component lifecycle management via Python — currently only `AddComponentToBlueprint` exists; there is no way to remove, list, or reconfigure components.

**New UFUNCTIONs in `MCPythonHelper.cpp`:**

| Function | Signature | Notes |
|---|---|---|
| `ListBlueprintComponents` | `(UBlueprint*)` → JSON array | Returns `[{name, class, variable_name, is_native}]` |
| `RemoveComponentFromBlueprint` | `(UBlueprint*, FString name)` → JSON | Finds SCS node by variable name and removes it |
| `SetComponentProperty` | `(UBlueprint*, FString comp, FString prop, FString value)` → JSON | Calls `SetBlueprintCDOProperty` on the component |

**Implementation notes:**
- `ListBlueprintComponents`: iterate `Blueprint->SimpleConstructionScript->GetAllNodes()`, serialize each node's `ComponentClass`, `VariableName`, `ComponentTemplate`
- `RemoveComponentFromBlueprint`: `SCS->RemoveNodeAndPromoteChildren(Node)` — mark dirty + recompile
- `SetComponentProperty`: get CDO via `Blueprint->GeneratedClass->GetDefaultObject()`, find component subobject, call property setter chain already used in `SetBlueprintCDOProperty`

**Python wrappers (mcp-server):** `list_blueprint_components`, `remove_component_from_blueprint`, `set_component_property`

**Difficulty:** Medium (C++)  
**Estimated effort:** 2–3 hours

---

## Branch 2: `feat/graph-info-defaultobject`

**Goal:** `GetBlueprintGraphInfo` currently only serializes `Pin->DefaultValue` (a string). Object-type pins store their value in `Pin->DefaultObject`, so they appear as empty strings in diagnostics — causing confusion and forcing workarounds.

**Change:** In `GetBlueprintGraphInfo` pin serialization loop, add:

```cpp
if (Pin->DefaultObject)
{
    PinObj->SetStringField(TEXT("default_object"), Pin->DefaultObject->GetPathName());
}
```

**Result:** Pin info now includes `"default_object": "/Game/FlappyBird/SM_Bird.SM_Bird"` when an asset is wired.

**Affected file:** `MCPythonHelper.cpp` — single addition inside the pin serialization loop in `GetBlueprintGraphInfo`.

**Difficulty:** Easy (C++ — 3 lines)  
**Estimated effort:** 30 minutes

---

## Branch 3: `feat/umg-property-api`

**Goal:** Eliminate the low-level `get_editor_property` / `set_editor_property` boilerplate in every HUD script by exposing typed helpers through MCPythonHelper.

**New UFUNCTIONs:**

| Function | Purpose |
|---|---|
| `UmgGetWidgetProperty(UBlueprint*, FString widget, FString prop)` | Returns JSON `{value, type}` |
| `UmgSetWidgetProperty(UBlueprint*, FString widget, FString prop, FString value)` | Sets string/numeric/bool properties |
| `UmgSetSlotLayout(UBlueprint*, FString widget, float anchorMinX, float anchorMinY, float anchorMaxX, float anchorMaxY, float offsetX, float offsetY, float sizeX, float sizeY)` | Sets CanvasPanelSlot AnchorData in one call |
| `UmgSetTextStyle(UBlueprint*, FString widget, int32 fontSize, float r, float g, float b, float a, int32 outlineSize)` | Sets font size + color + outline in one call |

**Implementation notes:**
- `UmgSetSlotLayout`: mirrors what `fix_hud_layout.py` does manually — find widget, get slot, cast to `UCanvasPanelSlot`, set `LayoutData.Anchors`, `LayoutData.Offsets`, `LayoutData.Alignment`
- `UmgSetTextStyle`: find widget, cast to `UTextBlock`, set `Font.Size`, `ColorAndOpacity`, `Font.OutlineSettings.OutlineSize`
- These reduce a 20-line Python block to a single function call

**Difficulty:** Medium (C++)  
**Estimated effort:** 3–4 hours

---

## Branch 4: `feat/level-tools`

**Goal:** Manage levels entirely from Python scripts — no manual editor interaction for world setup.

**New Python helpers (mcp-server/unreal_mcp_server.py or new module):**

| MCP Tool | Underlying API |
|---|---|
| `create_level(name, path)` | `unreal.EditorLevelLibrary.new_level(path)` |
| `load_level(path)` | `unreal.EditorLevelLibrary.load_level(path)` |
| `set_game_mode(level_path, gm_class_path)` | Set `AWorldSettings.DefaultGameMode` via CDO or world settings object |
| `list_level_actors(class_filter)` | `unreal.EditorLevelLibrary.get_all_level_actors()` filtered by class |
| `set_world_settings(gravity, time_dilation)` | Get `WorldSettings`, set `GlobalGravityZ`, `TimeDilation` |
| `place_actor(class_path, location, rotation)` | `unreal.EditorLevelLibrary.spawn_actor_from_class()` |

**Implementation notes:**
- All pure Python — no C++ required
- `set_game_mode`: `world_settings = unreal.EditorLevelLibrary.get_game_world().get_world_settings(); world_settings.set_editor_property('default_game_mode', gm_class)`
- Wrap in the standard MCP TCP dispatch pattern

**Difficulty:** Easy (Python)  
**Estimated effort:** 2 hours

---

## Branch 5: `feat/graph-autolayout`

**Goal:** After programmatic graph construction, nodes pile up at (0,0). Auto-layout distributes them into a left-to-right DAG that matches Unreal's visual style.

**Algorithm:**
1. Build adjacency list from `GetBlueprintGraphInfo` pin connections
2. Topological sort (Kahn's algorithm)
3. Assign column = max(predecessor columns) + 1
4. Within each column, assign row by order of appearance
5. Map (col, row) → (col * 250, row * 150) pixel positions
6. Call `SetBlueprintNodePosition(bp, graph, node_guid, x, y)` for each node

**New MCP Tool:** `auto_layout_graph(blueprint_path, graph_name)`

**New UFUNCTION (if needed):** `SetBlueprintNodePosition(UBlueprint*, FString graph, FString node_guid, float x, float y)` — alternatively use existing `set_node_position` if already present in server.

**Implementation notes:**
- Python-only if `SetBlueprintNodePosition` already exists in the MCP server
- If not, add the UFUNCTION in C++ (2 lines: find node by GUID, set `NodePosX`/`NodePosY`)
- Entry-point nodes (BeginPlay, Tick, custom events) always placed at column 0

**Difficulty:** Medium (Python algorithm + possibly 1 C++ helper)  
**Estimated effort:** 3 hours

---

## Implementation Order

Recommended sequence based on impact vs. effort:

| # | Branch | Why first |
|---|---|---|
| 1 | `feat/graph-info-defaultobject` | 30-min fix, eliminates ongoing diagnostic confusion |
| 2 | `feat/level-tools` | Pure Python, unblocks future level automation |
| 3 | `feat/umg-property-api` | Cleans up all future HUD work |
| 4 | `feat/blueprint-component-mgmt` | Enables full BP authoring without manual editor |
| 5 | `feat/graph-autolayout` | Quality-of-life polish after core tools are solid |

---

## Branch Naming Convention

```
git checkout -b feat/graph-info-defaultobject
git checkout -b feat/level-tools
git checkout -b feat/umg-property-api
git checkout -b feat/blueprint-component-mgmt
git checkout -b feat/graph-autolayout
```

Each branch targets a focused, reviewable diff. C++ branches require full rebuild of the plugin before testing.
