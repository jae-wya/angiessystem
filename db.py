"""
db.py — Supabase data layer for Angie's Florist v3.0
Replaces all JSON file read/write with Supabase REST calls.
Includes:
  - Cached reads (st.cache_data) for snappier navigation
  - Supabase Storage helpers for persistent file uploads
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional
import uuid
import hashlib
import secrets
from datetime import datetime

CACHE_TTL = 10  # seconds — balances freshness vs. speed for multi-user use
STORAGE_BUCKET = "angies-florist-uploads"


# ─────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────
# CACHE INVALIDATION
# ─────────────────────────────────────────────────────────────

def _invalidate_all():
    """Clear all cached reads. Called after any write so changes
    are immediately visible to the current user, and within
    CACHE_TTL seconds for everyone else."""
    st.cache_data.clear()


# ─────────────────────────────────────────────────────────────
# GENERIC HELPERS (uncached — internal use)
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
    _invalidate_all()
    return res.data[0] if res.data else {}


def _update(table: str, row_id: str, updates: dict) -> dict:
    sb = get_supabase()
    res = sb.table(table).update(updates).eq("id", row_id).execute()
    _invalidate_all()
    return res.data[0] if res.data else {}


def _delete(table: str, row_id: str) -> bool:
    sb = get_supabase()
    sb.table(table).delete().eq("id", row_id).execute()
    _invalidate_all()
    return True


def _upsert(table: str, row: dict) -> dict:
    sb = get_supabase()
    res = sb.table(table).upsert(row).execute()
    _invalidate_all()
    return res.data[0] if res.data else {}


# ─────────────────────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
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

@st.cache_data(ttl=CACHE_TTL)
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

@st.cache_data(ttl=CACHE_TTL)
def get_waste() -> list:
    return _select("waste")


def save_waste_entry(entry: dict) -> dict:
    return _insert("waste", entry)


def delete_waste_entry(entry_id: str) -> bool:
    return _delete("waste", entry_id)


# ─────────────────────────────────────────────────────────────
# FLORISTS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_florists() -> list:
    return _select("florists")


def save_florist(florist: dict) -> dict:
    return _insert("florists", florist)


def delete_florist(florist_id: str) -> bool:
    return _delete("florists", florist_id)


# ─────────────────────────────────────────────────────────────
# RIDERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_riders() -> list:
    return _select("riders")


def save_rider(rider: dict) -> dict:
    return _insert("riders", rider)


def delete_rider(rider_id: str) -> bool:
    return _delete("riders", rider_id)


# ─────────────────────────────────────────────────────────────
# PAYMENT TRANSACTIONS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_payment_transactions() -> list:
    return _select("payment_transactions")


def save_payment_transaction(txn: dict) -> dict:
    return _insert("payment_transactions", txn)


# ─────────────────────────────────────────────────────────────
# HR LOGS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
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


# ─────────────────────────────────────────────────────────────
# SUPABASE STORAGE — persistent file uploads
# ─────────────────────────────────────────────────────────────
#
# Files (inspiration pictures, proof of payment, proof of delivery,
# finished product photos) are stored in a Supabase Storage bucket
# instead of local disk — local disk on Streamlit Community Cloud is
# wiped on every restart/redeploy, so files would otherwise be lost.
#
# Make sure the bucket exists (see supabase_schema.sql for the
# one-time setup SQL / dashboard steps).

def upload_file(file_bytes: bytes, path: str, content_type: str = "application/octet-stream") -> Optional[str]:
    """
    Upload a file to Supabase Storage.
    `path` should be a unique path within the bucket, e.g.
    'orders/2025-06-13-MB-0001/inspo/photo1.jpg'
    Returns the public URL on success, or None on failure.
    """
    sb = get_supabase()
    try:
        sb.storage.from_(STORAGE_BUCKET).upload(
            path,
            file_bytes,
            {"content-type": content_type, "upsert": "true"},
        )
        return get_public_url(path)
    except Exception as e:
        st.error(f"⚠️ File upload failed: {e}")
        return None


def get_public_url(path: str) -> str:
    sb = get_supabase()
    return sb.storage.from_(STORAGE_BUCKET).get_public_url(path)


def delete_file(path: str) -> bool:
    sb = get_supabase()
    try:
        sb.storage.from_(STORAGE_BUCKET).remove([path])
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# STAFF ACCOUNTS — PIN-based login
# ─────────────────────────────────────────────────────────────

ROLES = ["Staff", "Florist", "Rider", "Branch Manager", "Super Admin"]


def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((salt + pin).encode()).hexdigest()


def make_pin_credentials(pin: str) -> tuple[str, str]:
    """Returns (salt, hash) for a new PIN."""
    salt = secrets.token_hex(8)
    return salt, _hash_pin(pin, salt)


@st.cache_data(ttl=CACHE_TTL)
def get_staff_accounts() -> list:
    return _select("staff_accounts")


def save_staff_account(account: dict) -> dict:
    return _insert("staff_accounts", account)


def update_staff_account(account_id: str, updates: dict) -> dict:
    return _update("staff_accounts", account_id, updates)


def delete_staff_account(account_id: str) -> bool:
    return _delete("staff_accounts", account_id)


def verify_login(pin: str) -> Optional[dict]:
    """Return the matching active staff account for this PIN, or None."""
    if not pin:
        return None
    accounts = get_staff_accounts()
    for a in accounts:
        if not a.get("active", True):
            continue
        if _hash_pin(pin, a.get("pin_salt", "")) == a.get("pin_hash"):
            return a
    return None


def pin_in_use(pin: str, exclude_id: str = None) -> bool:
    """Check if a PIN is already used by another active account."""
    accounts = get_staff_accounts()
    for a in accounts:
        if exclude_id and a.get("id") == exclude_id:
            continue
        if _hash_pin(pin, a.get("pin_salt", "")) == a.get("pin_hash"):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY AUTO-DEDUCTION
# ─────────────────────────────────────────────────────────────────────────────

def deduct_inventory_for_order(flower_items: list, branch: str) -> list:
    """
    Deduct flower quantities from inventory when an order is logged.
    Matches flower name (case-insensitive) against inventory items for the branch.
    Returns a list of warning strings for any issues found.
    """
    if not flower_items:
        return []

    inventory = get_inventory()
    warnings  = []

    for fi in flower_items:
        fname    = fi.get("flower", "").strip().lower()
        qty_used = int(fi.get("qty", 1))
        if not fname:
            continue

        match = next(
            (i for i in inventory
             if i.get("name", "").strip().lower() == fname
             and i.get("branch", "") == branch),
            None,
        )

        if match is None:
            warnings.append(
                f"⚠️ **{fi.get('flower')}** not found in inventory for **{branch}**. "
                f"Add it manually in 📦 Inventory."
            )
            continue

        new_qty = max(0, int(match.get("quantity", 0)) - qty_used)
        update_inventory_item(match["id"], {"quantity": new_qty})

        reorder = int(match.get("reorder_point", 10))
        if new_qty <= reorder:
            warnings.append(
                f"🔴 **{fi.get('flower')}** is now at **{new_qty} {match.get('unit','pcs')}** "
                f"— at or below reorder point ({reorder}). Consider restocking."
            )

    return warnings
