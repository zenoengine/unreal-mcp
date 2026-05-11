# Copyright (c) 2025 GenOrca. All Rights Reserved.

from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP

from unreal_mcp.core import send_unreal_action

LEVEL_ACTIONS_MODULE = "UnrealMCPython.level_actions"

level_mcp = FastMCP(
    name="LevelMCP",
    description="Tools for creating, loading, and configuring Unreal Engine levels."
)


@level_mcp.tool(
    name="create_level",
    description=(
        "Creates a new empty level at the given content-browser path and opens it. "
        "Example: '/Game/Maps/MyLevel'."
    ),
    tags={"unreal", "level", "create", "map"}
)
async def create_level(
    level_path: Annotated[str, Field(description="Content-browser path for the new level (e.g. '/Game/Maps/MyLevel').")]
) -> dict:
    return await send_unreal_action(LEVEL_ACTIONS_MODULE, {"level_path": level_path})


@level_mcp.tool(
    name="load_level",
    description="Opens an existing level in the Unreal editor by its content-browser path.",
    tags={"unreal", "level", "load", "open", "map"}
)
async def load_level(
    level_path: Annotated[str, Field(description="Content-browser path of the level to open (e.g. '/Game/Maps/MyLevel').")]
) -> dict:
    return await send_unreal_action(LEVEL_ACTIONS_MODULE, {"level_path": level_path})


@level_mcp.tool(
    name="list_level_actors",
    description=(
        "Lists all actors in the currently open level. "
        "Optionally filter by a partial class name (e.g. 'StaticMeshActor', 'BP_Bird')."
    ),
    tags={"unreal", "level", "actors", "list", "query"}
)
async def list_level_actors(
    class_filter: Annotated[Optional[str], Field(
        description="Optional partial class name to filter results (case-insensitive)."
    )] = None
) -> dict:
    return await send_unreal_action(LEVEL_ACTIONS_MODULE, {"class_filter": class_filter})


@level_mcp.tool(
    name="set_world_settings",
    description=(
        "Modifies World Settings of the current level. "
        "gravity sets GlobalGravityZ (negative = downward, standard Earth ≈ -980). "
        "time_dilation sets global time multiplier (1.0 = normal, 0.5 = half speed)."
    ),
    tags={"unreal", "level", "world", "settings", "gravity", "physics"}
)
async def set_world_settings(
    gravity: Annotated[Optional[float], Field(
        description="GlobalGravityZ value (e.g. -980 for Earth gravity). Negative = downward."
    )] = None,
    time_dilation: Annotated[Optional[float], Field(
        description="Global time dilation multiplier. 1.0 = normal speed."
    )] = None
) -> dict:
    return await send_unreal_action(LEVEL_ACTIONS_MODULE, {"gravity": gravity, "time_dilation": time_dilation})

