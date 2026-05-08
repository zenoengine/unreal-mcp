# Copyright (c) 2025 GenOrca. All Rights Reserved.

import unreal
import json
import traceback


def ue_umg_get_widget_info(asset_path: str = None) -> str:
    """Returns JSON describing the widget tree of a WidgetBlueprint."""
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        return unreal.MCPythonHelper.umg_get_widget_info(bp)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_add_widget(asset_path: str = None, widget_type: str = None,
                      widget_name: str = None, parent_name: str = "") -> str:
    """Adds a widget to the widget tree of a WidgetBlueprint."""
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_type:
        return json.dumps({"success": False, "message": "Required parameter 'widget_type' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        result = unreal.MCPythonHelper.umg_add_widget(bp, widget_type, widget_name, parent_name or "")
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        return result
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_remove_widget(asset_path: str = None, widget_name: str = None) -> str:
    """Removes a widget from the widget tree of a WidgetBlueprint."""
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        result = unreal.MCPythonHelper.umg_remove_widget(bp, widget_name)
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        return result
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_set_slot_layout(asset_path: str = None, widget_name: str = None,
                            anchor_min_x: float = 0.5, anchor_min_y: float = 0.5,
                            anchor_max_x: float = 0.5, anchor_max_y: float = 0.5,
                            offset_x: float = 0.0, offset_y: float = 0.0,
                            size_x: float = 100.0, size_y: float = 40.0) -> str:
    """
    Sets the CanvasPanelSlot layout (anchors + offset + size) on a widget.
    anchor_min/max are 0..1 fractions of the canvas. offset_x/y are pixel
    offsets from the anchor point (centre-aligned). size_x/y are pixel dimensions.
    """
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        result = unreal.MCPythonHelper.umg_set_slot_layout(
            bp, widget_name,
            anchor_min_x, anchor_min_y, anchor_max_x, anchor_max_y,
            offset_x, offset_y, size_x, size_y
        )
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        return result
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_set_text_style(asset_path: str = None, widget_name: str = None,
                           font_size: int = 24,
                           color_r: float = 1.0, color_g: float = 1.0,
                           color_b: float = 1.0, color_a: float = 1.0,
                           outline_size: int = 0) -> str:
    """
    Sets font size, text color, and outline size on a TextBlock widget.
    color_r/g/b/a are 0..1 linear colour values.
    outline_size=-1 leaves outline unchanged.
    """
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        result = unreal.MCPythonHelper.umg_set_text_style(
            bp, widget_name, font_size,
            color_r, color_g, color_b, color_a,
            outline_size
        )
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        return result
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_get_widget_property(asset_path: str = None, widget_name: str = None,
                                property_name: str = None) -> str:
    """Gets the value of an editor property on a named widget."""
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    if not property_name:
        return json.dumps({"success": False, "message": "Required parameter 'property_name' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        return unreal.MCPythonHelper.umg_get_widget_property(bp, widget_name, property_name)
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})


def ue_umg_set_widget_property(asset_path: str = None, widget_name: str = None,
                                property_name: str = None, value: str = None) -> str:
    """Sets the value of an editor property on a named widget from a string."""
    if not asset_path:
        return json.dumps({"success": False, "message": "Required parameter 'asset_path' is missing."})
    if not widget_name:
        return json.dumps({"success": False, "message": "Required parameter 'widget_name' is missing."})
    if not property_name:
        return json.dumps({"success": False, "message": "Required parameter 'property_name' is missing."})
    if value is None:
        return json.dumps({"success": False, "message": "Required parameter 'value' is missing."})
    try:
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        if bp is None:
            return json.dumps({"success": False, "message": f"Asset not found: '{asset_path}'."})
        result = unreal.MCPythonHelper.umg_set_widget_property(bp, widget_name, property_name, value)
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name(), only_if_is_dirty=False)
        return result
    except Exception as e:
        return json.dumps({"success": False, "message": str(e), "traceback": traceback.format_exc()})
