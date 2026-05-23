from __future__ import annotations


def create_plugin(context):
    return {
        "plugin_id": context.plugin_id,
        "name": "JSON Formatter",
        "data_path": str(context.data_path),
        "handle": lambda action, payload: {
            "action": action,
            "plugin_id": context.plugin_id,
            "payload": payload,
        },
    }
