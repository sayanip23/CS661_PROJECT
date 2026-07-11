import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
import time

def create_global_notifications():
    """
    Returns the container for global toast notifications.
    Positioned fixed at the bottom right.
    """
    return html.Div(
        id="toast-container",
        className="toast-container position-fixed bottom-0 end-0 p-3",
        style={"zIndex": "1090"}
    )

# The notification bus takes dictionary payloads:
# {"message": "Saved successfully", "type": "success", "icon": "bi-check-circle", "duration": 4000, "timestamp": 12345}

@callback(
    Output("toast-container", "children"),
    Input("notification-bus", "data"),
    State("toast-container", "children"),
    prevent_initial_call=True
)
def render_notification(payload, current_children):
    if not payload or "message" not in payload:
        return no_update
        
    current_children = current_children or []
    
    msg = payload.get("message", "")
    msg_type = payload.get("type", "info")
    icon = payload.get("icon", "bi-info-circle")
    duration = payload.get("duration", 4000)
    
    # Map types to bootstrap colors
    color_map = {
        "success": "success",
        "error": "danger",
        "warning": "warning",
        "info": "primary"
    }
    
    color = color_map.get(msg_type, "primary")
    
    new_toast = dbc.Toast(
        [html.I(className=f"bi {icon} me-2"), html.Span(msg)],
        id={"type": "toast", "index": str(time.time())},
        header="Notification" if msg_type != "error" else "Error",
        is_open=True,
        dismissable=True,
        duration=duration,
        color=color,
        className=f"mb-2 text-white bg-{color} border-0 shadow-lg fw-bold"
    )
    
    # Keep only the latest 5 toasts to prevent clutter
    current_children.append(new_toast)
    if len(current_children) > 5:
        current_children = current_children[-5:]
        
    return current_children
