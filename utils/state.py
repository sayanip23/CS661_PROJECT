"""
utils/state.py

Defines standard event types and helper functions for the Global Event Bus.
Pages can dispatch events to the `event-bus` store in app.py.
"""
from dash import no_update

# Event Types
EVENT_COMPANY_SELECTED = "COMPANY_SELECTED"
EVENT_SECTOR_SELECTED = "SECTOR_SELECTED"
EVENT_DATE_RANGE_CHANGED = "DATE_RANGE_CHANGED"
EVENT_THEME_CHANGED = "THEME_CHANGED"
EVENT_WATCHLIST_UPDATED = "WATCHLIST_UPDATED"
def create_event(event_type: str, payload: dict) -> dict:
    """Creates a standard event dictionary for the Event Bus."""
    return {
        "type": event_type,
        "payload": payload
    }
