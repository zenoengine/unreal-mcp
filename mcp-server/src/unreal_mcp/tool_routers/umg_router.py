# Copyright (c) 2025 GenOrca. All Rights Reserved.

from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP

from unreal_mcp.core import send_unreal_action

UMG_ACTIONS_MODULE = "UnrealMCPython.umg_actions"

umg_mcp = FastMCP(
    name="UmgMCP",
    description="Tools for querying and modifying Unreal Engine UMG widget blueprints."
)


@umg_mcp.tool(
    name="get_widget_info",
    description="Returns a JSON description of all widgets in a WidgetBlueprint's widget tree.",
    tags={"unreal", "umg", "widget", "info", "query"}
)
async def get_widget_info(
    asset_path: Annotated[str, Field(description="Content-browser path to the WidgetBlueprint (e.g. '/Game/UI/WBP_HUD').")]
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {"asset_path": asset_path})


@umg_mcp.tool(
    name="add_widget",
    description=(
        "Adds a new widget to a WidgetBlueprint's widget tree. "
        "widget_type is a UMG class name such as 'TextBlock', 'Button', 'Image', 'Border', 'CanvasPanel', 'VerticalBox', 'HorizontalBox'. "
        "parent_name is the name of the parent widget; leave empty to use the root panel."
    ),
    tags={"unreal", "umg", "widget", "add", "create"}
)
async def add_widget(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_type: Annotated[str, Field(description="UMG widget class name (e.g. 'TextBlock', 'Button', 'Image').")],
    widget_name: Annotated[str, Field(description="Unique name for the new widget.")],
    parent_name: Annotated[str, Field(description="Name of the parent widget. Leave empty to attach to root.")] = ""
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_type": widget_type,
        "widget_name": widget_name,
        "parent_name": parent_name,
    })


@umg_mcp.tool(
    name="remove_widget",
    description="Removes a named widget from a WidgetBlueprint's widget tree.",
    tags={"unreal", "umg", "widget", "remove", "delete"}
)
async def remove_widget(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_name: Annotated[str, Field(description="Name of the widget to remove.")]
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_name": widget_name,
    })


@umg_mcp.tool(
    name="set_slot_layout",
    description=(
        "Sets the CanvasPanelSlot layout on a widget in one call. "
        "anchor_min/max are 0..1 fractions of the canvas (e.g. 0.5,0.5 = centre). "
        "offset_x/y are pixel offsets from the anchor point. "
        "size_x/y are the widget's pixel dimensions. "
        "Alignment is always (0.5, 0.5) — the anchor lands at the widget centre."
    ),
    tags={"unreal", "umg", "widget", "layout", "position", "anchor", "canvas"}
)
async def set_slot_layout(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_name: Annotated[str, Field(description="Name of the widget to reposition.")],
    anchor_min_x: Annotated[float, Field(description="Minimum anchor X (0..1).")] = 0.5,
    anchor_min_y: Annotated[float, Field(description="Minimum anchor Y (0..1).")] = 0.5,
    anchor_max_x: Annotated[float, Field(description="Maximum anchor X (0..1). Same as min for point anchors.")] = 0.5,
    anchor_max_y: Annotated[float, Field(description="Maximum anchor Y (0..1). Same as min for point anchors.")] = 0.5,
    offset_x: Annotated[float, Field(description="Pixel X offset from anchor (positive = right).")] = 0.0,
    offset_y: Annotated[float, Field(description="Pixel Y offset from anchor (positive = down).")] = 0.0,
    size_x: Annotated[float, Field(description="Widget width in pixels.")] = 100.0,
    size_y: Annotated[float, Field(description="Widget height in pixels.")] = 40.0,
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_name": widget_name,
        "anchor_min_x": anchor_min_x,
        "anchor_min_y": anchor_min_y,
        "anchor_max_x": anchor_max_x,
        "anchor_max_y": anchor_max_y,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "size_x": size_x,
        "size_y": size_y,
    })


@umg_mcp.tool(
    name="set_text_style",
    description=(
        "Sets the font size, text color, and outline size on a TextBlock widget in one call. "
        "Colors are linear 0..1 values. outline_size=-1 leaves the outline unchanged."
    ),
    tags={"unreal", "umg", "widget", "text", "font", "color", "style"}
)
async def set_text_style(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_name: Annotated[str, Field(description="Name of the TextBlock widget.")],
    font_size: Annotated[int, Field(description="Font size in points.")] = 24,
    color_r: Annotated[float, Field(description="Red channel (0..1).")] = 1.0,
    color_g: Annotated[float, Field(description="Green channel (0..1).")] = 1.0,
    color_b: Annotated[float, Field(description="Blue channel (0..1).")] = 1.0,
    color_a: Annotated[float, Field(description="Alpha channel (0..1).")] = 1.0,
    outline_size: Annotated[int, Field(description="Outline size in pixels. Pass -1 to leave unchanged.")] = 0,
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_name": widget_name,
        "font_size": font_size,
        "color_r": color_r,
        "color_g": color_g,
        "color_b": color_b,
        "color_a": color_a,
        "outline_size": outline_size,
    })


@umg_mcp.tool(
    name="get_widget_property",
    description=(
        "Gets the value of a C++ UPROPERTY on a named widget. "
        "property_name must be the C++ member name (PascalCase), e.g. 'Text', 'bIsEnabled', 'ColorAndOpacity'. "
        "Returns the value as a string along with the C++ type name."
    ),
    tags={"unreal", "umg", "widget", "property", "get", "inspect"}
)
async def get_widget_property(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_name: Annotated[str, Field(description="Name of the target widget.")],
    property_name: Annotated[str, Field(description="C++ UPROPERTY name (PascalCase), e.g. 'Text', 'bIsEnabled', 'ColorAndOpacity'.")]
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_name": widget_name,
        "property_name": property_name,
    })


@umg_mcp.tool(
    name="set_widget_property",
    description=(
        "Sets a simple C++ UPROPERTY on a named widget from a string value. "
        "property_name must be the C++ member name (PascalCase), e.g. 'Text', 'bIsEnabled'. "
        "Supports bool ('True'/'False'), int, float, FText, and FString properties. "
        "For struct properties (layout, font), use set_slot_layout or set_text_style instead."
    ),
    tags={"unreal", "umg", "widget", "property", "set"}
)
async def set_widget_property(
    asset_path: Annotated[str, Field(description="Content path to the WidgetBlueprint.")],
    widget_name: Annotated[str, Field(description="Name of the target widget.")],
    property_name: Annotated[str, Field(description="C++ UPROPERTY name (PascalCase), e.g. 'Text', 'bIsEnabled', 'ToolTipText'.")],
    value: Annotated[str, Field(description="String representation of the value to set.")]
) -> dict:
    return await send_unreal_action(UMG_ACTIONS_MODULE, {
        "asset_path": asset_path,
        "widget_name": widget_name,
        "property_name": property_name,
        "value": value,
    })
