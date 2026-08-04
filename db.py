"""
db.py — Supabase data layer for Angie's Florist v3.0
Replaces all JSON file read/write with Supabase REST calls.
Includes:
  - Per-table cached reads (st.cache_data) for snappier navigation
  - Surgical cache invalidation — only the affected table is cleared on writes
    (previously: any write flushed ALL caches, causing thundering herd under load)
  - Supabase Storage helpers for persistent file uploads
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta

CACHE_TTL = 10  # seconds — balances freshness vs. speed for multi-user use
STORAGE_BUCKET = "angies-florist-uploads"


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN HELPERS — waybill QR and customer tracking
# ─────────────────────────────────────────────────────────────────────────────

def generate_rider_token() -> str:
    """Generate a secure token for the rider QR delivery page."""
    return secrets.token_urlsafe(6)


def generate_tracking_token() -> str:
    """Generate a secure token for the customer tracking page."""
    return secrets.token_urlsafe(6)


# ─────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────
# CACHE INVALIDATION — per-table (surgical)
# One write = only that table's cache is cleared.
# _invalidate_all() is kept as an emergency escape hatch only.
# ─────────────────────────────────────────────────────────────

def _invalidate_orders():           get_orders.clear()
def _invalidate_inventory():        get_inventory.clear()
def _invalidate_inventory_logs():   get_inventory_logs.clear()
def _invalidate_waste():            get_waste.clear()
def _invalidate_florists():         get_florists.clear()
def _invalidate_riders():           get_riders.clear()
def _invalidate_payment_txns():     get_payment_transactions.clear()
def _invalidate_hr():               get_hr_logs.clear()
def _invalidate_staff():            get_staff_accounts.clear()
def _invalidate_stock_count():      get_stock_count_entries.clear()
def _invalidate_expenses():         get_expenses.clear()
def _invalidate_branch_costs():     get_branch_fixed_costs.clear()

def _invalidate_all():
    """Emergency full cache flush. Do NOT call during normal operations."""
    st.cache_data.clear()


# ─────────────────────────────────────────────────────────────
# GENERIC HELPERS (uncached — internal use)
# NOTE: No auto-invalidation here. Each public write function
#       calls the correct _invalidate_<table>() itself.
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

@st.cache_data(ttl=CACHE_TTL)
def get_orders() -> list:
    return _select("orders")


def save_order(order: dict) -> dict:
    """Insert or upsert a single order. Auto-generates rider and tracking tokens if missing."""
    if not order.get("rider_token"):
        order["rider_token"] = generate_rider_token()
    if not order.get("tracking_token"):
        order["tracking_token"] = generate_tracking_token()
    result = _upsert("orders", order)
    _invalidate_orders()
    return result


def update_order(order_id: str, updates: dict) -> dict:
    updates["updated_at"] = datetime.now().isoformat()
    result = _update("orders", order_id, updates)
    _invalidate_orders()
    return result


def delete_order(order_id: str) -> bool:
    _delete("orders", order_id)
    _invalidate_orders()
    return True


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
    _invalidate_orders()


# ─────────────────────────────────────────────────────────────
# INVENTORY
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_inventory() -> list:
    return _select("inventory")


def save_inventory_item(item: dict) -> dict:
    result = _upsert("inventory", item)
    _invalidate_inventory()
    return result


def update_inventory_item(item_id: str, updates: dict) -> dict:
    result = _update("inventory", item_id, updates)
    _invalidate_inventory()
    return result


def delete_inventory_item(item_id: str) -> bool:
    _delete("inventory", item_id)
    _invalidate_inventory()
    return True


# ─────────────────────────────────────────────────────────────
# WASTE
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_waste() -> list:
    return _select("waste")


def save_waste_entry(entry: dict) -> dict:
    result = _insert("waste", entry)
    _invalidate_waste()
    return result


def delete_waste_entry(entry_id: str) -> bool:
    _delete("waste", entry_id)
    _invalidate_waste()
    return True


# ─────────────────────────────────────────────────────────────
# FLORISTS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_florists() -> list:
    return _select("florists")


def save_florist(florist: dict) -> dict:
    result = _insert("florists", florist)
    _invalidate_florists()
    return result


def delete_florist(florist_id: str) -> bool:
    _delete("florists", florist_id)
    _invalidate_florists()
    return True


# ─────────────────────────────────────────────────────────────
# RIDERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_riders() -> list:
    return _select("riders")


def save_rider(rider: dict) -> dict:
    result = _insert("riders", rider)
    _invalidate_riders()
    return result


def delete_rider(rider_id: str) -> bool:
    _delete("riders", rider_id)
    _invalidate_riders()
    return True


# ─────────────────────────────────────────────────────────────
# PAYMENT TRANSACTIONS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_payment_transactions() -> list:
    return _select("payment_transactions")


def save_payment_transaction(txn: dict) -> dict:
    result = _insert("payment_transactions", txn)
    _invalidate_payment_txns()
    return result


# ─────────────────────────────────────────────────────────────
# HR LOGS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_hr_logs() -> list:
    return _select("hr_logs")


def save_hr_log(entry: dict) -> dict:
    result = _insert("hr_logs", entry)
    _invalidate_hr()
    return result


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

def upload_file(file_bytes: bytes, path: str, content_type: str = "application/octet-stream") -> Optional[str]:
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
    result = _insert("staff_accounts", account)
    _invalidate_staff()
    return result


def update_staff_account(account_id: str, updates: dict) -> dict:
    result = _update("staff_accounts", account_id, updates)
    _invalidate_staff()
    return result


def delete_staff_account(account_id: str) -> bool:
    _delete("staff_accounts", account_id)
    _invalidate_staff()
    return True


def verify_login(pin: str) -> Optional[dict]:
    """Return the matching active staff account for this PIN, or None."""
    if not pin:
        return None
    try:
        accounts = _select("staff_accounts")
    except Exception:
        accounts = []
    for a in accounts:
        is_active = a.get("active")
        if is_active is False:
            continue
        stored_salt = a.get("pin_salt") or ""
        stored_hash = a.get("pin_hash") or ""
        if not stored_hash:
            continue
        if _hash_pin(pin, stored_salt) == stored_hash:
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
# SESSION TOKENS — persistent login across server restarts
# ─────────────────────────────────────────────────────────────────────────────

def create_session_token(account_id: str) -> str:
    """Create a persistent session token valid for 30 days. Returns the token."""
    token      = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    try:
        sb = get_supabase()
        sb.table("session_tokens").insert({
            "token":      token,
            "account_id": account_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
        }).execute()
    except Exception as e:
        st.error(f"⚠️ Session token creation failed: {e}")
    return token


def validate_session_token(token: str) -> Optional[dict]:
    """Validate a session token. Returns the account dict if valid, else None."""
    if not token:
        return None
    try:
        sb  = get_supabase()
        res = sb.table("session_tokens").select("*").eq("token", token).execute()
        if not res.data:
            return None

        row = res.data[0]

        # Check expiry
        if datetime.now().isoformat() > row.get("expires_at", ""):
            sb.table("session_tokens").delete().eq("token", token).execute()
            return None

        # Look up account
        accounts = _select("staff_accounts", {"id": row["account_id"]})
        if not accounts:
            return None

        account = accounts[0]
        if account.get("active") is False:
            return None

        return account

    except Exception:
        return None


def delete_session_token(token: str):
    """Remove a session token on logout."""
    try:
        get_supabase().table("session_tokens").delete().eq("token", token).execute()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY AUTO-DEDUCTION (color-aware, allows negative stock)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_flower_name(name: str) -> str:
    name = name.strip().upper()
    # Remove trailing S for plural matching
    # CARNATIONS → CARNATION, ROSES → ROSE, etc.
    # But preserve names that naturally end in S (STARGAZERS, GERBERAS)
    # Rule: if name ends in S and length > 4, try both with and without S
    return name


def _find_inventory_item(inventory: list, name: str, branch: str):
    name_upper = name.strip().upper()

    # 1. Exact match first
    match = next((i for i in inventory
        if i.get("name","").strip().upper() == name_upper
        and i.get("branch","") == branch), None)
    if match:
        return match

    # 2. Singular/plural fuzzy match
    # Try adding S (CARNATION → CARNATIONS)
    match = next((i for i in inventory
        if i.get("name","").strip().upper() == name_upper + "S"
        and i.get("branch","") == branch), None)
    if match:
        return match

    # Try removing S (CARNATIONS → CARNATION)
    if name_upper.endswith("S") and len(name_upper) > 3:
        match = next((i for i in inventory
            if i.get("name","").strip().upper() == name_upper[:-1]
            and i.get("branch","") == branch), None)
        if match:
            return match

    # 3. Try adding ES (ROSE → ROSES handled above,
    #    but BUNCH → BUNCHES)
    if not name_upper.endswith("S"):
        match = next((i for i in inventory
            if i.get("name","").strip().upper() == name_upper + "ES"
            and i.get("branch","") == branch), None)
        if match:
            return match

    return None


def deduct_inventory_for_order(flower_items: list, branch: str, order_id: str = "", logged_by: str = "") -> list:
    if not flower_items:
        return []
    inventory = get_inventory()
    warnings  = []

    def _find(name):
        return _find_inventory_item(inventory, name, branch)

    def _deduct(item, qty_used, display_name):
        current_qty = int(item.get("quantity", 0))
        new_qty     = current_qty - qty_used
        update_inventory_item(item["id"], {"quantity": new_qty})
        log_inventory_change(
            item.get("name", display_name), item.get("branch", branch),
            -qty_used, current_qty, new_qty, "Order deduction", order_id, logged_by
        )
        reorder = int(item.get("reorder_point", 10))
        if new_qty < 0:
            warnings.append(
                f"🔴🔴 **{display_name}** is now **NEGATIVE STOCK ({new_qty} {item.get('unit','pcs')})** "
                f"at **{branch}** — used more than on hand. Restock urgently."
            )
        elif new_qty == 0:
            warnings.append(f"🔴 **{display_name}** is now **OUT OF STOCK** at **{branch}**.")
        elif new_qty <= reorder:
            warnings.append(
                f"🟡 **{display_name}** is now at **{new_qty} {item.get('unit','pcs')}** "
                f"at **{branch}** — below reorder point ({reorder})."
            )

    for fi in flower_items:
        flower_name = fi.get("flower","").strip()
        qty_used    = int(fi.get("qty", 1))
        colors      = [c for c in fi.get("colors",[]) if c and c.lower() != "any"]
        if not flower_name: continue

        if not colors:
            item = _find(flower_name)
            if item:
                _deduct(item, qty_used, flower_name)
            else:
                new_qty = -qty_used
                new_item = {"id": str(uuid.uuid4())[:8], "name": flower_name,
                    "category": "🌹 Flowers", "branch": branch, "quantity": new_qty,
                    "unit": "pcs", "unit_cost": 0.0, "reorder_point": 10,
                    "notes": "Auto-added from order. Please update unit cost and reorder point.",
                    "created_at": datetime.now().isoformat()}
                _insert("inventory", new_item)
                _invalidate_inventory()
                inventory.append(new_item)
                log_inventory_change(flower_name, branch, new_qty, 0, new_qty, "Auto-created from order", order_id, logged_by)
                warnings.append(
                    f"🔴🔴 **{flower_name}** was not in inventory for **{branch}**. "
                    f"Auto-added with **{new_qty} stock**. Please update in 📦 Inventory."
                )
            continue

        for color in colors:
            color_item_name = f"{color.upper()} {flower_name.upper()}"
            item = _find(color_item_name)
            if item:
                _deduct(item, qty_used, color_item_name)
                continue
            base_item = _find(flower_name)
            if base_item:
                warnings.append(f"ℹ️ **{color_item_name}** not found — deducting from base **{flower_name}** instead.")
                _deduct(base_item, qty_used, flower_name)
                continue
            new_qty = -qty_used
            new_item = {"id": str(uuid.uuid4())[:8], "name": color_item_name,
                "category": "🌹 Flowers", "branch": branch, "quantity": new_qty,
                "unit": "pcs", "unit_cost": 0.0, "reorder_point": 10,
                "notes": "Auto-added from order. Please update unit cost and reorder point.",
                "created_at": datetime.now().isoformat()}
            _insert("inventory", new_item)
            _invalidate_inventory()
            inventory.append(new_item)
            log_inventory_change(color_item_name, branch, new_qty, 0, new_qty, "Auto-created from order", order_id, logged_by)
            warnings.append(
                f"🔴🔴 **{color_item_name}** was not in inventory for **{branch}**. "
                f"Auto-added with **{new_qty} stock**. Please update in 📦 Inventory."
            )
    return warnings


# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY RETURN (cancel / edit order)
# ─────────────────────────────────────────────────────────────────────────────

def return_inventory_for_order(flower_items: list, branch: str, reason: str, order_id: str = "", logged_by: str = "") -> list:
    """Return flower quantities to inventory (cancel or edit order)."""
    if not flower_items:
        return []
    inventory = get_inventory()
    info = []

    def _find(name):
        return _find_inventory_item(inventory, name, branch)

    for fi in flower_items:
        flower_name = fi.get("flower","").strip()
        qty_return  = int(fi.get("qty", 1))
        colors      = [c for c in fi.get("colors",[]) if c and c.lower() != "any"]
        if not flower_name: continue

        targets = [(f"{c.upper()} {flower_name.upper()}", flower_name) for c in colors] if colors else [(flower_name, flower_name)]

        for (item_name, base_name) in targets:
            match = _find(item_name) or _find(base_name)
            if match:
                qty_before = int(match.get("quantity", 0))
                qty_after  = qty_before + qty_return
                update_inventory_item(match["id"], {"quantity": qty_after})
                log_inventory_change(match["name"], branch, +qty_return, qty_before, qty_after, reason, order_id, logged_by)
                info.append(f"↩️ Returned **{qty_return} pcs** of **{match['name']}** to **{branch}** (now {qty_after} pcs)")
            else:
                info.append(f"ℹ️ **{item_name}** not found in inventory — nothing returned.")
    return info


# ─────────────────────────────────────────────────────────────────────────────
# WASTE → INVENTORY DEDUCTION
# ─────────────────────────────────────────────────────────────────────────────

def deduct_inventory_for_waste(item_name: str, qty: int, branch: str, logged_by: str = "") -> list:
    """Deduct from inventory when a waste entry is logged."""
    inventory = get_inventory()
    warnings  = []
    match = _find_inventory_item(inventory, item_name, branch)

    if match is None:
        new_qty = -qty
        _insert("inventory", {"id": str(uuid.uuid4())[:8], "name": item_name,
            "category": "🌹 Flowers", "branch": branch, "quantity": new_qty,
            "unit": "pcs", "unit_cost": 0.0, "reorder_point": 10,
            "notes": "Auto-created by waste log. Please update unit cost.",
            "created_at": datetime.now().isoformat()})
        _invalidate_inventory()
        log_inventory_change(item_name, branch, -qty, 0, new_qty, "Waste deduction (auto-created)", "", logged_by)
        warnings.append(f"⚠️ **{item_name}** was not in inventory. Auto-added with **{new_qty} pcs** at **{branch}**.")
    else:
        qty_before = int(match.get("quantity", 0))
        qty_after  = qty_before - qty
        update_inventory_item(match["id"], {"quantity": qty_after})
        log_inventory_change(match["name"], branch, -qty, qty_before, qty_after, "Waste deduction", "", logged_by)
        if qty_after < 0:
            warnings.append(f"🔴🔴 **{item_name}** is now at **{qty_after} pcs** at **{branch}** after waste deduction.")
        elif qty_after == 0:
            warnings.append(f"🔴 **{item_name}** is now **OUT OF STOCK** at **{branch}** after waste deduction.")
    return warnings


# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_inventory_logs() -> list:
    return _select("inventory_logs")


def log_inventory_change(item_name, branch, change_qty, qty_before, qty_after, reason, order_id="", logged_by=""):
    try:
        _insert("inventory_logs", {
            "id": str(uuid.uuid4())[:8], "item_name": item_name, "branch": branch,
            "change_qty": change_qty, "qty_before": qty_before, "qty_after": qty_after,
            "reason": reason, "order_id": order_id, "logged_by": logged_by,
            "created_at": datetime.now().isoformat(),
        })
        _invalidate_inventory_logs()
    except Exception:
        pass  # Never block an order save due to log failure


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM FLAGS (backfill protection etc.)
# ─────────────────────────────────────────────────────────────────────────────

def get_system_flag(key: str):
    try:
        sb  = get_supabase()
        res = sb.table("system_flags").select("*").eq("key", key).execute()
        if res.data: return res.data[0].get("value")
    except Exception:
        pass
    return None


def set_system_flag(key: str, value: str):
    try:
        get_supabase().table("system_flags").upsert(
            {"key": key, "value": value, "set_at": datetime.now().isoformat()}
        ).execute()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# STOCK COUNT ENTRIES
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_stock_count_entries() -> list:
    return _select("stock_count_entries")


def save_stock_count_entry(entry: dict) -> dict:
    result = _insert("stock_count_entries", entry)
    _invalidate_stock_count()
    return result


# ─────────────────────────────────────────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_expenses() -> list:
    return _select("expenses")


def save_expense(entry: dict) -> dict:
    result = _insert("expenses", entry)
    _invalidate_expenses()
    return result


def delete_expense(expense_id: str) -> bool:
    _delete("expenses", expense_id)
    _invalidate_expenses()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# BRANCH FIXED COSTS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_branch_fixed_costs() -> list:
    return _select("branch_fixed_costs")


def upsert_branch_fixed_cost(row: dict) -> dict:
    result = _upsert("branch_fixed_costs", row)
    _invalidate_branch_costs()
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MANUAL STOCK ADJUSTMENT HELPER
# ─────────────────────────────────────────────────────────────────────────────

def adjust_inventory_manual(item_id: str, item_name: str, branch: str,
                             delta: int, reason: str, logged_by: str) -> str:
    """
    Adjusts an inventory item's quantity by `delta` (positive = add, negative = remove).
    Logs the change to inventory_logs. Returns a status message.
    """
    inventory = get_inventory()
    match = next((i for i in inventory if i.get("id") == item_id), None)
    if not match:
        return f"❌ Item {item_name} not found."
    qty_before = int(match.get("quantity", 0))
    qty_after  = qty_before + delta
    update_inventory_item(item_id, {"quantity": qty_after})
    log_inventory_change(item_name, branch, delta, qty_before, qty_after, reason, "", logged_by)
    direction = "Added" if delta > 0 else "Removed"
    return f"✅ {direction} {abs(delta)} pcs of **{item_name}** at {branch}. Stock: {qty_before} → {qty_after}"


# ─────────────────────────────────────────────────────────────────────────────
# SLOT CONFIGS (Valentine's Day peak-season capacity management)
# ─────────────────────────────────────────────────────────────────────────────

def _invalidate_slot_configs():
    get_slot_configs.clear()


@st.cache_data(ttl=CACHE_TTL)
def get_slot_configs() -> list:
    return _select("slot_configs")


def save_slot_config(config: dict) -> dict:
    result = _upsert("slot_configs", config)
    _invalidate_slot_configs()
    return result


def delete_slot_config(config_id: str) -> bool:
    _delete("slot_configs", config_id)
    _invalidate_slot_configs()
    return True


def get_slot_usage(target_date: str, slot_label: str,
                   branch: str = "All") -> int:
    orders = get_orders()
    return len([
        o for o in orders
        if str(o.get("target_date",""))[:10] == target_date
        and o.get("target_time","") == slot_label
        and o.get("status") not in ("Cancelled",)
        and (branch == "All" or
             o.get("fulfillment_branch", o.get("branch","")) == branch)
    ])


# ─────────────────────────────────────────────────────────────────────────────
# INTER-BRANCH TRANSFERS
# ─────────────────────────────────────────────────────────────────────────────

def _invalidate_transfers():
    get_transfers.clear()


@st.cache_data(ttl=CACHE_TTL)
def get_transfers() -> list:
    return _select("branch_transfers")


def save_transfer(transfer: dict) -> dict:
    result = _insert("branch_transfers", transfer)
    _invalidate_transfers()
    _invalidate_inventory()
    return result


def confirm_transfer(transfer_id: str, confirmed_by: str) -> bool:
    _update("branch_transfers", transfer_id, {
        "status": "Received",
        "confirmed_by": confirmed_by,
        "confirmed_at": datetime.now().isoformat(),
    })
    _invalidate_transfers()
    return True
