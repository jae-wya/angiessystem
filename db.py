"""
db.py — Supabase data layer for Angie's Florist v3.0
Replaces all JSON file read/write with Supabase REST calls.
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional
import uuid
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────
# GENERIC HELPERS
# ─────────────────────────────────────────────────────────────

def _select(table: str, filters: dict = None) -> list:
    sb = get_supabase()
    q = sb.table(table).select("*")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    res = q.execute()
    return res.data or []


def _insert(table: str, row: dict) -> dict:
    sb = get_supabase()
    res = sb.table(table).insert(row).execute()
    return res.data[0] if res.data else {}


def _update(table: str, row_id: str, updates: dict) -> dict:
    sb = get_supabase()
    res = sb.table(table).update(updates).eq("id", row_id).execute()
    return res.data[0] if res.data else {}


def _delete(table: str, row_id: str) -> bool:
    sb = get_supabase()
    sb.table(table).delete().eq("id", row_id).execute()
    return True


def _upsert(table: str, row: dict) -> dict:
    sb = get_supabase()
    res = sb.table(table).upsert(row).execute()
    return res.data[0] if res.data else {}


# ─────────────────────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────────────────────

def get_orders() -> list:
    return _select("orders")


def save_order(order: dict) -> dict:
    """Insert or upsert a single order."""
    return _upsert("orders", order)


def update_order(order_id: str, updates: dict) -> dict:
    updates["updated_at"] = datetime.now().isoformat()
    return _update("orders", order_id, updates)


def delete_order(order_id: str) -> bool:
    return _delete("orders", order_id)


def update_order_status(order_id: str, new_status: str):
    updates = {
        "status": new_status,
        "updated_at": datetime.now().isoformat(),
    }
    if new_status == "Delivered":
        updates["delivered_at"] = datetime.now().isoformat()
    elif new_status == "Picked Up":
        updates["picked_up_at"] = datetime.now().isoformat()
    _update("orders", order_id, updates)


# ─────────────────────────────────────────────────────────────
# INVENTORY
# ─────────────────────────────────────────────────────────────

def get_inventory() -> list:
    return _select("inventory")


def save_inventory_item(item: dict) -> dict:
    return _upsert("inventory", item)


def update_inventory_item(item_id: str, updates: dict) -> dict:
    return _update("inventory", item_id, updates)


def delete_inventory_item(item_id: str) -> bool:
    return _delete("inventory", item_id)


# ─────────────────────────────────────────────────────────────
# WASTE
# ─────────────────────────────────────────────────────────────

def get_waste() -> list:
    return _select("waste")


def save_waste_entry(entry: dict) -> dict:
    return _insert("waste", entry)


def delete_waste_entry(entry_id: str) -> bool:
    return _delete("waste", entry_id)


# ─────────────────────────────────────────────────────────────
# FLORISTS
# ─────────────────────────────────────────────────────────────

def get_florists() -> list:
    return _select("florists")


def save_florist(florist: dict) -> dict:
    return _insert("florists", florist)


def delete_florist(florist_id: str) -> bool:
    return _delete("florists", florist_id)


# ─────────────────────────────────────────────────────────────
# RIDERS
# ─────────────────────────────────────────────────────────────

def get_riders() -> list:
    return _select("riders")


def save_rider(rider: dict) -> dict:
    return _insert("riders", rider)


def delete_rider(rider_id: str) -> bool:
    return _delete("riders", rider_id)


# ─────────────────────────────────────────────────────────────
# PAYMENT TRANSACTIONS
# ─────────────────────────────────────────────────────────────

def get_payment_transactions() -> list:
    return _select("payment_transactions")


def save_payment_transaction(txn: dict) -> dict:
    return _insert("payment_transactions", txn)


# ─────────────────────────────────────────────────────────────
# HR LOGS
# ─────────────────────────────────────────────────────────────

def get_hr_logs() -> list:
    return _select("hr_logs")


def save_hr_log(entry: dict) -> dict:
    return _insert("hr_logs", entry)


# ─────────────────────────────────────────────────────────────
# FLORIST CAPACITY HELPER
# ─────────────────────────────────────────────────────────────

def get_florist_active_load(florist_name: str) -> int:
    orders = get_orders()
    terminal = {"Delivered", "Picked Up", "Cancelled", "Failed Delivery"}
    return len([
        o for o in orders
        if o.get("assigned_florist") == florist_name
        and o.get("status") not in terminal
    ])
