"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ 🌸 Angie's Florist — Complete Unified Flower Shop System                     ║
║ Supabase Edition v3.0 · Streamlit Community Cloud Ready                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
DEPENDENCIES: pip install -r requirements.txt
USAGE:        streamlit run angies_florist_v3.py
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import uuid
import os
from datetime import datetime, timedelta, date
import warnings
warnings.filterwarnings("ignore")

import db  # Supabase data layer

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌸 Angie's Florist Complete",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }
.main { background-color: #FDF6F0; }
.stApp { background: linear-gradient(135deg, #FDF6F0 0%, #FFF0F5 100%); }
[data-testid="metric-container"] {
  background: white; border: 1px solid #F0D9E0; border-radius: 16px;
  padding: 16px; box-shadow: 0 2px 12px rgba(219,112,147,0.08);
}
[data-testid="stSidebar"] { background: linear-gradient(180deg, #2D1B2E 0%, #1A0F1E 100%); }
[data-testid="stSidebar"] * { color: #F5D5E0 !important; }
.stButton > button {
  background: linear-gradient(135deg, #C85C8E, #A0355F); color: white !important;
  border: none; border-radius: 10px; font-weight: 500; transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(200,92,142,0.3);
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(200,92,142,0.4); }
.section-header {
  font-family: 'Playfair Display', serif; font-size: 22px; color: #2D1B2E;
  border-bottom: 2px solid #F0D9E0; padding-bottom: 8px; margin-bottom: 20px;
}
.print-sheet {
  background: white; border: 2px solid #C85C8E; border-radius: 12px;
  padding: 24px; font-family: 'DM Sans', sans-serif;
}
.print-sheet h2, .print-sheet h3 { font-family: 'Playfair Display', serif; color: #2D1B2E; }
.print-sheet table { width: 100%; border-collapse: collapse; }
.print-sheet td, .print-sheet th { border: 1px solid #F0D9E0; padding: 8px 12px; text-align: left; }
.print-sheet th { background: #FDF6F0; font-weight: 600; }
.balance-box {
  background: #FFF0F5; border: 1.5px solid #C85C8E; border-radius: 10px;
  padding: 12px 18px; margin-top: 6px; font-family: 'DM Sans', sans-serif;
}
.balance-box .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.balance-box .amount { font-size: 24px; font-weight: 700; color: #C85C8E; }
.city-rank-bar {
  background: #FFF0F5; border-radius: 8px; padding: 10px 14px;
  margin-bottom: 6px; border-left: 4px solid #C85C8E;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
BRANCHES = ["Main Branch", "San Pablo Branch", "Sta. Rosa Branch"]
BRANCH_CODES = {"Main Branch": "MB", "San Pablo Branch": "SB", "Sta. Rosa Branch": "SR"}
STATUS_FLOW = ["Pending","Confirmed","In Progress","Ready","Delivered","Picked Up","Cancelled","Failed Delivery"]
SOURCE_PAGES = ["Facebook","Instagram","WhatsApp","TikTok","Website","Walk-in","Other"]
PAYMENT_METHODS_BALANCE = ["COD","GCash","Bank Transfer","Cash","Maya"]
PAYMENT_METHODS_DIGITAL = ["GCash","Bank Transfer","Cash","Maya"]
OCCASIONS = ["Birthday","Anniversary","Valentine's Day","Mother's Day","Graduation","Sympathy","Wedding","Just Because","Corporate","Other"]
CANCELLATION_REASONS = ["Customer request","Out of stock","Wrong order","Payment failed","Other"]
DELIVERY_FAILURE_REASONS = ["Needs Redelivery","Customer Refused","Address Invalid","Contact Unavailable","Other"]
COLOR_PREFERENCES = ["Any","Red","Two-tone Red","Pink","Two-tone Pink","White","Purple","Two-tone Purple","Yellow","Orange","Two-tone Orange","Blue","Green","Brown","Mixed","Custom"]
DELIVERY_ZONES = ["Calamba","Los Baños","Calauan","Cabuyao","Sta. Rosa","Biñan","San Pedro","Bay","San Pablo","Alaminos","Quezon","Batangas","Victoria","Pila","Sta. Cruz","Pagsanjan","Lumban","Rizal","Nagcarlan","Liliw","PICK UP","N/A"]
WASTE_REASONS = ["Wilted","Damaged","Miscalculation","Customer Return","Expired","Other"]
ARRANGEMENTS = [
    "CHINA ROSES","ECUADORIAN ROSES","PAPER ROSES/LISIATHUS","STARGAZERS",
    "YELLOWIN","CASA BLANCA","CARNATIONS","GERBERA","SUNLIGHT","PEONY","LIPIDIUM",
    "CALLA LILY","GYPSO","STATICE","ORCHIDS","AMARATHUS","SNAPDRAGON",
    "SUNFLOWER","HYDRANGEAS","CHAMOMILE","TULIPS","MUMS","PINGPONG",
    "Apricot Bloom","Pink Dreams","Purple Serenade","Blush Amour",
    "Sunset Blooms","Barbie Fantasy","Blush Petals","Ruby Whisper",
    "Pink Harmony","Little Whimsy","Sunburst Yellow","Thumbelina Bouquet",
    "Kyoto Pink","Opaline Dream",
    "MIXED IMPORTED FLOWERS #1","MIXED IMPORTED FLOWERS #2","MIXED IMPORTED FLOWERS #3",
    "MIXED IMPORTED FLOWERS #4","MIXED IMPORTED FLOWERS #5","MIXED IMPORTED FLOWERS #6",
    "MIXED IMPORTED FLOWERS #7","MIXED IMPORTED FLOWERS #8","MIXED IMPORTED FLOWERS #9",
    "MIXED IMPORTED FLOWERS #10","MIXED IMPORTED FLOWERS #11","MIXED IMPORTED FLOWERS #12",
    "Sympathy Arrangement","Bag Arrangement #1","Bag Arrangement #2","Bag Arrangement #3",
    "CUSTOMIZE - Per Stem",
]
INVENTORY_CATEGORIES = {
    "🌹 Flowers": ["CHINA ROSES","ECUADORIAN ROSES","STARGAZERS","SUNFLOWER","TULIPS"],
    "📦 Wrappers": ["Kraft Paper","Cellophane","Tissue Paper","Vellum Paper"],
    "🎨 Supplies": ["Spray Paint - Green","Spray Paint - Gold","Floral Tape","Wire"],
    "🎁 Add-ons": ["Ribbon","Balloon","Message Card","Tote Bag"],
}
BRANCH_CONFIG = {
    "Main Branch":      {"order_cutoff_time":"14:00","free_delivery_min_order":2500.0,"florist_max_concurrent":5},
    "San Pablo Branch": {"order_cutoff_time":"14:00","free_delivery_min_order":2500.0,"florist_max_concurrent":4},
    "Sta. Rosa Branch": {"order_cutoff_time":"13:00","free_delivery_min_order":3000.0,"florist_max_concurrent":3},
}
STATUS_COLOR = {
    "Pending":"#FFC107","Confirmed":"#17A2B8","In Progress":"#007BFF",
    "Ready":"#28A745","Delivered":"#6C757D","Picked Up":"#6C757D",
    "Cancelled":"#DC3545","Failed Delivery":"#FF6B35",
}

# ─────────────────────────────────────────────────────────────────────────────
# ROLE-BASED PAGE ACCESS
# ─────────────────────────────────────────────────────────────────────────────
PAGE_ACCESS = {
    "Super Admin":    {"Dashboard","New Order","All Orders","Edit Order","Florist Board","Rider Board","Schedule","Inventory","Waste Tracker","Staff Management","Reports","Customers","HR"},
    "Branch Manager": {"Dashboard","New Order","All Orders","Edit Order","Florist Board","Rider Board","Schedule","Inventory","Waste Tracker","Staff Management","Reports","Customers"},
    "Staff":          {"Dashboard","New Order","All Orders","Edit Order","Florist Board","Rider Board","Schedule","Inventory","Waste Tracker","Reports","Customers"},
    "Florist":        {"Dashboard","New Order","All Orders","Edit Order","Florist Board","Schedule"},
    "Rider":          {"Dashboard","Rider Board","Schedule"},
}

# Session state defaults
# Session state defaults
_SESSION_DEFAULTS = {
    "active_page": "Dashboard",
    "edit_order_id": None,
    "auth_user": None,
    "bf_preview_ready": False,
    "_param_rerun_attempted": False,
}
for k, v in _SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# SESSION RESTORE — runs on every page load before anything else
# If auth_user is missing from session_state but a valid token exists
# in the URL, restore the session silently (handles server restarts).
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.auth_user is None:
    _token_in_url = st.query_params.get("session", None)
    
    if not _token_in_url:
        # Query params not available yet on this run — rerun once to let
        # Streamlit finish initializing the WebSocket connection
        if not st.session_state.get("_param_rerun_attempted"):
            st.session_state["_param_rerun_attempted"] = True
            st.rerun()
        else:
            # Already retried — params genuinely not there, clear the flag
            st.session_state["_param_rerun_attempted"] = False
    else:
        # Token found — reset retry flag and attempt restore
        st.session_state["_param_rerun_attempted"] = False
        _restored = db.validate_session_token(_token_in_url)
        if _restored:
            st.session_state.auth_user      = _restored
            st.session_state.active_page    = "Dashboard"
            st.session_state._session_token = _token_in_url


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("""
    <div style='text-align:center; padding: 60px 0 20px;'>
      <div style='font-size:60px;'>🌸</div>
      <div style='font-family: Playfair Display, serif; font-size:28px; font-weight:700; color:#2D1B2E;'>Angie's Florist</div>
      <div style='font-size:12px; color:#C9A0B0; letter-spacing:2px; margin-top:4px;'>STAFF LOGIN</div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.form("login_form"):
            pin       = st.text_input("Enter your PIN", type="password",
                                      max_chars=6, placeholder="••••••")
            submitted = st.form_submit_button("🔓 Log In", use_container_width=True)

            if submitted:
                st.write("🔵 Button clicked")
                st.write(f"🔵 PIN length: {len(pin)}")
                account = db.verify_login(pin.strip())
                st.write(f"🔵 Account found: {account is not None}")
                if account:
                    st.write("🔵 Creating token...")
                    token = db.create_session_token(account["id"])
                    st.write(f"🔵 Token created: {token is not None}")
                    st.session_state.auth_user      = account
                    st.session_state.active_page    = "Dashboard"
                    st.session_state._session_token = token
                    st.query_params["session"]      = token
                    st.write("🔵 About to rerun...")
                    st.rerun()
                else:
                    st.error("❌ Invalid PIN. Please try again.")

        st.caption("Forgot your PIN? Ask a Branch Manager or Super Admin to reset it.")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.auth_user is None:
    page_login()
    st.stop()

CURRENT_USER   = st.session_state.auth_user
CURRENT_ROLE   = CURRENT_USER.get("role", "Staff")
CURRENT_BRANCH = CURRENT_USER.get("branch", "All")


def scope_by_branch(items: list, field: str = "branch") -> list:
    """Restrict a list of records to the logged-in user's branch,
    unless they are Super Admin or have branch == 'All'."""
    if CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All":
        return items
    return [i for i in items if i.get(field) == CURRENT_BRANCH]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def gen_order_code(branch: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    bc = BRANCH_CODES.get(branch, "XX")
    orders = db.get_orders()
    today_branch = [o for o in orders if o.get("branch") == branch and str(o.get("order_code","")).startswith(date_str)]
    seq = str(len(today_branch) + 1).zfill(4)
    return f"{date_str}-{bc}-{seq}"


def lookup_returning_customer(contact: str):
    if not contact or len(contact) < 7:
        return None, 0
    orders = db.get_orders()
    prior = [o for o in orders if o.get("customer_contact","").strip() == contact.strip()]
    if prior:
        latest = sorted(prior, key=lambda x: x.get("created_at",""), reverse=True)[0]
        return latest.get("customer_name",""), len(prior)
    return None, 0


def check_order_cutoff(branch: str, target_date) -> str | None:
    if target_date != date.today():
        return None
    cutoff_str = BRANCH_CONFIG.get(branch,{}).get("order_cutoff_time","14:00")
    cutoff_time = datetime.strptime(cutoff_str, "%H:%M").time()
    if datetime.now().time() > cutoff_time:
        return f"Same-day orders for **{branch}** must be placed before **{cutoff_str}**. Consider setting the target date to tomorrow."
    return None


def get_delivery_fee(branch: str, flower_price: float, base_fee: float) -> float:
    threshold = BRANCH_CONFIG.get(branch,{}).get("free_delivery_min_order", 9999)
    return 0.0 if flower_price >= threshold else base_fee


def flower_items_to_summary(flower_items: list) -> str:
    if not flower_items:
        return "—"
    parts = []
    for fi in flower_items:
        colors = ", ".join(fi.get("colors",[])) or "Any"
        parts.append(f"{fi.get('flower','')} ×{fi.get('qty',1)} [{colors}]")
    return " | ".join(parts)


def flower_items_to_arrangement_str(flower_items: list) -> str:
    return ", ".join(fi.get("flower","") for fi in flower_items) if flower_items else ""


def render_flower_builder(form_key_prefix: str, existing_items=None) -> list:
    sk = f"{form_key_prefix}_flower_items"
    if sk not in st.session_state:
        st.session_state[sk] = existing_items if existing_items else []
    items = st.session_state[sk]

    st.markdown("##### 🌸 Flower Selection")
    st.caption("Add one row per flower type. Each flower can have its own colors and quantity.")

    rows_to_delete = []
    for i, fi in enumerate(items):
        rc1, rc2, rc3, rc4 = st.columns([3, 1, 2, 0.5])
        arr_idx = ARRANGEMENTS.index(fi["flower"]) if fi["flower"] in ARRANGEMENTS else 0
        new_flower = rc1.selectbox(
            f"Flower" if i == 0 else f"Flower #{i+1}", ARRANGEMENTS, index=arr_idx,
            key=f"{sk}_flower_{i}", label_visibility="visible" if i == 0 else "collapsed",
        )
        new_qty = rc2.number_input(
            "Qty" if i == 0 else f"Qty{i}", min_value=1, value=int(fi.get("qty",1)),
            key=f"{sk}_qty_{i}", label_visibility="visible" if i == 0 else "collapsed",
        )
        new_colors = rc3.multiselect(
            "Colors" if i == 0 else f"Colors{i}", COLOR_PREFERENCES,
            default=[c for c in fi.get("colors",["Any"]) if c in COLOR_PREFERENCES],
            key=f"{sk}_colors_{i}", label_visibility="visible" if i == 0 else "collapsed",
        )
        with rc4:
            if st.button("🗑", key=f"{sk}_del_{i}", help="Remove"):
                rows_to_delete.append(i)
        items[i] = {"flower": new_flower, "qty": new_qty, "colors": new_colors if new_colors else ["Any"]}

    for idx in sorted(rows_to_delete, reverse=True):
        items.pop(idx)
    if rows_to_delete:
        st.session_state[sk] = items
        st.rerun()

    if st.button("➕ Add Another Flower", key=f"{sk}_add"):
        items.append({"flower": ARRANGEMENTS[0], "qty": 1, "colors": ["Any"]})
        st.session_state[sk] = items
        st.rerun()

    if not items:
        st.warning("⚠️ Please add at least one flower.")
    else:
        preview_lines = [
            f"🌸 <strong>{fi['flower']}</strong> × {fi['qty']} — <em>{', '.join(fi.get('colors',['Any']))}</em>"
            for fi in items
        ]
        st.markdown(
            "<div style='background:#FFF0F5; border:1.5px solid #F0D9E0; border-radius:10px; padding:10px 14px; margin-top:4px;'>"
            "<strong style='font-size:12px; color:#888;'>BOUQUET PREVIEW</strong><br>"
            + "<br>".join(preview_lines) + "</div>",
            unsafe_allow_html=True,
        )

    st.session_state[sk] = items
    return items


# ─────────────────────────────────────────────────────────────────────────────
# CSV HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def orders_to_csv(orders: list) -> bytes:
    rows = [{
        "Order Code": o.get("order_code",""),
        "Customer Name": o.get("customer_name",""),
        "Contact": o.get("customer_contact",""),
        "Recipient Name": o.get("recipient_name",""),
        "Recipient Contact": o.get("recipient_contact",""),
        "Is Surprise": "Yes" if o.get("is_surprise") else "No",
        "Arrangement": o.get("arrangement",""),
        "Flower Details": flower_items_to_summary(o.get("flower_items",[])),
        "Quantity": o.get("quantity",1),
        "Occasion": o.get("occasion",""),
        "Color Preference": o.get("color_preference",""),
        "Allow Substitution": "Yes" if o.get("allow_substitution") else "No",
        "Source Page": o.get("source_page",""),
        "Chat Branch": o.get("chat_branch",""),
        "Fulfillment Branch": o.get("fulfillment_branch", o.get("branch","")),
        "Order Type": o.get("order_type",""),
        "Delivery Address": o.get("delivery_address",""),
        "Delivery Zone": o.get("delivery_zone",""),
        "Target Date": o.get("target_date",""),
        "Target Time": o.get("target_time",""),
        "Flower Price": o.get("price",0),
        "Delivery Fee": o.get("delivery_fee",0),
        "Total Price": o.get("total_price",0),
        "Down Payment": o.get("down_payment_amount",0),
        "Split Payment": o.get("split_payment_amount",0),
        "Split Method": o.get("split_payment_method",""),
        "Total Balance": o.get("total_balance",0),
        "Balance Method": o.get("balance_payment_method",""),
        "Payment Status": o.get("payment_status",""),
        "Priority Rush": "Yes" if o.get("priority_rush") else "No",
        "Status": o.get("status",""),
        "Assigned Florist": o.get("assigned_florist",""),
        "Assigned Rider": o.get("assigned_rider",""),
        "Cancellation Reason": o.get("cancellation_reason",""),
        "Delivery Attempts": o.get("delivery_attempts",0),
        "Notes": o.get("notes",""),
        "Created At": str(o.get("created_at",""))[:19],
        "Updated At": str(o.get("updated_at",""))[:19],
    } for o in orders]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def waste_to_csv(waste: list) -> bytes:
    rows = [{"Item Name":w.get("item_name",""),"Quantity":w.get("quantity",0),"Unit":w.get("unit",""),"Cost (₱)":w.get("cost",0),"Reason":w.get("reason",""),"Date":w.get("date",""),"Notes":w.get("notes","")} for w in waste]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def inventory_to_csv(inventory: list) -> bytes:
    rows = [{"Item Name":i.get("name",""),"Category":i.get("category",""),"Branch":i.get("branch",""),"Quantity":i.get("quantity",0),"Unit":i.get("unit",""),"Unit Cost (₱)":i.get("unit_cost",0),"Total Value":i.get("quantity",0)*i.get("unit_cost",0),"Reorder Point":i.get("reorder_point",10),"Added":str(i.get("created_at",""))[:10]} for i in inventory]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px;'>
      <div style='font-size:40px;'>🌸</div>
      <div style='font-family: Playfair Display, serif; font-size:22px; font-weight:700; color:#F5D5E0;'>Angie's Florist</div>
      <div style='font-size:11px; color:#C9A0B0; letter-spacing:2px;'>SYSTEM v3.0 · Supabase</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    orders_sb = db.get_orders()
    pending_sb = len([o for o in orders_sb if o["status"] == "Pending"])
    making_sb  = len([o for o in orders_sb if o["status"] == "In Progress"])
    ready_sb   = len([o for o in orders_sb if o["status"] == "Ready"])
    col1, col2, col3 = st.columns(3)
    if pending_sb > 0: col1.metric("🔴", pending_sb)
    if making_sb  > 0: col2.metric("🟡", making_sb)
    if ready_sb   > 0: col3.metric("🟢", ready_sb)
    st.divider()

    pages_all = {
        "📊 Dashboard":      "Dashboard",
        "➕ New Order":      "New Order",
        "📋 All Orders":     "All Orders",
        "🌹 Florist Board":  "Florist Board",
        "🚴 Rider Board":    "Rider Board",
        "📅 Schedule":       "Schedule",
        "👤 Customers":      "Customers",
        "📦 Inventory":      "Inventory",
        "♻️ Waste Tracker":  "Waste Tracker",
        "👥 Staff Management":"Staff Management",
        "📈 Reports":        "Reports",
        "👔 HR Module":      "HR",
    }
    allowed = PAGE_ACCESS.get(CURRENT_ROLE, set())
    pages = {label: key for label, key in pages_all.items() if key in allowed}

    if st.session_state.active_page not in allowed:
        st.session_state.active_page = "Dashboard"

    for label, page_key in pages.items():
        active = st.session_state.active_page == page_key
        if st.button(label, use_container_width=True, key=f"nav_{page_key}", type="primary" if active else "secondary"):
            st.session_state.active_page = page_key
            st.session_state.edit_order_id = None
            st.rerun()

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True, help="Force-reload latest data from the database"):
        db._invalidate_all()
        st.rerun()

    st.divider()
    st.markdown(
        f"<div style='text-align:center; font-size:12px;'>"
        f"👤 <strong>{CURRENT_USER.get('name','')}</strong><br>"
        f"<span style='color:#C9A0B0;'>{CURRENT_ROLE} · {CURRENT_BRANCH}</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Log Out", use_container_width=True):
        # Invalidate the server-side token so the URL token stops working
        _token = st.session_state.get("_session_token")
        if _token:
            db.delete_session_token(_token)
        st.session_state.auth_user      = None
        st.session_state.active_page    = "Dashboard"
        st.session_state._session_token = None
        st.query_params.clear()
        st.rerun()

    st.markdown(f"<div style='font-size:11px; color:#C9A0B0; text-align:center; margin-top:8px;'>{datetime.now().strftime('%A, %B %d %Y')}</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("<div class='section-header'>📊 Dashboard</div>", unsafe_allow_html=True)
    orders    = scope_by_branch(db.get_orders())
    inventory = scope_by_branch(db.get_inventory())
    waste     = scope_by_branch(db.get_waste())
    today     = date.today().isoformat()

    today_orders    = [o for o in orders if str(o.get("target_date",""))[:10] == today]
    delivered_today = [o for o in orders if str(o.get("delivered_at",""))[:10] == today]
    ready_count     = len([o for o in orders if o["status"] == "Ready"])
    rush_orders     = len([o for o in orders if o.get("priority_rush") and o["status"] not in ["Delivered","Picked Up","Cancelled"]])
    pending_florist = len([o for o in orders if o["status"] == "Pending" and not o.get("assigned_florist")])
    revenue_today   = sum(float(o.get("total_price",0)) for o in delivered_today if o["status"] != "Cancelled")
    revenue_all     = sum(float(o.get("total_price",0)) for o in orders if o["status"] in ["Delivered","Picked Up"])
    waste_cost      = sum(float(w.get("cost",0)) for w in waste)
    profit          = revenue_all - waste_cost
    profit_margin   = (profit / revenue_all * 100) if revenue_all > 0 else 0
    cod_balance     = sum(float(o.get("total_balance",0)) for o in orders if o.get("balance_payment_method")=="COD" and o.get("total_balance",0)>0 and o["status"] in ["Ready","Delivered"])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📦 Today's Orders",  len(today_orders))
    c2.metric("✅ Delivered Today", len(delivered_today), f"₱{revenue_today:,.0f}")
    c3.metric("🎉 Ready",           ready_count)
    c4.metric("🚀 Rush Orders",     rush_orders)
    c5.metric("⏳ Need Florist",    pending_florist)
    c6.metric("⚠️ COD Balance",    f"₱{cod_balance:,.0f}")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 📊 Orders by Status")
        if orders:
            status_counts = pd.Series([o["status"] for o in orders]).value_counts()
            fig, ax = plt.subplots(figsize=(8,5), facecolor="#FDF6F0")
            ax.bar(status_counts.index, status_counts.values, color="#C85C8E", alpha=0.8)
            ax.set_facecolor("#FDF6F0"); ax.grid(True, axis="y", alpha=0.3)
            plt.xticks(rotation=45, ha="right"); plt.tight_layout()
            st.pyplot(fig); plt.close(fig)

    with col2:
        st.markdown("#### 🌹 Inventory Status")
        low  = len([i for i in inventory if i.get("quantity",0) <= i.get("reorder_point",10)])
        med  = len([i for i in inventory if i.get("reorder_point",10) < i.get("quantity",0) <= i.get("reorder_point",10)*2])
        high = len([i for i in inventory if i.get("quantity",0) > i.get("reorder_point",10)*2])
        if low+med+high > 0:
            fig, ax = plt.subplots(figsize=(8,5), facecolor="#FDF6F0")
            ax.pie([low,med,high], labels=["Low Stock","Medium","Optimal"], colors=["#DC3545","#FFC107","#28A745"], autopct="%1.0f%%")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)

    with col3:
        st.markdown("#### 💳 Revenue vs Waste")
        if revenue_all > 0:
            fig, ax = plt.subplots(figsize=(8,5), facecolor="#FDF6F0")
            ax.bar(["Revenue","Waste"], [revenue_all, waste_cost], color=["#28A745","#DC3545"], alpha=0.8)
            ax.set_facecolor("#FDF6F0"); ax.grid(True, axis="y", alpha=0.3)
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.divider()
    st.markdown("#### 📈 Summary")
    c1,c2,c3 = st.columns(3)
    c1.metric("💰 Total Revenue",    f"₱{revenue_all:,.0f}")
    c2.metric("📉 Total Waste Cost", f"₱{waste_cost:,.0f}")
    c3.metric("📈 Net Profit Margin",f"{profit_margin:.1f}%")

    # Stock alerts for managers
    if CURRENT_ROLE in ("Branch Manager","Super Admin"):
        neg_items  = [i for i in inventory if int(i.get("quantity",0)) < 0]
        zero_items = [i for i in inventory if int(i.get("quantity",0)) == 0]
        low_items  = [i for i in inventory if 0 < int(i.get("quantity",0)) <= int(i.get("reorder_point",10))]
        if neg_items or zero_items or low_items:
            st.divider()
            st.markdown("#### ⚠️ Inventory Alerts")
            if neg_items:
                with st.expander(f"🔴🔴 {len(neg_items)} item(s) in NEGATIVE STOCK — urgent restock needed", expanded=True):
                    for i in sorted(neg_items, key=lambda x: int(x.get("quantity",0))):
                        st.error(f"**{i['name']}** ({i.get('branch','')}) — **{i.get('quantity',0)} pcs**")
            if zero_items:
                with st.expander(f"🔴 {len(zero_items)} item(s) OUT OF STOCK"):
                    for i in zero_items:
                        st.warning(f"**{i['name']}** ({i.get('branch','')}) — OUT OF STOCK")
            if low_items:
                with st.expander(f"🟡 {len(low_items)} item(s) LOW STOCK"):
                    for i in sorted(low_items, key=lambda x: int(x.get("quantity",0))):
                        st.warning(f"**{i['name']}** ({i.get('branch','')}) — {i.get('quantity',0)} pcs (reorder at {i.get('reorder_point',10)})")
    st.divider()
    st.markdown("#### 📋 Shareable Recap")
    st.caption("Quick copy-paste summary for group chats / end-of-day reports.")
    recap_period = st.radio("Period", ["Today","This Week"], horizontal=True, key="recap_period")

    if recap_period == "Today":
        period_orders = [o for o in orders if str(o.get("target_date",""))[:10] == today]
        period_label = f"Today ({date.today().strftime('%b %d, %Y')})"
    else:
        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        period_orders = [o for o in orders if str(o.get("target_date",""))[:10] >= week_start]
        period_label = f"This Week (since {week_start})"

    period_completed = [o for o in period_orders if o["status"] in ("Delivered","Picked Up")]
    period_revenue   = sum(float(o.get("total_price",0)) for o in period_completed)
    period_pending   = len([o for o in period_orders if o["status"] not in ("Delivered","Picked Up","Cancelled","Failed Delivery")])
    period_cancelled = len([o for o in period_orders if o["status"] == "Cancelled"])
    period_rush      = len([o for o in period_orders if o.get("priority_rush")])

    # Top arrangement for the period
    arr_qty = {}
    for o in period_orders:
        arr_qty[o.get("arrangement","Unknown")] = arr_qty.get(o.get("arrangement","Unknown"),0) + int(o.get("quantity",1))
    top_arr = max(arr_qty.items(), key=lambda x: x[1])[0] if arr_qty else "—"

    low_stock_items = [i for i in inventory if i.get("quantity",0) <= i.get("reorder_point",10)]

    branch_label = CURRENT_BRANCH if CURRENT_BRANCH != "All" else "All Branches"
    recap_text = (
        f"🌸 Angie's Florist — {period_label}\n"
        f"Branch: {branch_label}\n"
        f"---------------------------\n"
        f"📦 Total Orders: {len(period_orders)}\n"
        f"✅ Completed: {len(period_completed)}\n"
        f"⏳ Pending/In Progress: {period_pending}\n"
        f"❌ Cancelled: {period_cancelled}\n"
        f"🚀 Rush Orders: {period_rush}\n"
        f"🏆 Top Arrangement: {top_arr}\n"
        f"💰 Revenue: ₱{period_revenue:,.2f}\n"
    )
    if low_stock_items:
        recap_text += f"⚠️ Low Stock Alerts: {len(low_stock_items)} item(s) — " + ", ".join(i['name'] for i in low_stock_items[:5])
        if len(low_stock_items) > 5:
            recap_text += f" +{len(low_stock_items)-5} more"
        recap_text += "\n"

    st.text_area("Recap (copy this)", value=recap_text, height=200, key="recap_text_area")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: NEW ORDER
# ─────────────────────────────────────────────────────────────────────────────
def page_new_order():
    st.markdown("<div class='section-header'>➕ Log New Order</div>", unsafe_allow_html=True)

    st.markdown("##### 🔍 Returning Customer Lookup")
    lk1, lk2 = st.columns([2,3])
    lookup_contact = lk1.text_input("Enter contact number to check:", key="vip_lookup_contact", placeholder="09XX-XXX-XXXX")
    vip_name, vip_count = lookup_returning_customer(lookup_contact)
    if vip_name:
        lk2.success(f"🌸 Returning customer — **{vip_count} order(s)** | Suggested name: **{vip_name}**")
    elif lookup_contact and len(lookup_contact) >= 7:
        lk2.info("New customer — no previous orders found.")
    st.divider()

    st.markdown("##### 💰 Price Inputs (live balance preview)")
    lp1,lp2,lp3 = st.columns(3)
    st.session_state.form_price        = lp1.number_input("Flower Price preview",   min_value=0.0, step=50.0,  value=st.session_state.get("form_price",0.0),        key="new_price_preview",   label_visibility="collapsed")
    st.session_state.form_delivery_fee = lp2.number_input("Delivery Fee preview",   min_value=0.0, step=25.0,  value=st.session_state.get("form_delivery_fee",0.0),  key="new_fee_preview",     label_visibility="collapsed")
    st.session_state.form_down_payment = lp3.number_input("Down Payment preview",   min_value=0.0, step=50.0,  value=st.session_state.get("form_down_payment",0.0),  key="new_dp_preview",      label_visibility="collapsed")
    live_total   = st.session_state.form_price + st.session_state.form_delivery_fee
    live_balance = max(live_total - st.session_state.form_down_payment, 0)
    pb1,pb2,pb3 = st.columns(3)
    pb1.markdown(f"""<div class="balance-box"><div class="label">Total Price</div><div class="amount">₱{live_total:,.2f}</div></div>""", unsafe_allow_html=True)
    pb2.markdown(f"""<div class="balance-box"><div class="label">Down Payment</div><div class="amount">₱{st.session_state.form_down_payment:,.2f}</div></div>""", unsafe_allow_html=True)
    pb3.markdown(f"""<div class="balance-box"><div class="label">Balance Due</div><div class="amount" style="color:{'#28A745' if live_balance==0 else '#C85C8E'};">{'✅ FULLY PAID' if live_balance==0 else f'₱{live_balance:,.2f}'}</div></div>""", unsafe_allow_html=True)
    st.info("ℹ️ Adjust the three fields above to see a live balance preview, then fill the full form below.")
    st.divider()

    flower_items = render_flower_builder("new")
    st.divider()

    with st.form("new_order_form", clear_on_submit=True):
        st.markdown("##### 👤 Customer Information")
        c1,c2 = st.columns(2)
        customer_name    = c1.text_input("Customer Name *",    value=vip_name if vip_name else "", placeholder="Juan dela Cruz")
        customer_contact = c2.text_input("Contact Number *",   value=lookup_contact if lookup_contact else "", placeholder="09XX-XXX-XXXX")

        st.markdown("##### 🎁 Recipient Details")
        rc1,rc2,rc3 = st.columns(3)
        recipient_name    = rc1.text_input("Recipient Name",    placeholder="Leave blank if same as buyer")
        recipient_contact = rc2.text_input("Recipient Contact", placeholder="Optional")
        is_surprise       = rc3.checkbox("🤫 Surprise Delivery?")

        st.markdown("##### 📦 Arrangement & Occasion")
        c1,c2 = st.columns(2)
        source_page = c1.selectbox("Source Page *", SOURCE_PAGES)
        occasion    = c2.selectbox("Occasion", OCCASIONS, index=OCCASIONS.index("Other"))
        cp1,cp2 = st.columns(2)
        allow_substitution = cp1.checkbox("Allow Substitutions?")
        substitution_notes = cp2.text_input("Substitution Notes", placeholder="e.g., No red — use orange instead") if allow_substitution else ""

        inspo_pictures = st.file_uploader(
            "📸 Upload Inspiration Pictures (Optional)",
            type=["jpg","jpeg","png","gif"],
            accept_multiple_files=True,
            key="inspo_uploader",
        )

        with st.expander("💌 Message Card (Optional)"):
            mc1,mc2 = st.columns(2)
            msg_to   = mc1.text_input("To:",   placeholder="e.g., Maria")
            msg_from = mc2.text_input("From:", placeholder="e.g., Juan")
            msg_body = st.text_area("Message:", placeholder="Happy Birthday!...")

        st.markdown("##### 💐 Pricing & Payments")
        c1,c2 = st.columns(2)
        price   = c1.number_input("Flower Price (₱) *", min_value=0.0, step=50.0, value=st.session_state.get("form_price",0.0))
        raw_fee = c2.number_input("Delivery Fee (₱)",   min_value=0.0, step=25.0, value=st.session_state.get("form_delivery_fee",0.0))
        down_payment = st.number_input("Down Payment (₱)", min_value=0.0, step=50.0, value=st.session_state.get("form_down_payment",0.0))

        proof_of_payment = st.file_uploader(
            "📄 Proof of Payment", type=["pdf","jpg","jpeg","png"], key="payment_proof"
        )

        st.markdown("**Split / Secondary Payment**")
        sp1,sp2 = st.columns(2)
        split_amount = sp1.number_input("Additional Payment Amount (₱)", min_value=0.0, step=50.0)
        split_method = sp2.selectbox("Via", PAYMENT_METHODS_DIGITAL)

        calc_total   = price + raw_fee
        calc_balance = max(calc_total - down_payment - split_amount, 0)
        balance_payment_method = "N/A"
        if calc_balance > 0:
            balance_payment_method = st.selectbox("Balance Payment Method *", PAYMENT_METHODS_BALANCE)

        st.markdown("##### 📅 Schedule & Location")
        c1,c2,c3 = st.columns(3)
        target_date = c1.date_input("Target Date *", min_value=date.today())
        target_time = c2.time_input("Target Time *", value=datetime.strptime("10:00","%H:%M").time())
        no_branch_options = BRANCHES if (CURRENT_ROLE in ("Super Admin","Branch Manager") or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
        default_branch_idx = no_branch_options.index(CURRENT_BRANCH) if CURRENT_BRANCH in no_branch_options else 0
        chat_branch = c3.selectbox("Chat Branch *", no_branch_options, index=default_branch_idx)
        fulfillment_branch = st.selectbox("Fulfillment Branch *", no_branch_options, index=no_branch_options.index(chat_branch) if chat_branch in no_branch_options else 0)

        st.markdown("##### 🚚 Delivery or Pick-up?")
        order_type       = st.radio("Order Type *", ["Delivery","Pick-up"], horizontal=True)
        delivery_address = ""
        delivery_zone    = ""
        if order_type == "Delivery":
            delivery_address = st.text_input("Delivery Address *", placeholder="Full address")
            delivery_zone    = st.selectbox("Delivery Zone", DELIVERY_ZONES)

        priority_rush = st.checkbox("🚀 Priority/Rush Order")
        notes = st.text_area("Special Instructions / Notes", placeholder="e.g., Add red ribbon")
        submitted = st.form_submit_button("🌸 Log Order", use_container_width=True)

    if submitted:
        flower_items = st.session_state.get("new_flower_items",[])
        errors = []
        if not customer_name or not customer_contact: errors.append("Customer name and contact are required.")
        if price == 0: errors.append("Flower price is required.")
        if order_type == "Delivery" and not delivery_address: errors.append("Delivery address is required.")
        if not flower_items: errors.append("Please add at least one flower in the Flower Selection above.")
        if errors:
            for e in errors: st.error(f"❌ {e}")
            return

        cutoff_warning = check_order_cutoff(fulfillment_branch, target_date)
        if cutoff_warning:
            st.warning(f"⏰ {cutoff_warning}")

        delivery_fee = get_delivery_fee(fulfillment_branch, price, raw_fee)
        if delivery_fee == 0 and raw_fee > 0:
            st.info(f"🎉 Free delivery applied! Order meets the ₱{BRANCH_CONFIG[fulfillment_branch]['free_delivery_min_order']:,.0f} threshold.")

        order_code      = gen_order_code(fulfillment_branch)
        total_price     = price + delivery_fee
        effective_down  = down_payment + split_amount
        total_balance   = max(total_price - effective_down, 0)
        arrangement_str = flower_items_to_arrangement_str(flower_items)
        total_qty       = sum(fi.get("qty",1) for fi in flower_items)
        all_colors      = list(set(c for fi in flower_items for c in fi.get("colors",[])))
        color_pref_str  = ", ".join(sorted(all_colors)) if all_colors else "Any"

        # Upload inspiration pictures to Supabase Storage
        inspo_urls = []
        for pic in (inspo_pictures or []):
            ext = pic.name.split(".")[-1].lower()
            path = f"orders/{order_code}/inspo/{uuid.uuid4().hex[:8]}.{ext}"
            url = db.upload_file(pic.getvalue(), path, content_type=pic.type or "image/jpeg")
            if url:
                inspo_urls.append(url)

        # Upload proof of payment to Supabase Storage
        proof_url = None
        if proof_of_payment:
            ext = proof_of_payment.name.split(".")[-1].lower()
            path = f"orders/{order_code}/payment_proof/{uuid.uuid4().hex[:8]}.{ext}"
            proof_url = db.upload_file(proof_of_payment.getvalue(), path, content_type=proof_of_payment.type or "application/octet-stream")

        order = {
            "order_code": order_code, "id": order_code,
            "customer_name": customer_name, "customer_contact": customer_contact,
            "recipient_name": recipient_name, "recipient_contact": recipient_contact,
            "is_surprise": is_surprise,
            "message_card_to": msg_to, "message_card_body": msg_body, "message_card_from": msg_from,
            "arrangement": arrangement_str, "quantity": total_qty,
            "source_page": source_page, "occasion": occasion,
            "color_preference": color_pref_str, "flower_items": flower_items,
            "allow_substitution": allow_substitution, "substitution_notes": substitution_notes,
            "inspo_pictures": inspo_urls,
            "price": price, "delivery_fee": delivery_fee, "total_price": total_price,
            "down_payment_amount": down_payment,
            "split_payment_amount": split_amount,
            "split_payment_method": split_method if split_amount > 0 else "",
            "total_balance": total_balance, "balance_payment_method": balance_payment_method,
            "proof_of_payment": proof_url,
            "notes": notes,
            "target_date": target_date.isoformat(),
            "target_time": target_time.strftime("%I:%M %p"),
            "chat_branch": chat_branch, "fulfillment_branch": fulfillment_branch, "branch": fulfillment_branch,
            "order_type": order_type, "delivery_address": delivery_address, "delivery_zone": delivery_zone,
            "priority_rush": priority_rush,
            "assigned_florist": "", "assigned_rider": "",
            "payment_status": "Fully Paid" if total_balance == 0 else "Partially Paid",
            "payment_method": balance_payment_method,
            "status": "Pending",
            "finished_product_picture": None,
            "proof_of_delivery": None,
            "delivery_attempts": 0, "cancellation_reason": "", "cancellation_notes": "",
            "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(),
            "encoded_by": CURRENT_USER.get("name", ""),
            "encoded_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        }
        db.save_order(order)

        if split_amount > 0:
            db.save_payment_transaction({
                "id": str(uuid.uuid4())[:8], "order_id": order_code,
                "amount": split_amount, "method": split_method,
                "note": "Split payment logged at order creation",
                "created_at": datetime.now().isoformat(),
            })

        # Auto inventory deduction
        inv_warnings = db.deduct_inventory_for_order(
            flower_items, fulfillment_branch,
            order_id=order_code, logged_by=CURRENT_USER.get("name","")
        )
        for k in ("form_price","form_delivery_fee","form_down_payment"):
            st.session_state[k] = 0.0
        st.session_state.pop("new_flower_items", None)
        st.success(f"✅ Order **{order_code}** logged successfully!")
        st.info(f"📌 **Order Code:** `{order_code}`")
        if inspo_urls:
            st.info(f"📸 {len(inspo_urls)} inspiration picture(s) uploaded.")
        if proof_url:
            st.info("📄 Proof of payment uploaded.")
        if delivery_fee == 0 and raw_fee > 0:
            st.success("🚚 Free delivery applied!")
        if inv_warnings:
            st.markdown("**📦 Inventory Update:**")
            for w in inv_warnings: st.warning(w)
        else:
            st.success("📦 Inventory updated automatically.")
        st.balloons()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: EDIT ORDER
# ─────────────────────────────────────────────────────────────────────────────
def page_edit_order():
    order_id = st.session_state.edit_order_id
    orders   = db.get_orders()
    order    = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        st.error("Order not found.")
        st.session_state.edit_order_id = None
        st.session_state.active_page = "All Orders"
        st.rerun(); return

    order_code = order.get("order_code", order.get("id","N/A"))
    st.markdown(f"<div class='section-header'>✏️ Edit Order — {order_code}</div>", unsafe_allow_html=True)
    if st.button("← Back to All Orders"):
        st.session_state.edit_order_id = None
        st.session_state.active_page = "All Orders"
        st.rerun()

    st.info(f"**Current Status:** {order['status']} | **Florist:** {order.get('assigned_florist','Unassigned')} | **Rider:** {order.get('assigned_rider','Unassigned')}")
    st.warning("⚠️ Editing does not change the order status, florist, or rider assignment.")
    st.divider()

    if "form_price" not in st.session_state:
        st.session_state.form_price        = float(order.get("price",0))
        st.session_state.form_delivery_fee = float(order.get("delivery_fee",0))
        st.session_state.form_down_payment = float(order.get("down_payment_amount",0))

    lp1,lp2,lp3 = st.columns(3)
    st.session_state.form_price        = lp1.number_input("Flower Price preview",  min_value=0.0, step=50.0, value=st.session_state.form_price,        key="edit_price_prev",  label_visibility="collapsed")
    st.session_state.form_delivery_fee = lp2.number_input("Delivery Fee preview",  min_value=0.0, step=25.0, value=st.session_state.form_delivery_fee,  key="edit_fee_prev",    label_visibility="collapsed")
    st.session_state.form_down_payment = lp3.number_input("Down Payment preview",  min_value=0.0, step=50.0, value=st.session_state.form_down_payment,  key="edit_dp_prev",     label_visibility="collapsed")
    live_total   = st.session_state.form_price + st.session_state.form_delivery_fee
    live_balance = max(live_total - st.session_state.form_down_payment, 0)
    pb1,pb2,pb3 = st.columns(3)
    pb1.markdown(f"""<div class="balance-box"><div class="label">Total Price</div><div class="amount">₱{live_total:,.2f}</div></div>""", unsafe_allow_html=True)
    pb2.markdown(f"""<div class="balance-box"><div class="label">Down Payment</div><div class="amount">₱{st.session_state.form_down_payment:,.2f}</div></div>""", unsafe_allow_html=True)
    pb3.markdown(f"""<div class="balance-box"><div class="label">Balance Due</div><div class="amount" style="color:{'#28A745' if live_balance==0 else '#C85C8E'};">{'✅ FULLY PAID' if live_balance==0 else f'₱{live_balance:,.2f}'}</div></div>""", unsafe_allow_html=True)
    st.divider()

    existing_flower_items = order.get("flower_items") or []
    edit_flower_items = render_flower_builder("edit", existing_items=existing_flower_items)
    st.divider()

    with st.form("edit_order_form"):
        st.markdown("##### 👤 Customer Information")
        c1,c2 = st.columns(2)
        customer_name    = c1.text_input("Customer Name *",  value=order.get("customer_name",""))
        customer_contact = c2.text_input("Contact Number *", value=order.get("customer_contact",""))

        st.markdown("##### 🎁 Recipient Details")
        rc1,rc2,rc3 = st.columns(3)
        recipient_name    = rc1.text_input("Recipient Name",    value=order.get("recipient_name",""))
        recipient_contact = rc2.text_input("Recipient Contact", value=order.get("recipient_contact",""))
        is_surprise       = rc3.checkbox("🤫 Surprise Delivery?", value=bool(order.get("is_surprise",False)))

        st.markdown("##### 📦 Arrangement & Occasion")
        c1,c2 = st.columns(2)
        src_idx = SOURCE_PAGES.index(order["source_page"]) if order.get("source_page") in SOURCE_PAGES else 0
        source_page = c1.selectbox("Source Page *", SOURCE_PAGES, index=src_idx)
        occ_idx = OCCASIONS.index(order["occasion"]) if order.get("occasion") in OCCASIONS else len(OCCASIONS)-1
        occasion = c2.selectbox("Occasion", OCCASIONS, index=occ_idx)
        cp1,cp2 = st.columns(2)
        allow_substitution = cp1.checkbox("Allow Substitutions?", value=bool(order.get("allow_substitution",False)))
        substitution_notes = cp2.text_input("Substitution Notes", value=order.get("substitution_notes",""))

        inspo_replace = st.file_uploader(
            "📸 Replace Inspiration Pictures (leave empty to keep existing)",
            type=["jpg","jpeg","png","gif"], accept_multiple_files=True, key="edit_inspo",
        )

        with st.expander("💌 Message Card"):
            mc1,mc2 = st.columns(2)
            msg_to   = mc1.text_input("To:",   value=order.get("message_card_to",""))
            msg_from = mc2.text_input("From:", value=order.get("message_card_from",""))
            msg_body = st.text_area("Message:", value=order.get("message_card_body",""))

        st.markdown("##### 💐 Pricing & Payments")
        c1,c2 = st.columns(2)
        price        = c1.number_input("Flower Price (₱) *", min_value=0.0, step=50.0, value=float(order.get("price",0)))
        delivery_fee = c2.number_input("Delivery Fee (₱)",   min_value=0.0, step=25.0, value=float(order.get("delivery_fee",0)))
        down_payment = st.number_input("Down Payment (₱)",   min_value=0.0, step=50.0, value=float(order.get("down_payment_amount",0)))
        proof_replace = st.file_uploader(
            "📄 Replace Proof of Payment (leave empty to keep existing)",
            type=["pdf","jpg","jpeg","png"], key="edit_proof",
        )
        bm_default = order.get("balance_payment_method", PAYMENT_METHODS_BALANCE[0])
        bm_idx = PAYMENT_METHODS_BALANCE.index(bm_default) if bm_default in PAYMENT_METHODS_BALANCE else 0
        balance_payment_method = st.selectbox("Balance Payment Method", PAYMENT_METHODS_BALANCE, index=bm_idx)

        st.markdown("##### 📅 Schedule & Location")
        c1,c2,c3 = st.columns(3)
        default_date = date.fromisoformat(str(order["target_date"])[:10]) if order.get("target_date") else date.today()
        target_date = c1.date_input("Target Date *", value=default_date)
        try:
            default_time = datetime.strptime(order.get("target_time","10:00 AM"),"%I:%M %p").time()
        except ValueError:
            default_time = datetime.strptime("10:00","%H:%M").time()
        target_time = c2.time_input("Target Time *", value=default_time)
        cb_idx = BRANCHES.index(order.get("chat_branch",BRANCHES[0])) if order.get("chat_branch") in BRANCHES else 0
        chat_branch = c3.selectbox("Chat Branch *", BRANCHES, index=cb_idx)
        fb_idx = BRANCHES.index(order.get("fulfillment_branch",BRANCHES[0])) if order.get("fulfillment_branch") in BRANCHES else 0
        fulfillment_branch = st.selectbox("Fulfillment Branch *", BRANCHES, index=fb_idx)

        ot_idx = 0 if order.get("order_type","Delivery") == "Delivery" else 1
        order_type = st.radio("Order Type *", ["Delivery","Pick-up"], horizontal=True, index=ot_idx)
        delivery_address = ""
        delivery_zone    = order.get("delivery_zone","")
        if order_type == "Delivery":
            delivery_address = st.text_input("Delivery Address *", value=order.get("delivery_address",""))
            dz_idx = DELIVERY_ZONES.index(delivery_zone) if delivery_zone in DELIVERY_ZONES else 0
            delivery_zone = st.selectbox("Delivery Zone", DELIVERY_ZONES, index=dz_idx)

        priority_rush = st.checkbox("🚀 Priority/Rush Order", value=bool(order.get("priority_rush",False)))
        notes = st.text_area("Special Instructions / Notes", value=order.get("notes",""))
        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

    if save_btn:
        errors = []
        if not customer_name or not customer_contact: errors.append("Customer name and contact are required.")
        if price == 0: errors.append("Flower price is required.")
        if order_type == "Delivery" and not delivery_address: errors.append("Delivery address is required.")
        if errors:
            for e in errors: st.error(f"❌ {e}")
            return

        total_price   = price + delivery_fee
        total_balance = max(total_price - down_payment, 0)
        efi = edit_flower_items

        inspo_files = order.get("inspo_pictures", [])
        if inspo_replace:
            inspo_files = []
            for pic in inspo_replace:
                ext = pic.name.split(".")[-1].lower()
                path = f"orders/{order_code}/inspo/{uuid.uuid4().hex[:8]}.{ext}"
                url = db.upload_file(pic.getvalue(), path, content_type=pic.type or "image/jpeg")
                if url:
                    inspo_files.append(url)

        proof_path = order.get("proof_of_payment")
        if proof_replace:
            ext = proof_replace.name.split(".")[-1].lower()
            path = f"orders/{order_code}/payment_proof/{uuid.uuid4().hex[:8]}.{ext}"
            proof_path = db.upload_file(proof_replace.getvalue(), path, content_type=proof_replace.type or "application/octet-stream")

        db.update_order(order_id, {
            "customer_name": customer_name, "customer_contact": customer_contact,
            "recipient_name": recipient_name, "recipient_contact": recipient_contact,
            "is_surprise": is_surprise,
            "message_card_to": msg_to, "message_card_body": msg_body, "message_card_from": msg_from,
            "arrangement": flower_items_to_arrangement_str(efi) or order.get("arrangement",""),
            "quantity": sum(fi.get("qty",1) for fi in efi) if efi else order.get("quantity",1),
            "flower_items": efi,
            "source_page": source_page, "occasion": occasion,
            "color_preference": ", ".join(sorted(set(c for fi in efi for c in fi.get("colors",["Any"])))) if efi else order.get("color_preference","Any"),
            "allow_substitution": allow_substitution, "substitution_notes": substitution_notes,
            "inspo_pictures": inspo_files,
            "price": price, "delivery_fee": delivery_fee, "total_price": total_price,
            "down_payment_amount": down_payment, "total_balance": total_balance,
            "balance_payment_method": balance_payment_method,
            "proof_of_payment": proof_path,
            "notes": notes,
            "target_date": target_date.isoformat(), "target_time": target_time.strftime("%I:%M %p"),
            "chat_branch": chat_branch, "fulfillment_branch": fulfillment_branch, "branch": fulfillment_branch,
            "order_type": order_type, "delivery_address": delivery_address, "delivery_zone": delivery_zone,
            "priority_rush": priority_rush,
            "payment_status": "Fully Paid" if total_balance == 0 else "Partially Paid",
            "updated_at": datetime.now().isoformat(),
        })
        # Inventory adjustment on edit
        old_fi = order.get("flower_items", [])
        old_br = order.get("fulfillment_branch", order.get("branch",""))
        if old_fi and efi and old_fi != efi:
            ret = db.return_inventory_for_order(old_fi, old_br,
                reason="Order edit — returning old flowers",
                order_id=order_code, logged_by=CURRENT_USER.get("name",""))
            ded = db.deduct_inventory_for_order(efi, fulfillment_branch,
                order_id=order_code, logged_by=CURRENT_USER.get("name",""))
            if ret or ded:
                st.markdown("**📦 Inventory adjusted:**")
                for r in ret: st.info(r)
                for d in ded: st.warning(d)
        st.success(f"✅ Order **{order_code}** updated successfully!")
        st.session_state.edit_order_id = None
        st.session_state.active_page   = "All Orders"
        for k in ("form_price","form_delivery_fee","form_down_payment"):
            st.session_state.pop(k, None)
        st.session_state.pop("edit_flower_items", None)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ALL ORDERS
# ─────────────────────────────────────────────────────────────────────────────
def page_all_orders():
    st.markdown("<div class='section-header'>📋 All Orders</div>", unsafe_allow_html=True)
    orders   = scope_by_branch(db.get_orders())
    florists = scope_by_branch(db.get_florists())

    if not orders:
        st.info("No orders yet. Head to **➕ New Order** to get started.")
        return

    branch_options = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
    c1,c2,c3,c4,c5 = st.columns(5)
    f_branch = c1.selectbox("Branch", ["All"] + branch_options, key="ao_branch")
    f_status = c2.selectbox("Status", ["All"] + STATUS_FLOW, key="ao_status")
    f_type   = c3.selectbox("Type",   ["All","Delivery","Pick-up"], key="ao_type")
    f_date   = c4.date_input("Date",  value=None, key="ao_date")
    search   = c5.text_input("🔍 Search", key="ao_search")

    show_all = st.checkbox("Show all orders (including older than 60 days) — may be slower", key="ao_show_all")

    filtered = orders.copy()
    if not show_all and not f_date and f_status == "All":
        cutoff = (date.today() - timedelta(days=60)).isoformat()
        filtered = [o for o in filtered if str(o.get("target_date",""))[:10] >= cutoff]
    if f_branch != "All": filtered = [o for o in filtered if o.get("branch") == f_branch]
    if f_status != "All": filtered = [o for o in filtered if o.get("status") == f_status]
    if f_type   != "All": filtered = [o for o in filtered if o.get("order_type") == f_type]
    if f_date:            filtered = [o for o in filtered if str(o.get("target_date",""))[:10] == f_date.isoformat()]
    if search:
        q = search.lower()
        filtered = [o for o in filtered if q in o.get("customer_name","").lower() or q in o.get("order_code","").lower() or q in o.get("arrangement","").lower()]

    def _ao_time(o):
        t=o.get("target_time","23:59")
        try: return datetime.strptime(t,"%I:%M %p").strftime("%H:%M")
        except: return t
    _date_groups={}
    for o in filtered: _date_groups.setdefault(str(o.get("target_date",""))[:10],[]).append(o)
    filtered=[]
    for _d in sorted(_date_groups.keys(),reverse=True): filtered.extend(sorted(_date_groups[_d],key=_ao_time))
    col_count, col_export = st.columns([3,1])
    col_count.markdown(f"**{len(filtered)} order(s) found** {'(last 60 days — check *Show all* for older)' if not show_all and not f_date and f_status=='All' else ''}")
    if filtered:
        col_export.download_button("⬇️ Export CSV", data=orders_to_csv(filtered),
            file_name=f"angies_orders_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)
    st.divider()

    # Pagination — show 25 at a time to keep the page snappy
    PAGE_SIZE = 25
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    if total_pages > 1:
        page_num = st.number_input(f"Page (1–{total_pages})", min_value=1, max_value=total_pages, value=1, key="ao_page")
    else:
        page_num = 1
    start_idx = (page_num - 1) * PAGE_SIZE
    page_orders = filtered[start_idx:start_idx + PAGE_SIZE]

    for o in page_orders:
        status       = o["status"]
        order_type   = o["order_type"]
        order_code   = o.get("order_code", o.get("id","N/A"))
        assigned_florist = o.get("assigned_florist","")
        priority_badge   = "🚀 **RUSH**" if o.get("priority_rush") else ""
        status_color     = STATUS_COLOR.get(status,"#888")
        balance          = float(o.get("total_balance",0))

        hc1,hc2,hc3,hc4,hc5 = st.columns([3, 1.2, 1.2, 0.7, 0.7])
        with hc1:
            st.markdown(
                f"**`{order_code}`** {priority_badge} \n"
                f"👤 {o['customer_name']} &nbsp; 📞 {o['customer_contact']} \n"
                f"📦 {o.get('arrangement','')} ×{o.get('quantity',1)} &nbsp; "
                f"📅 {str(o.get('target_date',''))[:10]} {o.get('target_time','')} \n"
                f"🏪 {o.get('fulfillment_branch',o.get('branch',''))} "
                f"&nbsp; 💳 ₱{float(o.get('total_price',0)):,.0f} "
                f"&nbsp; <span style='color:{status_color}; font-weight:700;'>{status}</span>",
                unsafe_allow_html=True,
            )

        with hc2:
            if status == "Pending":
                florist_labels = []
                for f in florists:
                    load = db.get_florist_active_load(f["name"])
                    max_load = f.get("max_concurrent_orders",5)
                    florist_labels.append(f"{f['name']} ({load}/{max_load})")
                florist_label_map = {lbl: f["name"] for lbl, f in zip(florist_labels, florists)}
                sel_label = st.selectbox("Florist", ["— assign —"] + florist_labels, key=f"flst_{order_code}", label_visibility="collapsed")
                sel_f = florist_label_map.get(sel_label,"")
                if sel_f and sel_f != assigned_florist:
                    chosen_obj = next((f for f in florists if f["name"] == sel_f), None)
                    at_capacity = False
                    if chosen_obj:
                        load = db.get_florist_active_load(sel_f)
                        at_capacity = load >= chosen_obj.get("max_concurrent_orders",5)
                    if at_capacity:
                        st.error(f"⛔ {sel_f} is at full capacity.")
                    else:
                        if st.button("✓ Assign Florist", key=f"af_{order_code}", use_container_width=True):
                            db.update_order(o["id"], {"assigned_florist": sel_f, "florist_assigned_at": datetime.now().isoformat()})
                            st.rerun()
            else:
                st.caption(f"🌹 {assigned_florist or '—'}")

        with hc3:
            if status == "Pending":
                if not assigned_florist:
                    st.caption("⏳ Assign florist first")
                else:
                    if st.button("✅ Confirm", key=f"conf_{order_code}", use_container_width=True):
                        db.update_order_status(o["id"],"Confirmed"); st.rerun()
            elif status == "Confirmed":
                if st.button("🌹 Start", key=f"start_{order_code}", use_container_width=True):
                    db.update_order_status(o["id"],"In Progress"); st.rerun()
            elif status == "In Progress":
                if st.button("🎉 Mark Ready", key=f"ready_{order_code}", use_container_width=True):
                    db.update_order_status(o["id"],"Ready"); st.rerun()
            elif status == "Ready" and order_type == "Pick-up":
                if st.button("🛍 Picked Up", key=f"pu_{order_code}", use_container_width=True):
                    db.update_order_status(o["id"],"Picked Up"); st.rerun()
            elif status == "Ready" and order_type == "Delivery":
                st.caption("→ Rider Board")

        with hc4:
            if status not in ("Delivered","Picked Up","Cancelled"):
                if st.button("✏️", key=f"edit_{order_code}", use_container_width=True):
                    st.session_state.edit_order_id    = o["id"]
                    st.session_state.form_price        = float(o.get("price",0))
                    st.session_state.form_delivery_fee = float(o.get("delivery_fee",0))
                    st.session_state.form_down_payment = float(o.get("down_payment_amount",0))
                    st.session_state.active_page       = "Edit Order"
                    st.rerun()

        with hc5:
            if st.button("🗑", key=f"del_{order_code}", use_container_width=True):
                db.delete_order(o["id"]); st.rerun()

        # Cancellation modal
        if status not in ("Cancelled","Delivered","Picked Up","Failed Delivery"):
            if st.button("🚫 Cancel Order", key=f"cancel_btn_{order_code}"):
                st.session_state[f"cancelling_{order_code}"] = True
            if st.session_state.get(f"cancelling_{order_code}"):
                with st.container():
                    st.warning(f"⚠️ Cancelling order **{order_code}** — please provide a reason.")
                    ccol1,ccol2 = st.columns(2)
                    cancel_reason = ccol1.selectbox("Reason *", CANCELLATION_REASONS, key=f"crsn_{order_code}")
                    cancel_notes  = ccol2.text_input("Notes (optional)", key=f"cnts_{order_code}")
                    ok_col, abort_col = st.columns(2)
                    if ok_col.button("✅ Confirm Cancellation", key=f"cok_{order_code}"):
                        db.update_order(o["id"],{"status":"Cancelled","cancellation_reason":cancel_reason,"cancellation_notes":cancel_notes})
                        # Auto-return stock
                        if o.get("flower_items"):
                            ret = db.return_inventory_for_order(
                                o["flower_items"],
                                o.get("fulfillment_branch", o.get("branch","")),
                                reason=f"Order cancelled ({cancel_reason})",
                                order_id=order_code, logged_by=CURRENT_USER.get("name","")
                            )
                            for r in ret: st.success(r)
                        st.session_state.pop(f"cancelling_{order_code}", None); st.rerun()
                    if abort_col.button("↩️ Keep Order", key=f"cabort_{order_code}"):
                        st.session_state.pop(f"cancelling_{order_code}", None); st.rerun()

        # Expandable detail
        with st.expander(f"📄 Full Details — {order_code}", expanded=False):
            dc1,dc2 = st.columns(2)
            with dc1:
                st.markdown(f"""
**Order Code:** `{order_code}`  
**Customer:** {o.get('customer_name','')}  
**Contact:** {o.get('customer_contact','')}  
**Recipient:** {o.get('recipient_name','—') or '(same as buyer)'}  
**Recipient Contact:** {o.get('recipient_contact','—')}  
**Surprise?:** {'🤫 YES' if o.get('is_surprise') else 'No'}  
**Source Page:** {o.get('source_page','')}  
**Chat Branch:** {o.get('chat_branch','')}  
**Fulfillment Branch:** {o.get('fulfillment_branch',o.get('branch',''))}  
**Arrangement:** {o.get('arrangement','')}  
**Flower Details:** {flower_items_to_summary(o.get('flower_items',[]))}  
**Quantity:** {o.get('quantity',1)}  
**Occasion:** {o.get('occasion','—')}  
**Substitutions:** {'✅ Yes' if o.get('allow_substitution') else 'No'} {o.get('substitution_notes','')}  
**Target Date:** {str(o.get('target_date',''))[:10]} @ {o.get('target_time','')}  
**Order Type:** {order_type}  
**Delivery Address:** {o.get('delivery_address','—')}  
**Delivery Zone:** {o.get('delivery_zone','—')}  
**Priority Rush:** {'🚀 YES' if o.get('priority_rush') else 'No'}
                """)
            with dc2:
                st.markdown(f"""
**Status:** {status}  
**Florist:** {o.get('assigned_florist','—')}  
**Rider:** {o.get('assigned_rider','—')}  
**Flower Price:** ₱{float(o.get('price',0)):,.2f}  
**Delivery Fee:** ₱{float(o.get('delivery_fee',0)):,.2f}  
**Total Price:** ₱{float(o.get('total_price',0)):,.2f}  
**Down Payment:** ₱{float(o.get('down_payment_amount',0)):,.2f}  
**Split Payment:** ₱{float(o.get('split_payment_amount',0)):,.2f} {o.get('split_payment_method','')}  
**Balance Due:** ₱{balance:,.2f}  
**Balance Method:** {o.get('balance_payment_method','N/A')}  
**Payment Status:** {o.get('payment_status','—')}  
**Delivery Attempts:** {o.get('delivery_attempts',0)}  
**Cancellation Reason:** {o.get('cancellation_reason','—')}  
**Created:** {str(o.get('created_at',''))[:19]}  
**Updated:** {str(o.get('updated_at',''))[:19]}
**Logged by:** {o.get('encoded_by','—') or '—'} · {o.get('encoded_at','—') or '—'}
                """)
                
            if any([o.get("message_card_to"), o.get("message_card_body"), o.get("message_card_from")]):
                st.markdown("**💌 Message Card:**")
                st.info(f"**To:** {o.get('message_card_to','')}\n\n{o.get('message_card_body','')}\n\n**From:** {o.get('message_card_from','')}")

            inspo = o.get("inspo_pictures", [])
            if inspo:
                st.markdown("**📸 Inspiration Pictures:**")
                cols = st.columns(min(3, len(inspo)))
                for i, url in enumerate(inspo):
                    cols[i % len(cols)].image(url, caption=f"Ref {i+1}", use_container_width=True)

            pod = o.get("proof_of_delivery")
            if pod:
                st.markdown("**📷 Proof of Delivery:**")
                st.image(pod, caption="Delivery Proof", width=300)
        st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FLORIST BOARD
# ─────────────────────────────────────────────────────────────────────────────
@st.fragment(run_every="30s")
def page_florist_board():
    st.markdown("<div class='section-header'>🌹 Florist Production Board</div>", unsafe_allow_html=True)
    st.caption("🔄 Auto-refreshes every 30 seconds")
    orders   = scope_by_branch(db.get_orders())
    florists = scope_by_branch(db.get_florists())
    production = [o for o in orders if o["status"] in ["Pending","Confirmed","In Progress"]]
    if not production:
        st.success("✅ All clear! No active orders."); return
    branch_opts_fb = BRANCHES if (CURRENT_ROLE=="Super Admin" or CURRENT_BRANCH=="All") else [CURRENT_BRANCH]
    fc1,fc2,fc3,fc4,fc5,fc6 = st.columns(6)
    fb_branch = fc1.selectbox("Branch",["All"]+branch_opts_fb,key="fb_branch")
    fb_status = fc2.selectbox("Status",["All","Pending","Confirmed","In Progress"],key="fb_status")
    fb_type   = fc3.selectbox("Type",["All","Delivery","Pick-up"],key="fb_type")
    fb_date   = fc4.date_input("Date",value=None,key="fb_date")
    fb_search = fc5.text_input("🔍 Search",key="fb_search")
    fb_sort   = fc6.selectbox("Sort by",["🚀 Rush First → Date → Time","📅 Date (earliest first)","🕐 Time (earliest first)","📋 Status (Pending first)"],key="fb_sort")
    ft1,ft2 = st.columns(2)
    fb_time_from = ft1.time_input("Time from",value=None,key="fb_time_from")
    fb_time_to   = ft2.time_input("Time to",value=None,key="fb_time_to")
    if fb_branch!="All": production=[o for o in production if o.get("branch")==fb_branch or o.get("fulfillment_branch")==fb_branch]
    if fb_status!="All": production=[o for o in production if o.get("status")==fb_status]
    if fb_type!="All":   production=[o for o in production if o.get("order_type")==fb_type]
    if fb_date:          production=[o for o in production if str(o.get("target_date",""))[:10]==fb_date.isoformat()]
    if fb_search:
        q=fb_search.lower(); production=[o for o in production if q in o.get("customer_name","").lower() or q in o.get("order_code","").lower() or q in o.get("arrangement","").lower() or q in o.get("assigned_florist","").lower()]
    def _fb_t(o):
        try: return datetime.strptime(o.get("target_time","12:00 AM"),"%I:%M %p").time()
        except: return None
    if fb_time_from: production=[o for o in production if (t:=_fb_t(o)) and t>=fb_time_from]
    if fb_time_to:   production=[o for o in production if (t:=_fb_t(o)) and t<=fb_time_to]
    def sort_key(o):
        rush=0 if o.get("priority_rush") else 1; d=str(o.get("target_date","9999-99-99"))[:10]
        t=o.get("target_time","23:59")
        try: t=datetime.strptime(t,"%I:%M %p").strftime("%H:%M")
        except: pass
        s={"Pending":0,"Confirmed":1,"In Progress":2}.get(o.get("status",""),3)
        if fb_sort.startswith("🚀"): return (rush,d,t)
        elif fb_sort.startswith("📅"): return (d,t)
        elif fb_sort.startswith("🕐"): return (t,d)
        else: return (s,d,t)
    production=sorted(production,key=sort_key)
    if not production: st.info("No orders match."); return
    st.markdown(f"**{len(production)} order(s) in production**")

    for o in production:
        florist    = o.get("assigned_florist","Unassigned")
        order_code = o.get("order_code", o.get("id","N/A"))
        priority   = "🚀 RUSH ORDER" if o.get("priority_rush") else "Normal"
        fi_list    = o.get("flower_items",[])
        msg_to_val   = o.get("message_card_to","")
        msg_body_val = o.get("message_card_body","")
        msg_from_val = o.get("message_card_from","")
        has_msg_card = any([msg_to_val, msg_body_val, msg_from_val])
        msg_card_row = (f"<tr><th>💌 Message Card</th><td><strong>To:</strong> {msg_to_val}<br>{msg_body_val}<br><strong>From:</strong> {msg_from_val}</td></tr>") if has_msg_card else ""

        if fi_list:
            flower_rows_html = "".join(f"<tr><td><strong>{fi.get('flower','')}</strong></td><td style='text-align:center;'>{fi.get('qty',1)} pc(s)</td><td>{', '.join(fi.get('colors',['Any']))}</td></tr>" for fi in fi_list)
            arrangement_block = f"<tr><th colspan='3' style='background:#FDF6F0; padding:6px 12px;'>🌸 Flower Details</th></tr><tr><th>Flower</th><th>Qty</th><th>Colors</th></tr>{flower_rows_html}"
        else:
            arrangement_block = f"<tr><th>Arrangement</th><td colspan='2'><strong>{o.get('arrangement','')}</strong></td></tr><tr><th>Quantity</th><td colspan='2'>{o.get('quantity',1)} pc(s)</td></tr>"

        with st.expander(f"🌸 {order_code} — {o['customer_name']} | {str(o.get('target_date',''))[:10]} | {florist}"):
            st.markdown(f"""
            <div class="print-sheet">
              <h3>🌹 FLORIST PRODUCTION SHEET</h3>
              <p style="color:#888; font-size:12px;">Order #{order_code} · {datetime.now().strftime('%b %d, %Y %I:%M %p')}</p>
              <table>
                <tr><th>Order Code</th><td colspan='2'><strong>{order_code}</strong></td></tr>
                <tr><th>Customer</th><td colspan='2'>{o['customer_name']} | {o['customer_contact']}</td></tr>
                <tr><th>Target Date & Time</th><td colspan='2'><strong>{str(o.get('target_date',''))[:10]} at {o.get('target_time','')}</strong></td></tr>
                {arrangement_block}
                <tr><th>Occasion</th><td colspan='2'>{o.get('occasion','')}</td></tr>
                <tr><th>Substitutions OK?</th><td colspan='2'>{'✅ Yes' if o.get('allow_substitution') else 'No'} {o.get('substitution_notes','')}</td></tr>
                <tr><th>Order Type</th><td colspan='2'>{'🚴 DELIVERY' if o['order_type']=='Delivery' else '🛍 PICK-UP'}</td></tr>
                <tr><th>Priority</th><td colspan='2'><strong style="color:#C85C8E;">{priority}</strong></td></tr>
                <tr><th>Assigned Florist</th><td colspan='2'><strong style="color:#C85C8E;">{florist}</strong></td></tr>
                <tr><th>Special Instructions</th><td colspan='2'><strong>{o.get('notes','None')}</strong></td></tr>
                <tr><th>Branch</th><td colspan='2'>{o.get('fulfillment_branch', o.get('branch',''))}</td></tr>
                <tr><th>Logged by</th><td colspan='2'>{o.get('encoded_by','—') or '—'} · {o.get('encoded_at','—') or '—'}</td></tr>
                {msg_card_row}
              </table>
              <p style="margin-top:16px; font-size:13px; color:#888;">☐ Flowers prepared &nbsp;|&nbsp; ☐ Arranged &nbsp;|&nbsp; ☐ Quality checked &nbsp;|&nbsp; ☐ Ready</p>
            </div>
            """, unsafe_allow_html=True)

            # Inspiration pictures (on-screen)
            inspo_pics = o.get("inspo_pictures", [])
            if inspo_pics:
                st.markdown("#### 📸 Inspiration Pictures")
                cols = st.columns(min(3, len(inspo_pics)))
                for idx, pic_url in enumerate(inspo_pics):
                    cols[idx % len(cols)].image(pic_url, caption=f"Reference {idx+1}", use_container_width=True)

            # ── Print button ───────────────────────────────────────────────

            # Flower block for print
            if fi_list:
                print_flower_rows = "".join(
                    "<tr><td><strong>" + fi.get("flower","") + "</strong></td>"
                    "<td style='text-align:center;'>" + str(fi.get("qty",1)) + "</td>"
                    "<td>" + ", ".join(fi.get("colors", ["Any"])) + "</td></tr>"
                    for fi in fi_list
                )
                print_flower_block = (
                    "<table class='flower-table'>"
                    "<thead><tr><th>Flower</th><th>Qty</th><th>Colors</th></tr></thead>"
                    "<tbody>" + print_flower_rows + "</tbody>"
                    "</table>"
                )
            else:
                print_flower_block = (
                    "<table class='flower-table'><tbody>"
                    "<tr><td><strong>Arrangement:</strong></td><td>" + o.get("arrangement","") + "</td></tr>"
                    "<tr><td><strong>Quantity:</strong></td><td>" + str(o.get("quantity",1)) + " pc(s)</td></tr>"
                    "</tbody></table>"
                )

            # Message card block for print
            if has_msg_card:
                print_msg_block = (
                    "<div class='section-box'>"
                    "<div class='section-title'>💌 Message Card</div>"
                    "<p><strong>To:</strong> " + msg_to_val + "</p>"
                    "<p style='margin:4px 0;'>" + msg_body_val + "</p>"
                    "<p><strong>From:</strong> " + msg_from_val + "</p>"
                    "</div>"
                )
            else:
                print_msg_block = ""

            # Inspiration pictures block for print
            inspo_pics = o.get("inspo_pictures", [])
            if inspo_pics:
                cols_count = 1 if len(inspo_pics) == 1 else (2 if len(inspo_pics) == 2 else 3)
                pic_tags = "".join(
                    "<img src='" + url + "' alt='Ref " + str(i+1) + "' />"
                    for i, url in enumerate(inspo_pics)
                )
                print_inspo_block = (
                    "<div class='section-box'>"
                    "<div class='section-title'>📸 Inspiration Pictures</div>"
                    "<div class='inspo-grid' style='grid-template-columns: repeat(" + str(cols_count) + ", 1fr);'>"
                    + pic_tags +
                    "</div></div>"
                )
            else:
                print_inspo_block = ""

            # Pre-computed values for print HTML
            sub_text = ("Substitutions allowed. " + o.get("substitution_notes","")).strip() if o.get("allow_substitution") else "No substitutions."
            rush_banner = "<div class='rush-banner'>🚀 RUSH ORDER — PRIORITISE IMMEDIATELY</div>" if o.get("priority_rush") else ""
            order_type_label = "🚴 DELIVERY" if o.get("order_type") == "Delivery" else "🛍 PICK-UP"
            branch_name = o.get("fulfillment_branch", o.get("branch",""))
            print_timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")

            # Full print HTML
            print_html = (
                "<!DOCTYPE html><html lang='en'><head>"
                "<meta charset='UTF-8'/>"
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'/>"
                "<title>Order " + order_code + " — Angie's Florist</title>"
                "<style>"
                "* { box-sizing: border-box; margin: 0; padding: 0; }"
                "body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #111; background: #fff; padding: 10px 14px; line-height: 1.3; }"
                ".shop-name { font-size: 14px; font-weight: 700; color: #C85C8E; display:inline; }"
                ".sheet-title { font-size: 10px; color: #666; display:inline; margin-left:8px; }"
                ".divider { border: none; border-top: 1.5px solid #C85C8E; margin: 6px 0 8px; }"
                ".rush-banner { background: #C85C8E; color: #fff; font-size: 12px; font-weight: 700; text-align: center; padding: 5px; border-radius: 4px; margin-bottom: 6px; }"
                ".date-hero { background: #FDF0F7; border: 2px solid #C85C8E; border-radius: 6px; padding: 6px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }"
                ".date-hero .label { font-size: 9px; color: #888; text-transform: uppercase; letter-spacing: 0.4px; }"
                ".date-hero .value { font-size: 17px; font-weight: 800; color: #C85C8E; }"
                ".date-hero .order-code { font-size: 14px; font-weight: 700; color: #333; }"
                ".two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px; }"
                ".info-box { border: 1px solid #e8d0dc; border-radius: 5px; padding: 5px 8px; background: #FFFAFE; }"
                ".info-box .key { font-size: 9px; font-weight: 700; color: #C85C8E; text-transform: uppercase; letter-spacing: 0.4px; }"
                ".info-box .val { font-size: 11px; color: #111; margin-top: 1px; }"
                ".section-box { border: 1px solid #e8d0dc; border-radius: 5px; padding: 5px 8px; margin-bottom: 6px; background: #FFFAFE; }"
                ".section-title { font-size: 9px; font-weight: 700; color: #C85C8E; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }"
                ".flower-table { width: 100%; border-collapse: collapse; font-size: 10px; }"
                ".flower-table th { background: #FDF0F7; color: #C85C8E; font-weight: 700; padding: 3px 6px; text-align: left; border-bottom: 1.5px solid #C85C8E; }"
                ".flower-table td { padding: 3px 6px; border-bottom: 1px solid #f0e4ec; }"
                ".flower-table tr:last-child td { border-bottom: none; }"
                ".checklist { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 3px; }"
                ".checklist-item { display: flex; align-items: center; gap: 5px; font-size: 11px; }"
                ".checklist-item .box { width: 14px; height: 14px; border: 1.5px solid #C85C8E; border-radius: 2px; display: inline-block; flex-shrink: 0; }"
                ".footer { margin-top: 6px; border-top: 1px solid #e0d0d8; padding-top: 4px; font-size: 9px; color: #aaa; display: flex; justify-content: space-between; }"
                ".inspo-grid { display: grid; gap: 6px; margin-top: 4px; }"
                ".inspo-grid img { width: 100%; max-height: 550px; object-fit: contain; border-radius: 4px; border: 1px solid #e8d0dc; display: block; }"
                "@media print { body { padding: 8px 10px; } @page { margin: 6mm 8mm; size: A4; } }"
                "</style></head><body>"
                "<div class='shop-name'>🌹 Angie's Florist</div>"
                "<span class='sheet-title'>· Florist Production Sheet · Printed " + print_timestamp + "</span>"
                "<hr class='divider' />"
                + rush_banner +
                "<div class='date-hero'>"
                "<div>"
                "<div class='label'>Target Date &amp; Time</div>"
                "<div class='value'>" + str(o.get("target_date",""))[:10] + " &nbsp;at&nbsp; " + o.get("target_time","") + "</div>"
                "</div>"
                "<div style='text-align:right;'>"
                "<div class='label'>Order Code</div>"
                "<div class='order-code'>" + order_code + "</div>"
                "<div style='font-size:10px; color:#888; margin-top:2px;'>" + order_type_label + "</div>"
                "</div></div>"
                "<div class='two-col'>"
                "<div class='info-box'><div class='key'>Customer</div><div class='val'>" + o.get("customer_name","") + " · " + o.get("customer_contact","") + "</div></div>"
                "<div class='info-box'><div class='key'>Assigned Florist</div><div class='val'><strong>" + florist + "</strong></div></div>"
                "<div class='info-box'><div class='key'>Occasion</div><div class='val'>" + o.get("occasion","—") + "</div></div>"
                "<div class='info-box'><div class='key'>Substitutions</div><div class='val'>" + sub_text + "</div></div>"
                "<div class='info-box'><div class='key'>Branch</div><div class='val'>" + branch_name + "</div></div>"
                "<div class='info-box'><div class='key'>Priority</div><div class='val'>" + ("🚀 RUSH" if o.get("priority_rush") else "Normal") + "</div></div>"
                "</div>"
                "<div class='section-box'><div class='section-title'>🌸 Flower Details</div>" + print_flower_block + "</div>"
                "<div class='section-box'><div class='section-title'>📝 Special Instructions</div>"
                "<div style='font-size:11px; white-space:pre-wrap;'>" + o.get("notes","None") + "</div></div>"
                + print_msg_block
                + print_inspo_block +
                "<div class='section-box'><div class='section-title'>✅ Production Checklist</div>"
                "<div class='checklist'>"
                "<div class='checklist-item'><span class='box'></span> Flowers prepared</div>"
                "<div class='checklist-item'><span class='box'></span> Arranged</div>"
                "<div class='checklist-item'><span class='box'></span> Quality checked</div>"
                "<div class='checklist-item'><span class='box'></span> Ready</div>"
                "</div></div>"
                "<div class='footer'>"
                "<span>Angie's Florist Digital Management System</span>"
                "<span>Branch: " + branch_name + " · Printed: " + print_timestamp + "</span>"
                "</div>"
                "<script>window.addEventListener('load', function() { window.print(); });</script>"
                "</body></html>"
            )

            # Print button
            print_key = f"print_triggered_{order_code}"
            if st.button("🖨️ Print Order Sheet", key=f"print_btn_{order_code}", use_container_width=False):
                st.session_state[print_key] = True

            if st.session_state.get(print_key):
                import base64
                import streamlit.components.v1 as components
                b64 = base64.b64encode(print_html.encode("utf-8")).decode("utf-8")
                trigger_js = (
                    "<script>"
                    "(function() {"
                    "var b64 = '" + b64 + "';"
                    "var binary = atob(b64);"
                    "var bytes = new Uint8Array(binary.length);"
                    "for (var i = 0; i < binary.length; i++) { bytes[i] = binary.charCodeAt(i); }"
                    "var blob = new Blob([bytes], { type: 'text/html; charset=utf-8' });"
                    "var url = URL.createObjectURL(blob);"
                    "var win = window.open(url, '_blank');"
                    "if (!win) { alert('Pop-up blocked! Please allow pop-ups for this page and try again.'); }"
                    "})();"
                    "</script>"
                )
                components.html(trigger_js, height=0, scrolling=False)
                st.session_state[print_key] = False

            # ── Full status workflow ───────────────────────────────────────
            st.markdown("---")
            ac1, ac2, ac3 = st.columns(3)

            with ac1:
                if o["status"] == "Pending":
                    florist_assigned = o.get("assigned_florist","")
                    if CURRENT_ROLE in ("Super Admin", "Branch Manager", "Staff"):
                        if not florist_assigned:
                            florist_labels = []
                            for f in florists:
                                load = db.get_florist_active_load(f["name"])
                                max_load = f.get("max_concurrent_orders", 5)
                                florist_labels.append(f"{f['name']} ({load}/{max_load})")
                            florist_label_map = {lbl: f["name"] for lbl, f in zip(florist_labels, florists)}
                            sel_label = st.selectbox("Assign Florist", ["— assign —"] + florist_labels,
                                key=f"fb_flst_{order_code}", label_visibility="collapsed")
                            sel_f = florist_label_map.get(sel_label, "")
                            if sel_f:
                                chosen_obj = next((f for f in florists if f["name"] == sel_f), None)
                                if chosen_obj:
                                    load = db.get_florist_active_load(sel_f)
                                    if load >= chosen_obj.get("max_concurrent_orders", 5):
                                        st.error(f"⛔ {sel_f} is at full capacity.")
                                    elif st.button("✓ Assign Florist", key=f"fb_af_{order_code}", use_container_width=True):
                                        db.update_order(o["id"], {"assigned_florist": sel_f,
                                            "florist_assigned_at": datetime.now().isoformat()})
                                        st.rerun()
                        else:
                            if st.button("✅ Confirm Order", key=f"fb_conf_{order_code}", use_container_width=True):
                                db.update_order_status(o["id"], "Confirmed"); st.rerun()
                    else:
                        # Florist/Rider — read only
                        if florist_assigned:
                            st.caption(f"🌹 Assigned to: **{florist_assigned}**")
                        else:
                            st.caption("⏳ Awaiting florist assignment")
            with ac2:
                if o["status"] == "Confirmed":
                    if st.button("🌹 Start Production", key=f"fstart_{order_code}", use_container_width=True):
                        db.update_order_status(o["id"],"In Progress"); st.rerun()
            with ac3:
                if o["status"] == "In Progress":
                    finished_pic = st.file_uploader(
                        "📸 Upload Finished Product Picture",
                        type=["jpg","jpeg","png"], key=f"finished_{order_code}",
                    )
                    if finished_pic:
                        if st.button("✅ Mark as READY", key=f"fready_{order_code}", use_container_width=True):
                            ext = finished_pic.name.split(".")[-1].lower()
                            path = f"orders/{order_code}/finished_product/{uuid.uuid4().hex[:8]}.{ext}"
                            url = db.upload_file(finished_pic.getvalue(), path, content_type=finished_pic.type or "image/jpeg")
                            db.update_order(o["id"], {"finished_product_picture": url, "status": "Ready"})
                            if o.get("order_type") == "Delivery":
                                st.success(f"✅ Order **{order_code}** marked READY — it will appear on the 🚴 Rider Board!")
                            else:
                                st.success(f"✅ Order **{order_code}** marked READY — awaiting pick-up.")
                            st.rerun()
                    else:
                        st.info("📸 Upload a finished product picture before marking ready.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RIDER BOARD
# ─────────────────────────────────────────────────────────────────────────────
@st.fragment(run_every="30s")
def page_rider_board():
    st.markdown("<div class='section-header'>🚴 Rider Delivery Board</div>", unsafe_allow_html=True)
    st.caption("🔄 Auto-refreshes every 30 seconds")
    orders  = scope_by_branch(db.get_orders())
    riders  = scope_by_branch(db.get_riders())
    rider_names    = [r["name"] for r in riders]
    rider_contacts = {r["name"]: r.get("contact","") for r in riders}
    rider_orders = [o for o in orders if o.get("order_type")=="Delivery" and o["status"] in ["Ready","Failed Delivery"]]
    branch_opts_rb = BRANCHES if (CURRENT_ROLE=="Super Admin" or CURRENT_BRANCH=="All") else [CURRENT_BRANCH]
    rc1,rc2,rc3,rc4,rc5 = st.columns(5)
    rb_branch = rc1.selectbox("Branch",["All"]+branch_opts_rb,key="rb_branch")
    rb_status = rc2.selectbox("Status",["All","Ready","Failed Delivery"],key="rb_status")
    rb_date   = rc3.date_input("Date",value=None,key="rb_date")
    rb_search = rc4.text_input("🔍 Search",key="rb_search")
    rb_sort   = rc5.selectbox("Sort by",["📅 Date (earliest first)","🕐 Time (earliest first)","🚀 Rush First → Date → Time","💰 COD first"],key="rb_sort")
    rt1,rt2 = st.columns(2)
    rb_time_from = rt1.time_input("Time from",value=None,key="rb_time_from")
    rb_time_to   = rt2.time_input("Time to",value=None,key="rb_time_to")
    rb_rider = st.selectbox("Filter by Rider",["All Riders","Unassigned"]+rider_names,key="rb_rider") if riders else "All Riders"
    filtered_orders = rider_orders.copy()
    if rb_branch!="All": filtered_orders=[o for o in filtered_orders if o.get("branch")==rb_branch or o.get("fulfillment_branch")==rb_branch]
    if rb_status!="All": filtered_orders=[o for o in filtered_orders if o.get("status")==rb_status]
    if rb_date:          filtered_orders=[o for o in filtered_orders if str(o.get("target_date",""))[:10]==rb_date.isoformat()]
    if rb_search:
        q=rb_search.lower(); filtered_orders=[o for o in filtered_orders if q in o.get("customer_name","").lower() or q in o.get("order_code","").lower() or q in o.get("arrangement","").lower() or q in (o.get("recipient_name","") or "").lower() or q in o.get("delivery_address","").lower() or q in o.get("assigned_rider","").lower()]
    if rb_rider!="All Riders":
        if rb_rider=="Unassigned": filtered_orders=[o for o in filtered_orders if not o.get("assigned_rider")]
        else: filtered_orders=[o for o in filtered_orders if o.get("assigned_rider")==rb_rider]
    def _rb_t(o):
        try: return datetime.strptime(o.get("target_time","12:00 AM"),"%I:%M %p").time()
        except: return None
    if rb_time_from: filtered_orders=[o for o in filtered_orders if (t:=_rb_t(o)) and t>=rb_time_from]
    if rb_time_to:   filtered_orders=[o for o in filtered_orders if (t:=_rb_t(o)) and t<=rb_time_to]
    def rb_sort_key(o):
        d=str(o.get("target_date","9999-99-99"))[:10]
        t=o.get("target_time","23:59")
        try: t=datetime.strptime(t,"%I:%M %p").strftime("%H:%M")
        except: pass
        rush=0 if o.get("priority_rush") else 1
        cod=0 if (o.get("balance_payment_method")=="COD" and float(o.get("total_balance",0))>0) else 1
        if rb_sort.startswith("📅"):   return (d,t)
        elif rb_sort.startswith("🕐"): return (t,d)
        elif rb_sort.startswith("🚀"): return (rush,d,t)
        else:                           return (cod,d,t)
    filtered_orders=sorted(filtered_orders,key=rb_sort_key)
    cod_total=sum(float(o.get("total_balance",0)) for o in filtered_orders if o.get("balance_payment_method")=="COD" and o.get("total_balance",0)>0)
    st.metric("💰 COD to Collect",f"₱{cod_total:,.2f}")
    if not filtered_orders: st.info("No delivery orders match." if rider_orders else "No delivery orders ready yet."); return
    st.success(f"🚴 {len(filtered_orders)} delivery order(s) ready")
    st.divider()

    for idx, o in enumerate(filtered_orders):
        order_code    = o.get("order_code", o.get("id","N/A"))
        rider_name    = o.get("assigned_rider","")
        order_total   = float(o.get("total_price",0))
        balance       = float(o.get("total_balance",0))
        balance_method= o.get("balance_payment_method","N/A")
        recip_name    = o.get("recipient_name") or o["customer_name"]
        recip_contact = o.get("recipient_contact") or o["customer_contact"]
        surprise_note = "🤫 **SURPRISE — do NOT mention sender**" if o.get("is_surprise") else ""
        banner_color  = "#DC3545" if balance>0 and balance_method=="COD" else "#FFC107" if balance>0 else "#28A745"
        payment_banner= f"⚠️ **COLLECT ₱{balance:,.2f} via COD**" if balance>0 and balance_method=="COD" else f"⚠️ **BALANCE ₱{balance:,.2f} via {balance_method}**" if balance>0 else "✅ **FULLY PAID — Nothing to collect**"

        with st.expander(f"📦 {order_code} — {o['customer_name']} | Rider: {rider_name or '⏳ Unassigned'}"):
            if not rider_name:
                st.warning("⏳ **Rider not yet assigned**")
                ra1,ra2 = st.columns([2,1])
                with ra1:
                    sel_rider = st.selectbox("Assign Rider", rider_names, key=f"ar_{order_code}", label_visibility="collapsed")
                with ra2:
                    if st.button("✓ Assign Rider", key=f"arbtn_{order_code}"):
                        db.update_order(o["id"],{"assigned_rider": sel_rider}); st.rerun()
            st.divider()
            st.markdown(f"""
            <div class="print-sheet">
              <h3>🚴 RIDER DELIVERY SHEET</h3>
              <hr style="border:1px solid #C85C8E;"/>
              <p><strong>Order Code:</strong> {order_code} &nbsp;|&nbsp; <strong>Customer (Buyer):</strong> {o['customer_name']}</p>
              <p><strong>Rider:</strong> {rider_name or '—'} &nbsp;|&nbsp; <strong>Rider Contact:</strong> {rider_contacts.get(rider_name,'—')}</p>
              <hr style="border:1px solid #C85C8E;"/>
              <p><strong>📍 Deliver TO (Recipient):</strong> <span style="font-size:17px;"><strong>{recip_name}</strong></span></p>
              <p><strong>Recipient Contact:</strong> {recip_contact}</p>
              {"<p style='color:#C85C8E; font-weight:700;'>" + surprise_note + "</p>" if surprise_note else ""}
              <p><strong>Delivery Address:</strong> {o.get('delivery_address','')}</p>
              <p><strong>Zone:</strong> {o.get('delivery_zone','N/A')} &nbsp;|&nbsp; <strong>Attempts:</strong> {o.get('delivery_attempts',0)}</p>
              <p><strong>Date:</strong> {str(o.get('target_date',''))[:10]} &nbsp; <strong>Time:</strong> {o.get('target_time','')}</p>
              <hr style="border:1px solid #C85C8E;"/>
              <p><strong>Arrangement:</strong> {o['arrangement']} × {o['quantity']}</p>
              <p><strong>Order Total:</strong> ₱{order_total:,.2f}</p>
              <p><strong>Down Paid:</strong> ₱{float(o.get('down_payment_amount',0)):,.2f}</p>
              <p style="font-size:18px; font-weight:700; color:{banner_color};">{payment_banner}</p>
            </div>
            """, unsafe_allow_html=True)

            # Finished product picture
            fp = o.get("finished_product_picture")
            if fp:
                st.markdown("#### 📸 Finished Product")
                st.image(fp, caption="Ready for delivery", width=350)

            # Proof of delivery
            st.markdown("#### 📷 Proof of Delivery")
            pod = o.get("proof_of_delivery")
            if pod:
                st.success("✅ Proof of delivery already uploaded.")
                st.image(pod, caption="Delivery Proof", width=300)
                if st.button(f"✅ Mark as DELIVERED", key=f"mkdel_{order_code}"):
                    db.update_order_status(o["id"],"Delivered")
                    st.success("✅ Order marked as DELIVERED!"); st.rerun()
            else:
                st.warning("📷 **Upload a proof of delivery photo before marking as Delivered.**")
                proof_image = st.file_uploader(
                    "Upload Proof of Delivery Photo",
                    type=["jpg","jpeg","png","webp"], key=f"pod_upload_{order_code}",
                    help="Take a photo on your phone and upload it here.",
                )
                if proof_image:
                    st.image(proof_image, caption="Preview", width=300)
                    if st.button(f"📸 Confirm & Mark DELIVERED", key=f"mkdel_{order_code}"):
                        ext = proof_image.name.split(".")[-1].lower()
                        path = f"orders/{order_code}/delivery_proof/{uuid.uuid4().hex[:8]}.{ext}"
                        url = db.upload_file(proof_image.getvalue(), path, content_type=proof_image.type or "image/jpeg")
                        db.update_order(o["id"], {"proof_of_delivery": url})
                        db.update_order_status(o["id"],"Delivered")
                        st.success("✅ Order marked as DELIVERED with proof!"); st.rerun()

            # Failed delivery
            st.divider()
            if o["status"] != "Failed Delivery":
                if st.button(f"⚠️ Report Delivery Issue", key=f"fail_btn_{order_code}"):
                    st.session_state[f"reporting_fail_{order_code}"] = True
            if st.session_state.get(f"reporting_fail_{order_code}"):
                fc1,fc2 = st.columns(2)
                fail_reason = fc1.selectbox("Failure Reason", DELIVERY_FAILURE_REASONS, key=f"frsn_{order_code}")
                if fc2.button("✅ Submit Report", key=f"fsubmit_{order_code}"):
                    db.update_order(o["id"],{"status":"Failed Delivery","delivery_attempts":o.get("delivery_attempts",0)+1,"delivery_fail_reason":fail_reason})
                    st.session_state.pop(f"reporting_fail_{order_code}", None)
                    st.warning(f"⚠️ Order {order_code} marked as Failed Delivery."); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SCHEDULE
# ─────────────────────────────────────────────────────────────────────────────
def page_schedule():
    st.markdown("<div class='section-header'>📅 Schedule</div>", unsafe_allow_html=True)
    orders = scope_by_branch(db.get_orders())
    active = [o for o in orders if o["status"] != "Cancelled"]
    today  = date.today()

    view = st.radio("View", ["Today","Tomorrow","This Week","Custom Date"], horizontal=True)
    if view == "Today":        target_dates = [today.isoformat()]; label = "Today"
    elif view == "Tomorrow":   target_dates = [(today+timedelta(days=1)).isoformat()]; label = "Tomorrow"
    elif view == "This Week":  target_dates = [(today+timedelta(days=i)).isoformat() for i in range(7)]; label = "Next 7 Days"
    else:
        custom = st.date_input("Select Date")
        target_dates = [custom.isoformat()]; label = custom.isoformat()

    filtered = sorted([o for o in active if str(o.get("target_date",""))[:10] in target_dates],
                       key=lambda x: (str(x.get("target_date","")), x.get("target_time","")))

    c1,c2,c3 = st.columns(3)
    c1.metric(f"Total Orders ({label})", len(filtered))
    c2.metric("Deliveries", len([o for o in filtered if o.get("order_type")=="Delivery"]))
    c3.metric("Pick-ups",   len([o for o in filtered if o.get("order_type")=="Pick-up"]))
    st.divider()

    if not filtered:
        st.info(f"No orders scheduled for {label}."); return
    by_date = {}
    for o in filtered:
        by_date.setdefault(str(o.get("target_date",""))[:10], []).append(o)
    for d, day_orders in sorted(by_date.items()):
        st.markdown(f"#### 📅 {d}")
        for o in sorted(day_orders, key=lambda x: x.get("target_time","")):
            status_c = STATUS_COLOR.get(o["status"],"#888")
            rush = " 🚀" if o.get("priority_rush") else ""
            st.markdown(
                f"**{o['target_time']}** | `{o.get('order_code','N/A')}`{rush} | "
                f"{o['customer_name']} | {o.get('arrangement','')} | ₱{float(o.get('total_price',0)):,.0f} | "
                f"<span style='color:{status_c}; font-weight:700;'>{o['status']}</span>",
                unsafe_allow_html=True,
            )
        st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CUSTOMERS (CRM)
# ─────────────────────────────────────────────────────────────────────────────
def page_customers():
    st.markdown("<div class='section-header'>👤 Customers</div>", unsafe_allow_html=True)
    orders = scope_by_branch(db.get_orders())

    if not orders:
        st.info("No order data yet."); return

    search = st.text_input("🔍 Search by name or contact number", key="cust_search")

    # Aggregate per customer (by contact number)
    customers = {}
    for o in orders:
        contact = o.get("customer_contact","").strip()
        if not contact:
            continue
        c = customers.setdefault(contact, {
            "name": o.get("customer_name",""),
            "contact": contact,
            "orders": [],
            "total_spent": 0.0,
            "completed": 0,
            "cancelled": 0,
        })
        c["orders"].append(o)
        if o.get("status") in ("Delivered","Picked Up"):
            c["total_spent"] += float(o.get("total_price",0))
            c["completed"] += 1
        elif o.get("status") == "Cancelled":
            c["cancelled"] += 1
        # Keep the most recently used name
        if o.get("created_at","") >= max((x.get("created_at","") for x in c["orders"]), default=""):
            c["name"] = o.get("customer_name", c["name"])

    rows = []
    for contact, c in customers.items():
        last_order = sorted(c["orders"], key=lambda x: x.get("created_at",""), reverse=True)[0]
        rows.append({
            "Name": c["name"],
            "Contact": contact,
            "Total Orders": len(c["orders"]),
            "Completed": c["completed"],
            "Cancelled": c["cancelled"],
            "Lifetime Spend (₱)": c["total_spent"],
            "Last Order Date": str(last_order.get("target_date",""))[:10],
            "Last Status": last_order.get("status",""),
        })

    if search:
        q = search.lower()
        rows = [r for r in rows if q in r["Name"].lower() or q in r["Contact"]]

    rows = sorted(rows, key=lambda x: x["Lifetime Spend (₱)"], reverse=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("👥 Unique Customers", len(customers))
    c2.metric("🔁 Returning Customers", len([r for r in rows if r["Total Orders"] > 1]))
    c3.metric("💰 Total Lifetime Revenue", f"₱{sum(r['Lifetime Spend (₱)'] for r in rows):,.0f}")
    st.divider()

    if not rows:
        st.info("No customers match your search."); return

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format({"Lifetime Spend (₱)": "₱{:,.2f}"}),
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.markdown("##### 📜 Order History")
    selected_contact = st.selectbox(
        "View order history for:",
        options=[r["Contact"] for r in rows],
        format_func=lambda c: f"{customers[c]['name']} ({c})",
    )
    if selected_contact:
        hist = sorted(customers[selected_contact]["orders"], key=lambda x: x.get("created_at",""), reverse=True)
        for o in hist:
            status_c = STATUS_COLOR.get(o["status"],"#888")
            st.markdown(
                f"**`{o.get('order_code','')}`** · {str(o.get('target_date',''))[:10]} · "
                f"{o.get('arrangement','')} ×{o.get('quantity',1)} · ₱{float(o.get('total_price',0)):,.0f} · "
                f"<span style='color:{status_c}; font-weight:700;'>{o['status']}</span>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.download_button(
        "⬇️ Export Customer List CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"customers_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )



# ─────────────────────────────────────────────────────────────────────────────
# PAGE: INVENTORY
# ─────────────────────────────────────────────────────────────────────────────

@st.dialog("➕ Add New Inventory Item")
def _inventory_add_modal():
    with st.form("modal_inv_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        name     = c1.text_input("Item Name *", placeholder="e.g. CHINA ROSES")
        category = c2.selectbox("Category *", list(INVENTORY_CATEGORIES.keys()))
        c1,c2   = st.columns(2)
        modal_branch_options = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
        default_idx = modal_branch_options.index(CURRENT_BRANCH) if CURRENT_BRANCH in modal_branch_options else 0
        branch  = c1.selectbox("Branch *", modal_branch_options, index=default_idx)
        qty     = c2.number_input("Initial Quantity", min_value=0, value=0)
        c1,c2,c3 = st.columns(3)
        unit    = c1.text_input("Unit", value="pcs")
        cost    = c2.number_input("Unit Cost (₱)", min_value=0.0, step=10.0)
        reorder = c3.number_input("Reorder Point", min_value=1, value=10)
        notes_i = st.text_input("Notes (optional)")
        col_save, col_cancel = st.columns(2)
        save_clicked   = col_save.form_submit_button("✅ Add Item",  use_container_width=True)
        cancel_clicked = col_cancel.form_submit_button("✖ Cancel",  use_container_width=True)
    if cancel_clicked: st.rerun()
    if save_clicked:
        if not name:
            st.error("❌ Item name is required.")
        else:
            db.save_inventory_item({
                "id": str(uuid.uuid4())[:8], "name": name.strip(),
                "category": category, "branch": branch, "quantity": qty,
                "unit": unit, "unit_cost": cost, "reorder_point": reorder,
                "notes": notes_i, "created_at": datetime.now().isoformat(),
            })
            st.success(f"✅ **{name}** added to {branch}!"); st.rerun()


def page_inventory():
    st.markdown("<div class='section-header'>📦 Inventory Management</div>", unsafe_allow_html=True)
    inventory = scope_by_branch(db.get_inventory())

    tab_inv, tab_adjust, tab_count, tab_log, tab_backfill = st.tabs([
        "📦 Stock List",
        "🔧 Manual Adjustment",
        "📋 Stock Count Entry",
        "📜 Audit Log",
        "🔁 Backfill",
    ])

    # ── TAB 1: STOCK LIST ─────────────────────────────────────────────────
    with tab_inv:
        hdr1, hdr2 = st.columns([5, 1])
        with hdr1:
            st.markdown("#### 📦 Current Stock — All Categories")
        with hdr2:
            if st.button("➕ Add Item", use_container_width=True, type="primary"):
                _inventory_add_modal()

        c1, c2, c3 = st.columns(3)
        category_filter    = c1.selectbox("Filter Category", ["All"] + list(INVENTORY_CATEGORIES.keys()))
        inv_branch_options = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
        branch_filter      = c2.selectbox("Filter Branch",   ["All"] + inv_branch_options)
        search_inv         = c3.text_input("🔍 Search item name")

        filtered = inventory.copy()
        if category_filter != "All":
            filtered = [i for i in filtered if i.get("category") == category_filter]
        if branch_filter != "All":
            filtered = [i for i in filtered if i.get("branch") == branch_filter]
        if search_inv:
            filtered = [i for i in filtered if search_inv.lower() in i.get("name","").lower()]

        if not filtered:
            st.info("No items match. Use **➕ Add Item** to get started.")
        else:
            total_val  = sum(i.get("quantity", 0) * i.get("unit_cost", 0) for i in filtered)
            low_count  = len([i for i in filtered if i.get("quantity", 0) <= i.get("reorder_point", 10)])
            sm1, sm2, sm3 = st.columns(3)
            sm1.metric("📦 Items",       len(filtered))
            sm2.metric("💰 Total Value", f"₱{total_val:,.2f}")
            sm3.metric("🔴 Low Stock",   low_count)

            st.download_button("⬇️ Export Inventory CSV", data=inventory_to_csv(filtered),
                file_name=f"angies_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv")
            st.divider()

            # Group by category for display
            for cat in list(INVENTORY_CATEGORIES.keys()):
                cat_items = [i for i in sorted(filtered, key=lambda x: x.get("quantity", 0))
                             if i.get("category") == cat]
                if not cat_items:
                    continue
                st.markdown(f"##### {cat}")
                for item in cat_items:
                    qty     = item.get("quantity", 0)
                    reorder = item.get("reorder_point", 10)
                    status  = ("🔴🔴 NEGATIVE" if qty < 0 else
                               "🔴 Low"        if qty <= reorder else
                               "🟡 Medium"     if qty <= reorder * 2 else
                               "🟢 Optimal")
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([2.5, 1.2, 0.8, 0.8, 1, 0.6])
                    ic1.write(f"**{item['name']}** — {item.get('branch','')}")
                    ic2.write(item.get("unit", ""))
                    ic3.write(str(qty))
                    ic4.write(status)
                    with ic5:
                        new_qty = st.number_input(
                            "qty", value=qty, min_value=min(0, qty),
                            label_visibility="collapsed", key=f"iq_{item['id']}"
                        )
                        if new_qty != qty:
                            db.update_inventory_item(item["id"], {"quantity": new_qty})
                            st.rerun()
                    with ic6:
                        if st.button("🗑", key=f"di_{item['id']}", use_container_width=True):
                            db.delete_inventory_item(item["id"]); st.rerun()
                    with st.expander(f"📋 Details — {item['name']}", expanded=False):
                        st.write(
                            f"- **Category:** {item.get('category','')}\n"
                            f"- **Branch:** {item.get('branch','')}\n"
                            f"- **Unit Cost:** ₱{item.get('unit_cost',0):,.2f}\n"
                            f"- **Total Value:** ₱{qty * item.get('unit_cost',0):,.2f}\n"
                            f"- **Reorder Point:** {reorder} {item.get('unit','')}\n"
                            f"- **Notes:** {item.get('notes','—')}\n"
                            f"- **Added:** {str(item.get('created_at',''))[:10]}"
                        )
                st.divider()

    # ── TAB 2: MANUAL ADJUSTMENT ──────────────────────────────────────────
    with tab_adjust:
        st.markdown("#### 🔧 Manual Stock Adjustment")
        st.caption("Use this to record stock changes not tied to an order — e.g. purchases, damages, returns.")

        inventory_fresh = scope_by_branch(db.get_inventory())
        adj_branch_opts = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]

        with st.form("manual_adj_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            adj_branch = ac1.selectbox("Branch *", adj_branch_opts)
            adj_cat    = ac2.selectbox("Category", ["All"] + list(INVENTORY_CATEGORIES.keys()))

            branch_items = [i for i in inventory_fresh if i.get("branch") == adj_branch]
            if adj_cat != "All":
                branch_items = [i for i in branch_items if i.get("category") == adj_cat]
            item_names   = [i["name"] for i in branch_items]

            if not item_names:
                st.warning("No items found for this branch/category. Add items first.")
                st.form_submit_button("Apply Adjustment", disabled=True)
            else:
                bc1, bc2, bc3 = st.columns(3)
                selected_name = bc1.selectbox("Item *", item_names)
                adj_direction = bc2.radio("Direction", ["➕ Add Stock", "➖ Remove Stock"], horizontal=True)
                adj_qty       = bc3.number_input("Quantity *", min_value=1, value=1)

                adj_reason = st.selectbox("Reason *", [
                    "Purchased / Restocked",
                    "Used (non-order)",
                    "Damaged / Spoiled",
                    "Returned",
                    "Count Correction",
                    "Other",
                ])
                adj_notes = st.text_input("Notes (optional)")

                submitted_adj = st.form_submit_button("✅ Apply Adjustment", use_container_width=True)

        if "submitted_adj" in dir() and submitted_adj and item_names:
            selected_item = next((i for i in inventory_fresh
                if i["name"] == selected_name and i.get("branch") == adj_branch), None)
            if selected_item:
                delta = adj_qty if "Add" in adj_direction else -adj_qty
                full_reason = f"{adj_reason}" + (f" — {adj_notes}" if adj_notes else "")
                msg = db.adjust_inventory_manual(
                    selected_item["id"], selected_item["name"],
                    adj_branch, delta, full_reason, CURRENT_USER.get("name","")
                )
                st.success(msg)
                st.rerun()

    # ── TAB 3: STOCK COUNT ENTRY ──────────────────────────────────────────
    with tab_count:
        st.markdown("#### 📋 Stock Count Entry")
        st.caption("Encode the florist's physical stock count form here. Each entry is logged for audit purposes.")

        count_branch_opts = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
        inventory_for_count = scope_by_branch(db.get_inventory())

        sc1, sc2, sc3 = st.columns(3)
        sc_branch = sc1.selectbox("Branch *", count_branch_opts, key="sc_branch")
        sc_shift  = sc2.radio("Shift *", ["Opening", "Closing"], horizontal=True, key="sc_shift")
        sc_date   = sc3.date_input("Date *", value=date.today(), key="sc_date")

        branch_inv = [i for i in inventory_for_count if i.get("branch") == sc_branch]
        if not branch_inv:
            st.warning(f"No inventory items found for {sc_branch}. Add items first.")
        else:
            st.markdown(f"**Entering {sc_shift} count for {sc_branch} — {sc_date}**")
            count_data = {}
            for cat in list(INVENTORY_CATEGORIES.keys()):
                cat_items = [i for i in branch_inv if i.get("category") == cat]
                if not cat_items:
                    continue
                st.markdown(f"**{cat}**")
                for item in cat_items:
                    col_name, col_sys, col_count = st.columns([3, 1, 1])
                    col_name.write(f"{item['name']}")
                    col_sys.write(f"System: {item.get('quantity', 0)}")
                    entered = col_count.number_input(
                        "Counted", min_value=0, value=max(0, int(item.get("quantity", 0))),
                        key=f"sc_{sc_shift}_{sc_branch}_{item['id']}_{sc_date}",
                        label_visibility="collapsed"
                    )
                    count_data[item["id"]] = {
                        "item": item,
                        "counted": entered,
                    }

            sc_notes = st.text_area("General Notes for this count (optional)", key="sc_notes")

            if st.button(f"💾 Save {sc_shift} Count for {sc_branch}", type="primary"):
                saved = 0
                for item_id, data in count_data.items():
                    item = data["item"]
                    counted = data["counted"]
                    sys_qty = int(item.get("quantity", 0))
                    variance = counted - sys_qty
                    entry = {
                        "id": str(uuid.uuid4())[:8],
                        "branch": sc_branch,
                        "shift": sc_shift,
                        "item_name": item["name"],
                        "category": item.get("category", ""),
                        "counted_qty": counted,
                        "previous_qty": sys_qty,
                        "variance": variance,
                        "notes": sc_notes,
                        "encoded_by": CURRENT_USER.get("name", ""),
                        "created_at": datetime.now().isoformat(),
                    }
                    db.save_stock_count_entry(entry)
                    db.log_inventory_change(
                        item["name"], sc_branch, 0, sys_qty, sys_qty,
                        f"{sc_shift} stock count — counted: {counted}, variance: {variance:+d}",
                        "", CURRENT_USER.get("name", "")
                    )
                    saved += 1
                st.success(f"✅ {sc_shift} count saved for {saved} items at {sc_branch}.")
                st.rerun()

            # Show recent counts
            st.divider()
            st.markdown("##### Recent Stock Count Entries")
            all_counts = db.get_stock_count_entries()
            recent_counts = [c for c in all_counts if c.get("branch") == sc_branch]
            recent_counts = sorted(recent_counts, key=lambda x: x.get("created_at",""), reverse=True)[:50]
            if recent_counts:
                df_counts = pd.DataFrame(recent_counts)
                display_cols = [col for col in ["created_at","shift","item_name","category",
                                                 "counted_qty","previous_qty","variance","encoded_by"]
                                if col in df_counts.columns]
                df_counts["created_at"] = df_counts["created_at"].apply(lambda x: str(x)[:19])
                st.dataframe(df_counts[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No count entries for this branch yet.")

    # ── TAB 4: AUDIT LOG ──────────────────────────────────────────────────
    with tab_log:
        st.markdown("#### 📜 Inventory Movement Log")
        st.caption("Every stock change is recorded here — orders, adjustments, waste, counts, backfill.")
        logs = db.get_inventory_logs()
        if CURRENT_ROLE not in ("Super Admin", "Branch Manager"):
            logs = [l for l in logs if l.get("branch") == CURRENT_BRANCH]
        if not logs:
            st.info("No inventory movements recorded yet.")
        else:
            log_search = st.text_input("🔍 Filter logs", key="inv_log_search",
                placeholder="Search by item, reason, order ID...")
            if log_search:
                q = log_search.lower()
                logs = [l for l in logs if
                    q in l.get("item_name","").lower() or
                    q in l.get("reason","").lower() or
                    q in l.get("order_id","").lower()]
            df_logs = pd.DataFrame(sorted(logs, key=lambda x: x.get("created_at",""), reverse=True))
            df_logs = df_logs.rename(columns={
                "item_name":"Item","branch":"Branch","change_qty":"Change",
                "qty_before":"Before","qty_after":"After","reason":"Reason",
                "order_id":"Order","logged_by":"By","created_at":"When"
            })
            keep = [c for c in ["When","Item","Branch","Change","Before","After","Reason","Order","By"]
                    if c in df_logs.columns]
            df_logs = df_logs[keep]
            df_logs["When"] = df_logs["When"].apply(lambda x: str(x)[:19])
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export Audit Log CSV",
                data=df_logs.to_csv(index=False).encode("utf-8"),
                file_name=f"inventory_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv")

    # ── TAB 5: BACKFILL (Super Admin only) ────────────────────────────────
    with tab_backfill:
        if CURRENT_ROLE != "Super Admin":
            st.info("🔒 Backfill is available to Super Admins only.")
        else:
            st.markdown("#### 🔁 Inventory Backfill from Past Orders")
            st.caption("One-time tool — deducts ALL past orders from current inventory.")
            backfill_flag = db.get_system_flag("inventory_backfill_applied")
            if backfill_flag:
                st.success(f"✅ Backfill already applied on **{backfill_flag}**. Cannot run again.")
            else:
                st.warning("⚠️ **Irreversible.** Reviews ALL orders ever logged.")
                if st.button("🔍 Preview Backfill Deductions", key="bf_preview_btn", type="primary"):
                    st.session_state["bf_preview_ready"] = True
                if st.session_state.get("bf_preview_ready"):
                    all_orders    = db.get_orders()
                    all_inventory = db.get_inventory()
                    deduction_map = {}
                    for o in all_orders:
                        branch_o = o.get("fulfillment_branch", o.get("branch",""))
                        for fi in (o.get("flower_items") or []):
                            fname    = fi.get("flower","").strip()
                            qty_used = int(fi.get("qty",1))
                            colors   = [c for c in fi.get("colors",[]) if c and c.lower()!="any"]
                            if not fname: continue
                            if not colors:
                                key = (fname.upper(), branch_o)
                                deduction_map[key] = deduction_map.get(key,0) + qty_used
                            else:
                                for color in colors:
                                    key = (f"{color.upper()} {fname.upper()}", branch_o)
                                    deduction_map[key] = deduction_map.get(key,0) + qty_used
                    if not deduction_map:
                        st.info("No flower items found.")
                    else:
                        preview_rows = []
                        for (item_name, branch_o), total_d in sorted(deduction_map.items()):
                            inv_match = next((i for i in all_inventory
                                if i.get("name","").strip().upper()==item_name
                                and i.get("branch","")==branch_o), None)
                            if inv_match is None and " " in item_name:
                                base = " ".join(item_name.split(" ")[1:])
                                inv_match = next((i for i in all_inventory
                                    if i.get("name","").strip().upper()==base
                                    and i.get("branch","")==branch_o), None)
                            curr  = int(inv_match.get("quantity",0)) if inv_match else "Not in inventory"
                            after = (curr - total_d) if isinstance(curr,int) else f"Will be created at -{total_d}"
                            preview_rows.append({"Flower":item_name,"Branch":branch_o,
                                "Total to Deduct":total_d,"Current Stock":curr,"Stock After":after})
                        df_preview = pd.DataFrame(preview_rows)
                        def _hl(row):
                            a = row["Stock After"]
                            if isinstance(a,int) and a < 0:  return ["background-color:#FFEBEE"]*len(row)
                            if isinstance(a,int) and a == 0: return ["background-color:#FFF3E0"]*len(row)
                            if not isinstance(a,int):        return ["background-color:#F3E5F5"]*len(row)
                            return [""]*len(row)
                        st.dataframe(df_preview.style.apply(_hl,axis=1), use_container_width=True, hide_index=True)
                        st.markdown("🔴 Red = goes negative &nbsp;|&nbsp; 🟠 Orange = hits 0 &nbsp;|&nbsp; 🟣 Purple = auto-created")
                        st.divider()
                        confirm = st.checkbox("✅ I reviewed the preview and want to apply this backfill", key="bf_confirm")
                        if confirm:
                            if st.button("🚀 Apply Backfill Now", key="bf_apply_btn", type="primary"):
                                with st.spinner("Applying backfill..."):
                                    total_warnings = []
                                    for (item_name, branch_o), total_d in deduction_map.items():
                                        fresh = db.get_inventory()
                                        match = next((i for i in fresh
                                            if i.get("name","").strip().upper()==item_name
                                            and i.get("branch","")==branch_o), None)
                                        if match is None and " " in item_name:
                                            base = " ".join(item_name.split(" ")[1:])
                                            match = next((i for i in fresh
                                                if i.get("name","").strip().upper()==base
                                                and i.get("branch","")==branch_o), None)
                                        if match:
                                            nq = int(match.get("quantity",0)) - total_d
                                            db.update_inventory_item(match["id"], {"quantity": nq})
                                            db.log_inventory_change(match["name"], branch_o, -total_d,
                                                int(match.get("quantity",0)), nq, "Inventory backfill", "", CURRENT_USER.get("name",""))
                                        else:
                                            nq = -total_d
                                            db.save_inventory_item({"id": str(uuid.uuid4())[:8],"name":item_name,
                                                "category":"🌹 Flowers","branch":branch_o,"quantity":nq,
                                                "unit":"pcs","unit_cost":0.0,"reorder_point":10,
                                                "notes":"Auto-created by backfill.","created_at":datetime.now().isoformat()})
                                            db.log_inventory_change(item_name, branch_o, -total_d, 0, nq,
                                                "Inventory backfill (auto-created)", "", CURRENT_USER.get("name",""))
                                        if nq <= 0: total_warnings.append(f"{'🔴🔴' if nq<0 else '🔴'} **{item_name}** ({branch_o}): {nq} pcs")
                                    db.set_system_flag("inventory_backfill_applied", datetime.now().strftime("%Y-%m-%d %H:%M"))
                                    db._invalidate_all()
                                st.success("✅ Backfill complete!")
                                if total_warnings:
                                    st.markdown("**Items at 0 or negative after backfill:**")
                                    for w in total_warnings: st.warning(w)
                                st.session_state["bf_preview_ready"] = False
                                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: WASTE TRACKER
# ─────────────────────────────────────────────────────────────────────────────
def page_waste_tracker():
    st.markdown("<div class='section-header'>♻️ Waste & Spoilage Tracker</div>", unsafe_allow_html=True)
    waste = scope_by_branch(db.get_waste())
    tab1,tab2 = st.tabs(["📋 Log","➕ Add Entry"])

    with tab1:
        if not waste:
            st.info("No waste entries logged yet.")
        else:
            st.download_button("⬇️ Export Waste CSV", data=waste_to_csv(waste),
                file_name=f"angies_waste_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
            total_waste_cost = sum(float(w.get("cost",0)) for w in waste)
            st.metric("Total Waste Cost", f"₱{total_waste_cost:,.2f}")
            st.divider()
            for w in sorted(waste, key=lambda x: str(x.get("date","")), reverse=True):
                wc1,wc2,wc3 = st.columns([3,1,0.7])
                wc1.write(f"**{w['item_name']}** | {w.get('branch','')} | {w['reason']} | {str(w.get('date',''))[:10]} | {w.get('quantity','')} {w.get('unit','')}")
                wc2.write(f"₱{float(w.get('cost',0)):,.0f}")
                if wc3.button("🗑", key=f"dw_{w['id']}"):
                    db.delete_waste_entry(w["id"]); st.rerun()

    with tab2:
        with st.form("log_waste"):
            c1,c2   = st.columns(2)
            item    = c1.text_input("Item Name *")
            qty     = c2.number_input("Quantity *", min_value=1, value=1)
            c1,c2,c3 = st.columns(3)
            unit    = c1.text_input("Unit", value="pcs")
            cost    = c2.number_input("Cost (₱) *", min_value=0.0, step=50.0)
            reason  = c3.selectbox("Reason *", WASTE_REASONS)
            waste_branch_options = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
            branch  = st.selectbox("Branch *", waste_branch_options)
            notes   = st.text_area("Notes")
            wdate   = st.date_input("Date")
            if st.form_submit_button("📝 Log Waste", use_container_width=True):
                if not item or cost == 0:
                    st.error("Item name and cost are required.")
                else:
                    db.save_waste_entry({
                        "id": str(uuid.uuid4())[:8], "item_name": item,
                        "quantity": qty, "unit": unit, "cost": cost,
                        "reason": reason, "branch": branch, "notes": notes,
                        "date": wdate.isoformat(), "logged_at": datetime.now().isoformat(),
                    })
                    st.success("✅ Waste entry logged!")
                    waste_warns = db.deduct_inventory_for_waste(
                        item, qty, branch, logged_by=CURRENT_USER.get("name","")
                    )
                    if waste_warns:
                        for w in waste_warns: st.warning(w)
                    else:
                        st.info(f"📦 Deducted {qty} {unit} of **{item}** from inventory at **{branch}**.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: STAFF MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
def page_staff_management():
    st.markdown("<div class='section-header'>👥 Staff Management</div>", unsafe_allow_html=True)
    florists = scope_by_branch(db.get_florists())
    riders   = scope_by_branch(db.get_riders())
    smgmt_branch_options = BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]
    tab1,tab2,tab3,tab4,tab5 = st.tabs(["🌹 Florists","➕ Add Florist","🚴 Riders","➕ Add Rider","🔐 Accounts"])

    with tab1:
        if not florists: st.info("No florists added yet.")
        for f in florists:
            load     = db.get_florist_active_load(f["name"])
            max_load = f.get("max_concurrent_orders",5)
            fc1,fc2,fc3,fc4 = st.columns([2.5,1.5,1,0.6])
            fc1.write(f"**{f['name']}** | 📱 {f.get('contact','')}")
            fc2.write(f"🏪 {f.get('branch','')}")
            fc3.write(f"📋 Load: {load}/{max_load}")
            if fc4.button("🗑", key=f"df_{f['id']}"):
                db.delete_florist(f["id"]); st.rerun()

    with tab2:
        with st.form("add_florist"):
            name     = st.text_input("Name *")
            contact  = st.text_input("Contact *")
            branch   = st.selectbox("Branch *", smgmt_branch_options)
            max_conc = st.number_input("Max Concurrent Orders", min_value=1, value=5)
            if st.form_submit_button("➕ Add Florist", use_container_width=True):
                if name and contact:
                    db.save_florist({"id":str(uuid.uuid4())[:8],"name":name,"contact":contact,"branch":branch,"max_concurrent_orders":max_conc,"created_at":datetime.now().isoformat()})
                    st.success(f"✅ Florist **{name}** added!")

    with tab3:
        if not riders: st.info("No riders added yet.")
        for r in riders:
            rc1,rc2,rc3 = st.columns([2.5,2,0.6])
            rc1.write(f"**{r['name']}** | 📱 {r.get('contact','')}")
            rc2.write(f"🏪 {r.get('branch','')}")
            if rc3.button("🗑", key=f"dr_{r['id']}"):
                db.delete_rider(r["id"]); st.rerun()

    with tab4:
        with st.form("add_rider"):
            name    = st.text_input("Name *")
            contact = st.text_input("Contact *")
            branch  = st.selectbox("Branch *", smgmt_branch_options)
            if st.form_submit_button("➕ Add Rider", use_container_width=True):
                if name and contact:
                    db.save_rider({"id":str(uuid.uuid4())[:8],"name":name,"contact":contact,"branch":branch,"created_at":datetime.now().isoformat()})
                    st.success(f"✅ Rider **{name}** added!")

    with tab5:
        st.markdown("##### 🔐 Login Accounts")
        st.caption("Each staff member logs in with their own 4-6 digit PIN.")
        accounts = db.get_staff_accounts()
        if CURRENT_ROLE != "Super Admin":
            accounts = [a for a in accounts if a.get("branch") == CURRENT_BRANCH]

        if not accounts:
            st.info("No accounts yet — create one below.")
        for a in sorted(accounts, key=lambda x: x.get("name","")):
            ac1,ac2,ac3,ac4 = st.columns([2,1.3,1.3,1])
            ac1.write(f"**{a['name']}**")
            ac2.write(a.get("role",""))
            ac3.write(f"🏪 {a.get('branch','')}")
            ac4.write("🟢 Active" if a.get("active",True) else "🔴 Inactive")
            with st.expander(f"⚙️ Manage {a['name']}"):
                mc1,mc2 = st.columns(2)
                new_pin = mc1.text_input("Set New PIN (4-6 digits)", key=f"pin_{a['id']}", max_chars=6, type="password", placeholder="••••••")
                if mc1.button("🔄 Reset PIN", key=f"resetpin_{a['id']}"):
                    if new_pin and new_pin.isdigit() and 4 <= len(new_pin) <= 6:
                        if db.pin_in_use(new_pin, exclude_id=a["id"]):
                            st.error("⚠️ That PIN is already in use by another account.")
                        else:
                            salt, pin_hash = db.make_pin_credentials(new_pin)
                            db.update_staff_account(a["id"], {"pin_salt": salt, "pin_hash": pin_hash})
                            st.success("✅ PIN updated!"); st.rerun()
                    else:
                        st.error("PIN must be 4-6 digits.")
                toggle_label = "🔴 Deactivate Account" if a.get("active",True) else "🟢 Activate Account"
                if mc2.button(toggle_label, key=f"toggleacc_{a['id']}"):
                    db.update_staff_account(a["id"], {"active": not a.get("active",True)})
                    st.rerun()
                if mc2.button("🗑 Delete Account", key=f"delacc_{a['id']}"):
                    db.delete_staff_account(a["id"]); st.rerun()

        st.divider()
        st.markdown("##### ➕ Create New Account")
        with st.form("add_account"):
            acc_name = st.text_input("Name *")
            if CURRENT_ROLE == "Super Admin":
                acc_role_options   = db.ROLES
                acc_branch_options = ["All"] + BRANCHES
            else:
                acc_role_options   = ["Staff","Florist","Rider"]
                acc_branch_options = [CURRENT_BRANCH]
            c1,c2 = st.columns(2)
            acc_role   = c1.selectbox("Role *", acc_role_options)
            acc_branch = c2.selectbox("Branch *", acc_branch_options)
            acc_pin    = st.text_input("PIN (4-6 digits) *", max_chars=6, type="password", placeholder="••••••")
            if st.form_submit_button("➕ Create Account", use_container_width=True):
                if not acc_name or not acc_pin:
                    st.error("Name and PIN are required.")
                elif not acc_pin.isdigit() or not (4 <= len(acc_pin) <= 6):
                    st.error("PIN must be 4-6 digits.")
                elif db.pin_in_use(acc_pin):
                    st.error("⚠️ This PIN is already in use. Choose a different one.")
                else:
                    salt, pin_hash = db.make_pin_credentials(acc_pin)
                    db.save_staff_account({
                        "id": str(uuid.uuid4())[:8], "name": acc_name,
                        "pin_salt": salt, "pin_hash": pin_hash,
                        "role": acc_role, "branch": acc_branch, "active": True,
                        "created_at": datetime.now().isoformat(),
                    })
                    st.success(f"✅ Account for **{acc_name}** created!")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: REPORTS
# ─────────────────────────────────────────────────────────────────────────────
def page_reports():
    st.markdown("<div class='section-header'>📈 Reports & Analytics</div>", unsafe_allow_html=True)
    orders    = scope_by_branch(db.get_orders())
    waste     = scope_by_branch(db.get_waste())
    inventory = scope_by_branch(db.get_inventory())
    florists  = scope_by_branch(db.get_florists())
    riders    = scope_by_branch(db.get_riders())
    if not orders:
        st.info("No order data yet."); return

    tab_labels = ["💰 Financial","🌹 Florists","🚴 Riders","📦 Inventory","🏆 Best Sellers","📍 Delivery Cities","📈 Restock Forecast","📅 Monthly","📆 Quarterly","🗓️ Yearly","📅 Daily & Weekly","💸 Expenses"]
    show_branch_compare = (CURRENT_ROLE == "Super Admin")
    if show_branch_compare: tab_labels.append("🏪 Branch Comparison")
    tabs = st.tabs(tab_labels)
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab_daily,tab_expenses = tabs[:12]
    tab11 = tabs[12] if show_branch_compare else None

    with tab1:
        completed  = [o for o in orders if o["status"] in ["Delivered","Picked Up"]]
        revenue    = sum(float(o.get("total_price",0)) for o in completed)
        waste_cost = sum(float(w.get("cost",0)) for w in waste)
        profit     = revenue - waste_cost
        margin     = (profit/revenue*100) if revenue>0 else 0
        avg_order  = revenue/len(completed) if completed else 0
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("💰 Revenue",       f"₱{revenue:,.0f}")
        c2.metric("📉 Waste",         f"₱{waste_cost:,.0f}")
        c3.metric("📈 Profit",        f"₱{profit:,.0f}")
        c4.metric("% Margin",         f"{margin:.1f}%")
        c5.metric("Avg Order Value",  f"₱{avg_order:,.0f}")
        st.divider()

        if completed:
            branch_rev = {}
            for o in completed:
                b = o.get("fulfillment_branch", o.get("branch","Unknown"))
                branch_rev[b] = branch_rev.get(b,0) + float(o.get("total_price",0))
            fc1,fc2 = st.columns(2)
            with fc1:
                st.markdown("**Revenue by Branch**")
                fig,ax = plt.subplots(figsize=(6,4), facecolor="#FDF6F0")
                ax.bar(branch_rev.keys(), branch_rev.values(), color="#C85C8E", alpha=0.85)
                ax.set_facecolor("#FDF6F0"); ax.grid(axis="y",alpha=0.3)
                plt.xticks(rotation=15, ha="right", fontsize=9); plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            with fc2:
                st.markdown("**Orders by Status**")
                status_counts = pd.Series([o["status"] for o in orders]).value_counts()
                colors = ["#C85C8E","#28A745","#FFC107","#17A2B8","#6C757D","#DC3545","#007BFF","#FF6B35"]
                fig,ax = plt.subplots(figsize=(6,4), facecolor="#FDF6F0")
                ax.pie(status_counts.values, labels=status_counts.index, colors=colors[:len(status_counts)], autopct="%1.0f%%", startangle=140)
                plt.tight_layout(); st.pyplot(fig); plt.close(fig)

            occ_counts = {}
            for o in orders:
                occ = o.get("occasion","Other"); occ_counts[occ] = occ_counts.get(occ,0)+1
            if occ_counts:
                st.markdown("**Orders by Occasion**")
                st.dataframe(pd.DataFrame(occ_counts.items(), columns=["Occasion","Count"]).sort_values("Count",ascending=False), use_container_width=True)

        st.divider()
        ex1,ex2,ex3 = st.columns(3)
        with ex1:
            st.download_button("⬇️ All Orders CSV", data=orders_to_csv(orders), file_name=f"all_orders_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        with ex2:
            st.download_button("⬇️ Completed Orders CSV", data=orders_to_csv(completed), file_name=f"completed_orders_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        with ex3:
            st.download_button("⬇️ Waste Log CSV", data=waste_to_csv(waste), file_name=f"waste_log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

    with tab2:
        if not florists: st.info("No florists added yet.")
        else:
            perf_data = []
            for f in florists:
                assigned = [o for o in orders if o.get("assigned_florist")==f["name"]]
                done     = [o for o in assigned if o["status"] in ["Delivered","Picked Up"]]
                rate     = (len(done)/len(assigned)*100) if assigned else 0
                rev      = sum(float(o.get("total_price",0)) for o in done)
                load     = db.get_florist_active_load(f["name"])
                perf_data.append({"Florist":f["name"],"Branch":f.get("branch",""),"Current Load":f"{load}/{f.get('max_concurrent_orders',5)}","Assigned":len(assigned),"Completed":len(done),"Completion %":f"{rate:.0f}%","Revenue Handled":f"₱{rev:,.0f}"})
            st.dataframe(pd.DataFrame(perf_data), use_container_width=True)

    with tab3:
        if not riders: st.info("No riders added yet.")
        else:
            rider_data = []
            for r in riders:
                assigned  = [o for o in orders if o.get("assigned_rider")==r["name"]]
                delivered = [o for o in assigned if o["status"]=="Delivered"]
                failed    = [o for o in assigned if o["status"]=="Failed Delivery"]
                rate      = (len(delivered)/len(assigned)*100) if assigned else 0
                cod_amt   = sum(float(o.get("total_balance",0)) for o in delivered if o.get("balance_payment_method")=="COD")
                rider_data.append({"Rider":r["name"],"Branch":r.get("branch",""),"Assigned":len(assigned),"Delivered":len(delivered),"Failed":len(failed),"Delivery %":f"{rate:.0f}%","COD Collected":f"₱{cod_amt:,.0f}"})
            st.dataframe(pd.DataFrame(rider_data), use_container_width=True)

    with tab4:
        if not inventory: st.info("No inventory items yet.")
        else:
            low  = len([i for i in inventory if i.get("quantity",0)<=i.get("reorder_point",10)])
            med  = len([i for i in inventory if i.get("reorder_point",10)<i.get("quantity",0)<=i.get("reorder_point",10)*2])
            high = len([i for i in inventory if i.get("quantity",0)>i.get("reorder_point",10)*2])
            total_val = sum(float(i.get("unit_cost",0))*i.get("quantity",0) for i in inventory)
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("🔴 Low Stock",  low); c2.metric("🟡 Medium",med)
            c3.metric("🟢 Optimal",   high); c4.metric("💰 Total Value",f"₱{total_val:,.0f}")
            low_items = [i for i in inventory if i.get("quantity",0)<=i.get("reorder_point",10)]
            if low_items:
                st.warning(f"⚠️ {len(low_items)} item(s) at or below reorder point:")
                st.dataframe(pd.DataFrame([{"Item":i["name"],"Branch":i.get("branch",""),"Qty":i["quantity"],"Reorder At":i.get("reorder_point",10),"Unit":i.get("unit","")} for i in low_items]), use_container_width=True)

    with tab5:
        bs1,bs2,bs3 = st.columns(3)
        bs_branch = bs1.selectbox("Branch",["All"]+ (BRANCHES if (CURRENT_ROLE=="Super Admin" or CURRENT_BRANCH=="All") else [CURRENT_BRANCH]), key="bs_branch")
        bs_from   = bs2.date_input("From", value=date.today()-timedelta(days=30), key="bs_from")
        bs_to     = bs3.date_input("To",   value=date.today(), key="bs_to")
        bs_orders = [o for o in orders if bs_from.isoformat() <= str(o.get("target_date",""))[:10] <= bs_to.isoformat() and (bs_branch=="All" or o.get("fulfillment_branch",o.get("branch",""))==bs_branch)]
        if not bs_orders: st.info("No orders found for the selected filters.")
        else:
            arr_counts={}; arr_revenue={}; arr_qty={}
            for o in bs_orders:
                arr = o.get("arrangement","Unknown"); qty = int(o.get("quantity",1)); rev = float(o.get("total_price",0))
                arr_counts[arr]=arr_counts.get(arr,0)+1; arr_qty[arr]=arr_qty.get(arr,0)+qty; arr_revenue[arr]=arr_revenue.get(arr,0)+rev
            sorted_arr = sorted(arr_qty.items(), key=lambda x: x[1], reverse=True); top_n = sorted_arr[:10]
            bsc1,bsc2,bsc3 = st.columns(3)
            bsc1.metric("🌸 Unique Arrangements", len(arr_counts))
            bsc2.metric("🏆 #1 Best Seller", top_n[0][0][:25] if top_n else "—")
            bsc3.metric("📦 Units (Top 1)", top_n[0][1] if top_n else 0)
            st.divider()
            if top_n:
                fig,ax = plt.subplots(figsize=(9,5), facecolor="#FDF6F0")
                bars = ax.barh([a[0] for a in reversed(top_n)],[a[1] for a in reversed(top_n)], color="#C85C8E", alpha=0.85)
                ax.set_facecolor("#FDF6F0"); ax.grid(axis="x",alpha=0.3); ax.set_xlabel("Units Sold")
                for bar,val in zip(bars,[a[1] for a in reversed(top_n)]):
                    ax.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2, str(val), va="center", fontsize=9)
                plt.tight_layout(); st.pyplot(fig); plt.close(fig)
            rank_rows = [{"Rank":"🥇" if r==1 else "🥈" if r==2 else "🥉" if r==3 else f"#{r}","Arrangement":arr,"Orders":arr_counts.get(arr,0),"Units Sold":units,"Revenue (₱)":f"₱{arr_revenue.get(arr,0):,.2f}","Avg/Order (₱)":f"₱{arr_revenue.get(arr,0)/arr_counts.get(arr,1):,.2f}"} for r,(arr,units) in enumerate(sorted_arr,1)]
            st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)

    with tab6:
        dc1,dc2,dc3 = st.columns(3)
        cty_branch = dc1.selectbox("Branch",["All"]+ (BRANCHES if (CURRENT_ROLE=="Super Admin" or CURRENT_BRANCH=="All") else [CURRENT_BRANCH]), key="cty_branch")
        cty_from   = dc2.date_input("From", value=date.today()-timedelta(days=30), key="cty_from")
        cty_to     = dc3.date_input("To",   value=date.today(), key="cty_to")
        delivery_orders = [o for o in orders if o.get("order_type")=="Delivery" and cty_from.isoformat() <= str(o.get("target_date",""))[:10] <= cty_to.isoformat() and (cty_branch=="All" or o.get("fulfillment_branch",o.get("branch",""))==cty_branch)]
        if not delivery_orders: st.info("No delivery orders found for the selected filters.")
        else:
            zone_counts={}; zone_revenue={}; zone_failed={}
            for o in delivery_orders:
                zone = o.get("delivery_zone","").strip() or "Unspecified"
                zone_counts[zone]=zone_counts.get(zone,0)+1; zone_revenue[zone]=zone_revenue.get(zone,0)+float(o.get("total_price",0))
                if o.get("status")=="Failed Delivery": zone_failed[zone]=zone_failed.get(zone,0)+1
            sorted_zones = sorted(zone_counts.items(), key=lambda x: x[1], reverse=True)
            zc1,zc2,zc3,zc4 = st.columns(4)
            zc1.metric("🚴 Total Deliveries",len(delivery_orders)); zc2.metric("📍 Zones Served",len(zone_counts))
            zc3.metric("🏆 Top Zone", sorted_zones[0][0] if sorted_zones else "—"); zc4.metric("❌ Failed",sum(zone_failed.values()))
            st.divider()
            city_rows = [{"Zone":zone,"Deliveries":count,"Revenue (₱)":f"₱{zone_revenue.get(zone,0):,.2f}","Avg Order (₱)":f"₱{zone_revenue.get(zone,0)/count:,.2f}","Failed":zone_failed.get(zone,0),"Failure Rate":f"{zone_failed.get(zone,0)/count*100:.1f}%"} for zone,count in sorted_zones]
            st.dataframe(pd.DataFrame(city_rows), use_container_width=True, hide_index=True)
            st.divider()
            max_count = sorted_zones[0][1] if sorted_zones else 1
            for rank,(zone,count) in enumerate(sorted_zones,1):
                medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"#{rank}"
                pct   = count/max_count
                st.markdown(f"<div class='city-rank-bar'><strong>{medal} {zone}</strong> &nbsp; <span style='color:#C85C8E; font-weight:700;'>{count} deliveries</span><div style='background:#F0D9E0; border-radius:4px; height:8px; margin-top:4px;'><div style='background:#C85C8E; width:{pct*100:.0f}%; height:8px; border-radius:4px;'></div></div></div>", unsafe_allow_html=True)

    # ── RESTOCK FORECAST ────────────────────────────────────────────────────
    with tab7:
        st.markdown("##### 📈 Restock Forecast")
        st.caption("Estimates based on flower usage from orders placed in the last 30 days. Matches inventory item names against flowers used in the Flower Builder.")

        lookback_days = 30
        cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
        recent_orders = [o for o in orders if str(o.get("target_date",""))[:10] >= cutoff and o.get("status") != "Cancelled"]

        usage = {}
        for o in recent_orders:
            for fi in (o.get("flower_items") or []):
                fname = fi.get("flower","").strip().lower()
                if fname:
                    usage[fname] = usage.get(fname, 0) + int(fi.get("qty",1))

        if not usage:
            st.info("Not enough order history with flower details yet to forecast usage — this improves as more orders are logged with the Flower Builder.")
        else:
            forecast_rows = []
            for item in inventory:
                iname = item.get("name","").strip().lower()
                used = usage.get(iname, 0)
                current_qty = item.get("quantity",0)
                daily_rate = used / lookback_days if used else 0
                days_left = (current_qty / daily_rate) if daily_rate > 0 else None
                forecast_rows.append({
                    "Item": item.get("name",""),
                    "Branch": item.get("branch",""),
                    "Current Stock": current_qty,
                    f"Used (last {lookback_days}d)": used,
                    "Avg Daily Use": round(daily_rate,2),
                    "Est. Days Until Stockout": round(days_left,1) if days_left is not None else None,
                    "Reorder Point": item.get("reorder_point",10),
                })

            df_forecast = pd.DataFrame(forecast_rows)
            df_forecast["_sort"] = df_forecast["Est. Days Until Stockout"].apply(lambda v: v if v is not None else float("inf"))
            df_forecast = df_forecast.sort_values("_sort").drop(columns="_sort")
            df_forecast["Est. Days Until Stockout"] = df_forecast["Est. Days Until Stockout"].apply(lambda v: f"{v:.1f}" if v is not None else "—")

            urgent = [r for r in forecast_rows if r["Est. Days Until Stockout"] is not None and r["Est. Days Until Stockout"] <= 14]
            if urgent:
                st.warning(f"⚠️ {len(urgent)} item(s) projected to run out within 14 days based on recent usage: " + ", ".join(r["Item"] for r in urgent))

            st.dataframe(df_forecast, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Export Restock Forecast CSV",
                data=df_forecast.to_csv(index=False).encode("utf-8"),
                file_name=f"restock_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    # ── PERIOD REPORT HELPER ─────────────────────────────────────────────────
    def render_period_report(tab, period_label, group_fn):
        with tab:
            st.markdown(f"##### {period_label} Sales & Performance Report")
            rp1,rp2=st.columns(2)
            rp_branch=rp1.selectbox("Branch",["All"]+(BRANCHES if (CURRENT_ROLE=="Super Admin" or CURRENT_BRANCH=="All") else [CURRENT_BRANCH]),key=f"rp_branch_{period_label}")
            rp_year=rp2.number_input("Year",min_value=2023,max_value=date.today().year+1,value=date.today().year,step=1,key=f"rp_year_{period_label}")
            yr_orders=[o for o in orders if str(o.get("target_date",""))[:4]==str(rp_year) and (rp_branch=="All" or o.get("fulfillment_branch",o.get("branch",""))==rp_branch)]
            if not yr_orders: st.info(f"No orders found for {rp_branch} in {rp_year}."); return
            completed_r=[o for o in yr_orders if o["status"] in ("Delivered","Picked Up")]
            revenue_r=sum(float(o.get("total_price",0)) for o in completed_r)
            waste_r=[w for w in waste if str(w.get("date",""))[:4]==str(rp_year) and (rp_branch=="All" or w.get("branch","")==rp_branch)]
            waste_cost_r=sum(float(w.get("cost",0)) for w in waste_r)
            cod_r=sum(float(o.get("total_balance",0)) for o in completed_r if o.get("balance_payment_method")=="COD")
            m1,m2,m3,m4,m5=st.columns(5)
            m1.metric("📦 Total Orders",len(yr_orders)); m2.metric("✅ Completed",len(completed_r))
            m3.metric("💰 Revenue",f"₱{revenue_r:,.0f}"); m4.metric("📉 Waste Cost",f"₱{waste_cost_r:,.0f}"); m5.metric("⚠️ COD",f"₱{cod_r:,.0f}")
            st.divider()
            period_data={}
            for o in completed_r:
                k=group_fn(o)
                period_data[k]=period_data.get(k,{"orders":0,"revenue":0.0})
                period_data[k]["orders"]+=1; period_data[k]["revenue"]+=float(o.get("total_price",0))
            if period_data:
                sk=sorted(period_data.keys())
                fig,ax=plt.subplots(figsize=(10,4),facecolor="#FDF6F0")
                ax.bar(sk,[period_data[k]["revenue"] for k in sk],color="#C85C8E",alpha=0.85)
                ax.set_facecolor("#FDF6F0"); ax.grid(axis="y",alpha=0.3); plt.xticks(rotation=30,ha="right",fontsize=9); ax.set_ylabel("Revenue (₱)")
                plt.tight_layout(); st.pyplot(fig); plt.close(fig); st.divider()
                st.dataframe(pd.DataFrame([{"Period":k,"Orders":period_data[k]["orders"],"Revenue (₱)":f"₱{period_data[k]['revenue']:,.2f}"} for k in sk]),use_container_width=True,hide_index=True); st.divider()
            arr_cnt={}; arr_rev={}
            for o in completed_r:
                a=o.get("arrangement","Unknown"); arr_cnt[a]=arr_cnt.get(a,0)+int(o.get("quantity",1)); arr_rev[a]=arr_rev.get(a,0)+float(o.get("total_price",0))
            if arr_cnt:
                top5=sorted(arr_cnt.items(),key=lambda x:x[1],reverse=True)[:5]
                st.markdown("**Top 5 Arrangements**")
                st.dataframe(pd.DataFrame([{"Arrangement":a,"Units":u,"Revenue":f"₱{arr_rev.get(a,0):,.2f}"} for a,u in top5]),use_container_width=True,hide_index=True); st.divider()
            if CURRENT_ROLE=="Super Admin" and rp_branch=="All":
                b_rev={}
                for o in completed_r: b=o.get("fulfillment_branch",o.get("branch","Unknown")); b_rev[b]=b_rev.get(b,0)+float(o.get("total_price",0))
                st.markdown("**Revenue by Branch**"); st.dataframe(pd.DataFrame([{"Branch":b,"Revenue (₱)":f"₱{r:,.2f}"} for b,r in sorted(b_rev.items(),key=lambda x:x[1],reverse=True)]),use_container_width=True,hide_index=True); st.divider()
            st.download_button(f"⬇️ Export {period_label} CSV",data=pd.DataFrame([{"Order Code":o.get("order_code",""),"Customer":o.get("customer_name",""),"Branch":o.get("fulfillment_branch",o.get("branch","")),"Total":o.get("total_price",0),"Status":o.get("status",""),"Target Date":str(o.get("target_date",""))[:10]} for o in yr_orders]).to_csv(index=False).encode("utf-8"),file_name=f"report_{period_label.lower().replace(' ','_')}_{rp_year}.csv",mime="text/csv",use_container_width=True)
    render_period_report(tab8,"Monthly",lambda o:date.fromisoformat(str(o.get("target_date","2000-01-01"))[:10]).strftime("%Y-%m (%B)"))
    render_period_report(tab9,"Quarterly",lambda o:f"Q{(date.fromisoformat(str(o.get('target_date','2000-01-01'))[:10]).month-1)//3+1} {str(o.get('target_date','2000'))[:4]}")
    render_period_report(tab10,"Yearly",lambda o:str(o.get("target_date","2000-01-01"))[:4])
    # ── BRANCH COMPARISON (Super Admin only) ────────────────────────────────
    if show_branch_compare:
        with tab11:
            st.markdown("##### 🏪 Branch Comparison")
            st.caption("Compares all branches side-by-side. Visible to Super Admin only.")
            
            bc_rows = []
            for branch in BRANCHES:
                b_orders    = [o for o in orders if o.get("fulfillment_branch", o.get("branch","")) == branch]
                b_completed = [o for o in b_orders if o["status"] in ("Delivered","Picked Up")]
                b_revenue   = sum(float(o.get("total_price",0)) for o in b_completed)
                b_avg       = (b_revenue / len(b_completed)) if b_completed else 0
                b_cancelled = len([o for o in b_orders if o["status"] == "Cancelled"])
                b_failed    = len([o for o in b_orders if o["status"] == "Failed Delivery"])
                b_waste     = sum(float(w.get("cost",0)) for w in waste if w.get("branch") == branch)
                bc_rows.append({
                    "Branch": branch,
                    "Total Orders": len(b_orders),
                    "Completed": len(b_completed),
                    "Cancelled": b_cancelled,
                    "Failed Deliveries": b_failed,
                    "Revenue (₱)": b_revenue,
                    "Avg Order (₱)": b_avg,
                    "Waste Cost (₱)": b_waste,
                })
            
            # ── DAILY & WEEKLY SALES ────────────────────────────────────────────────
    with tab_daily:
        st.markdown("##### 📅 Daily & Weekly Sales")
        dw1, dw2, dw3 = st.columns(3)
        dw_branch = dw1.selectbox("Branch", ["All"] + (BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH]), key="dw_branch")
        week_start_default = date.today() - timedelta(days=date.today().weekday())
        dw_from = dw2.date_input("From", value=week_start_default, key="dw_from")
        dw_to   = dw3.date_input("To",   value=date.today(),       key="dw_to")

        dw_orders = [o for o in orders
            if dw_from.isoformat() <= str(o.get("target_date",""))[:10] <= dw_to.isoformat()
            and (dw_branch == "All" or o.get("fulfillment_branch", o.get("branch","")) == dw_branch)]

        # Build day-by-day table
        day_range = [(dw_from + timedelta(days=i)) for i in range((dw_to - dw_from).days + 1)]
        daily_rows = []
        for d in day_range:
            ds = d.isoformat()
            day_orders = [o for o in dw_orders if str(o.get("target_date",""))[:10] == ds]
            completed  = [o for o in day_orders if o["status"] in ("Delivered","Picked Up")]
            revenue    = sum(float(o.get("total_price",0)) for o in completed)
            avg_val    = revenue / len(completed) if completed else 0
            daily_rows.append({
                "Date":       ds,
                "Day":        d.strftime("%A"),
                "Total Orders":    len(day_orders),
                "Completed":       len(completed),
                "Revenue (₱)":     revenue,
                "Avg Order (₱)":   avg_val,
            })

        if not daily_rows:
            st.info("No orders found for this period.")
        else:
            df_daily = pd.DataFrame(daily_rows)

            # Comparison to same period previous week
            prev_from = dw_from - timedelta(days=7)
            prev_to   = dw_to   - timedelta(days=7)
            prev_orders = [o for o in orders
                if prev_from.isoformat() <= str(o.get("target_date",""))[:10] <= prev_to.isoformat()
                and (dw_branch == "All" or o.get("fulfillment_branch", o.get("branch","")) == dw_branch)]
            prev_completed = [o for o in prev_orders if o["status"] in ("Delivered","Picked Up")]
            prev_revenue   = sum(float(o.get("total_price",0)) for o in prev_completed)
            curr_revenue   = df_daily["Revenue (₱)"].sum()
            curr_orders    = df_daily["Total Orders"].sum()
            prev_order_cnt = len(prev_orders)

            rev_delta   = ((curr_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else None
            order_delta = ((curr_orders  - prev_order_cnt) / prev_order_cnt * 100) if prev_order_cnt else None

            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric("📦 Total Orders",  int(curr_orders))
            cm2.metric("💰 Total Revenue", f"₱{curr_revenue:,.0f}",
                delta=f"{rev_delta:+.1f}% vs prev week" if rev_delta is not None else "No prev data")
            cm3.metric("🔢 Orders vs Prev", f"{int(curr_orders)}",
                delta=f"{order_delta:+.1f}%" if order_delta is not None else "No prev data")
            cm4.metric("📅 Days in Period", len(day_range))
            st.divider()

            # Bar chart
            fig, ax = plt.subplots(figsize=(10, 4), facecolor="#FDF6F0")
            ax.bar(df_daily["Date"], df_daily["Revenue (₱)"], color="#C85C8E", alpha=0.85)
            ax.set_facecolor("#FDF6F0"); ax.grid(axis="y", alpha=0.3)
            plt.xticks(rotation=30, ha="right", fontsize=9); ax.set_ylabel("Revenue (₱)")
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)
            st.divider()

            st.dataframe(
                df_daily.style.format({"Revenue (₱)": "₱{:,.2f}", "Avg Order (₱)": "₱{:,.2f}"}),
                use_container_width=True, hide_index=True
            )
            st.download_button("⬇️ Export Daily Sales CSV",
                data=df_daily.to_csv(index=False).encode("utf-8"),
                file_name=f"daily_sales_{dw_from}_{dw_to}.csv", mime="text/csv")

    # ── EXPENSES ────────────────────────────────────────────────────────────
    with tab_expenses:
        st.markdown("##### 💸 Expenses")
        exp_tab1, exp_tab2, exp_tab3 = st.tabs(["📊 Summary", "➕ Log Expense", "⚙️ Fixed Cost Settings"])

        all_expenses = db.get_expenses()
        fixed_costs  = db.get_branch_fixed_costs()
        fixed_map    = {f["branch"]: f for f in fixed_costs}

        # ── SUMMARY ─────────────────────────────────────────────────────────
        with exp_tab1:
            es1, es2, es3 = st.columns(3)
            exp_branch = es1.selectbox("Branch", ["All (Company-wide)"] + BRANCHES, key="exp_branch_sum")
            exp_s_from = es2.date_input("From", value=date.today().replace(day=1), key="exp_s_from")
            exp_s_to   = es3.date_input("To",   value=date.today(),               key="exp_s_to")
            num_days   = max(1, (exp_s_to - exp_s_from).days + 1)

            # Revenue for the period
            rev_orders = [o for o in orders
                if exp_s_from.isoformat() <= str(o.get("target_date",""))[:10] <= exp_s_to.isoformat()
                and o["status"] in ("Delivered","Picked Up")
                and (exp_branch == "All (Company-wide)" or
                     o.get("fulfillment_branch", o.get("branch","")) == exp_branch)]
            period_revenue = sum(float(o.get("total_price",0)) for o in rev_orders)

            # Variable expenses for period
            var_exp = [e for e in all_expenses
                if exp_s_from.isoformat() <= e.get("date","") <= exp_s_to.isoformat()
                and (exp_branch == "All (Company-wide)" or e.get("branch") == exp_branch)]
            total_var = sum(float(e.get("amount",0)) for e in var_exp)

            # Fixed costs for period
            if exp_branch == "All (Company-wide)":
                branches_in_scope = BRANCHES
            else:
                branches_in_scope = [exp_branch]

            total_fixed = 0.0
            fixed_breakdown = []
            for br in branches_in_scope:
                fc = fixed_map.get(br, {})
                daily_total = (float(fc.get("daily_salary_budget",0)) +
                               float(fc.get("daily_electricity",0)) +
                               float(fc.get("daily_water",0)) +
                               float(fc.get("daily_other",0)))
                period_fixed = daily_total * num_days
                total_fixed += period_fixed
                fixed_breakdown.append({
                    "Branch": br,
                    "Daily Fixed Total (₱)": daily_total,
                    f"Fixed Cost × {num_days} days (₱)": period_fixed,
                })

            total_expenses = total_fixed + total_var
            net = period_revenue - total_expenses

            st.markdown(f"**Period: {exp_s_from} to {exp_s_to} ({num_days} days)**")
            sc1,sc2,sc3,sc4,sc5 = st.columns(5)
            sc1.metric("💰 Revenue",        f"₱{period_revenue:,.0f}")
            sc2.metric("🏗 Fixed Costs",    f"₱{total_fixed:,.0f}")
            sc3.metric("🧾 Variable Exp",   f"₱{total_var:,.0f}")
            sc4.metric("📊 Total Expenses", f"₱{total_expenses:,.0f}")
            sc5.metric("📈 Net",            f"₱{net:,.0f}", delta=f"{'profit' if net>=0 else 'loss'}")
            st.divider()

            st.markdown("**Fixed Costs Breakdown by Branch**")
            st.dataframe(
                pd.DataFrame(fixed_breakdown).style.format({
                    "Daily Fixed Total (₱)": "₱{:,.2f}",
                    f"Fixed Cost × {num_days} days (₱)": "₱{:,.2f}",
                }),
                use_container_width=True, hide_index=True
            )

            if var_exp:
                st.divider()
                st.markdown("**Variable Expenses by Category**")
                cat_totals = {}
                for e in var_exp:
                    c = e.get("category","Other")
                    cat_totals[c] = cat_totals.get(c, 0) + float(e.get("amount",0))
                st.dataframe(
                    pd.DataFrame(cat_totals.items(), columns=["Category","Amount (₱)"])
                        .sort_values("Amount (₱)", ascending=False)
                        .style.format({"Amount (₱)": "₱{:,.2f}"}),
                    use_container_width=True, hide_index=True
                )

                st.divider()
                st.markdown("**All Variable Expenses — Detail**")
                df_var = pd.DataFrame(var_exp)
                display_exp_cols = [c for c in ["date","branch","category","amount","notes","encoded_by","created_at"]
                                    if c in df_var.columns]
                st.dataframe(df_var[display_exp_cols], use_container_width=True, hide_index=True)
                st.download_button("⬇️ Export Expenses CSV",
                    data=df_var.to_csv(index=False).encode("utf-8"),
                    file_name=f"expenses_{exp_s_from}_{exp_s_to}.csv", mime="text/csv")

        # ── LOG EXPENSE ──────────────────────────────────────────────────────
        with exp_tab2:
            st.markdown("#### ➕ Log an Expense")
            with st.form("log_expense_form", clear_on_submit=True):
                le1, le2 = st.columns(2)
                exp_log_branch = le1.selectbox("Branch *", BRANCHES if (CURRENT_ROLE == "Super Admin" or CURRENT_BRANCH == "All") else [CURRENT_BRANCH])
                exp_log_date   = le2.date_input("Date *", value=date.today())
                le3, le4 = st.columns(2)
                exp_log_cat    = le3.selectbox("Category *", ["Food","Water","Electricity","Supplies","Salary","Operational","Other"])
                exp_log_amt    = le4.number_input("Amount (₱) *", min_value=0.0, step=50.0)
                exp_log_notes  = st.text_input("Notes (optional)")
                if st.form_submit_button("💾 Log Expense", use_container_width=True):
                    if exp_log_amt <= 0:
                        st.error("Amount must be greater than 0.")
                    else:
                        db.save_expense({
                            "id": str(uuid.uuid4())[:8],
                            "branch": exp_log_branch,
                            "date": exp_log_date.isoformat(),
                            "category": exp_log_cat,
                            "amount": exp_log_amt,
                            "notes": exp_log_notes,
                            "encoded_by": CURRENT_USER.get("name",""),
                            "created_at": datetime.now().isoformat(),
                        })
                        st.success("✅ Expense logged.")

        # ── FIXED COST SETTINGS (Super Admin only) ───────────────────────────
        with exp_tab3:
            if CURRENT_ROLE != "Super Admin":
                st.info("🔒 Fixed cost configuration is available to Super Admins only.")
            else:
                st.markdown("#### ⚙️ Fixed Daily Cost Settings per Branch")
                st.caption("These are used to auto-calculate fixed costs for any date range in the Summary tab.")
                for br in BRANCHES:
                    fc = fixed_map.get(br, {})
                    st.markdown(f"**{br}**")
                    with st.form(f"fc_form_{br}", clear_on_submit=False):
                        fc1, fc2, fc3, fc4 = st.columns(4)
                        sal  = fc1.number_input("Daily Salary Budget (₱)",   min_value=0.0, step=100.0, value=float(fc.get("daily_salary_budget",0)),  key=f"fc_sal_{br}")
                        elec = fc2.number_input("Daily Electricity (₱)",     min_value=0.0, step=50.0,  value=float(fc.get("daily_electricity",0)),     key=f"fc_elec_{br}")
                        wat  = fc3.number_input("Daily Water (₱)",           min_value=0.0, step=10.0,  value=float(fc.get("daily_water",0)),           key=f"fc_wat_{br}")
                        oth  = fc4.number_input("Other Daily Fixed Costs (₱)",min_value=0.0, step=50.0, value=float(fc.get("daily_other",0)),           key=f"fc_oth_{br}")
                        if st.form_submit_button(f"💾 Save {br} Fixed Costs"):
                            db.upsert_branch_fixed_cost({
                                "id":     fc.get("id", f"bfc-{br[:2].lower()}"),
                                "branch": br,
                                "daily_salary_budget": sal,
                                "daily_electricity":   elec,
                                "daily_water":         wat,
                                "daily_other":         oth,
                                "updated_at":  datetime.now().isoformat(),
                                "updated_by":  CURRENT_USER.get("name",""),
                            })
                            st.success(f"✅ Fixed costs saved for {br}.")
                    st.divider()

    # ── BRANCH COMPARISON (dynamic, Super Admin only) ────────────────────────
    if show_branch_compare:
        with st.expander("🏪 Branch Comparison — Super Admin", expanded=False):
            st.markdown("##### 🏪 Branch Comparison")
            bc_rows = []
            for branch in BRANCHES:
                b_orders    = [o for o in orders if o.get("fulfillment_branch", o.get("branch","")) == branch]
                b_completed = [o for o in b_orders if o["status"] in ("Delivered","Picked Up")]
                b_revenue   = sum(float(o.get("total_price",0)) for o in b_completed)
                b_avg       = (b_revenue / len(b_completed)) if b_completed else 0
                b_cancelled = len([o for o in b_orders if o["status"] == "Cancelled"])
                b_failed    = len([o for o in b_orders if o["status"] == "Failed Delivery"])
                b_waste     = sum(float(w.get("cost",0)) for w in waste if w.get("branch") == branch)
                bc_rows.append({"Branch": branch,"Total Orders": len(b_orders),
                    "Completed": len(b_completed),"Cancelled": b_cancelled,
                    "Failed Deliveries": b_failed,"Revenue (₱)": b_revenue,
                    "Avg Order (₱)": b_avg,"Waste Cost (₱)": b_waste})
            df_bc = pd.DataFrame(bc_rows)
            st.dataframe(df_bc.style.format({"Revenue (₱)":"₱{:,.2f}","Avg Order (₱)":"₱{:,.2f}","Waste Cost (₱)":"₱{:,.2f}"}),
                use_container_width=True, hide_index=True)
            fc1,fc2 = st.columns(2)
            with fc1:
                fig,ax = plt.subplots(figsize=(6,4), facecolor="#FDF6F0")
                ax.bar(df_bc["Branch"], df_bc["Revenue (₱)"], color="#C85C8E", alpha=0.85)
                ax.set_facecolor("#FDF6F0"); ax.grid(axis="y",alpha=0.3)
                plt.xticks(rotation=15, ha="right", fontsize=9); plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            with fc2:
                fig,ax = plt.subplots(figsize=(6,4), facecolor="#FDF6F0")
                ax.bar(df_bc["Branch"], df_bc["Total Orders"], color="#17A2B8", alpha=0.85)
                ax.set_facecolor("#FDF6F0"); ax.grid(axis="y",alpha=0.3)
                plt.xticks(rotation=15, ha="right", fontsize=9); plt.tight_layout()
                st.pyplot(fig); plt.close(fig)
            st.download_button("⬇️ Export Branch Comparison CSV",
                data=df_bc.to_csv(index=False).encode("utf-8"),
                file_name=f"branch_comparison_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HR MODULE
# ─────────────────────────────────────────────────────────────────────────────
def page_hr():
    if CURRENT_ROLE != "Super Admin":
        st.error("🔒 Access denied. This section is for Super Admins only.")
        return

    st.markdown("<div class='section-header'>👔 HR Module — Super Admin</div>", unsafe_allow_html=True)
    florists = db.get_florists(); riders = db.get_riders()
    all_staff = [{"name":f["name"],"role":"Florist","branch":f.get("branch","")} for f in florists] + [{"name":r["name"],"role":"Rider","branch":r.get("branch","")} for r in riders]
    hr_logs = db.get_hr_logs()
    tab1,tab2 = st.tabs(["📋 Hours & Pay Log","➕ Log Hours"])

    with tab1:
        if not hr_logs: st.info("No HR entries logged yet.")
        else:
            df = pd.DataFrame(hr_logs)
            st.dataframe(df, use_container_width=True)
            if "employee" in df.columns and "total_pay" in df.columns:
                st.markdown("**Pay Summary by Employee**")
                summary = df.groupby("employee")["total_pay"].sum().reset_index()
                summary.columns = ["Employee","Total Pay (₱)"]
                st.dataframe(summary.style.format({"Total Pay (₱)":"₱{:,.2f}"}), use_container_width=True)
            st.download_button("⬇️ Export HR Log CSV", data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"hr_log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    with tab2:
        with st.form("hr_log_form"):
            staff_names = [s["name"] for s in all_staff]
            c1,c2 = st.columns(2)
            emp_name  = (c1.selectbox("Employee *", staff_names) if staff_names else c1.text_input("Employee Name *"))
            work_date = c2.date_input("Work Date *", value=date.today())
            c1,c2,c3 = st.columns(3)
            reg_hours   = c1.number_input("Regular Hours",  min_value=0.0, max_value=24.0, step=0.5, value=8.0)
            ot_hours    = c2.number_input("Overtime Hours", min_value=0.0, max_value=12.0, step=0.5, value=0.0)
            hourly_rate = c3.number_input("Hourly Rate (₱)",min_value=0.0, step=10.0, value=60.0)
            ot_mult     = st.number_input("OT Rate Multiplier", min_value=1.0, max_value=3.0, step=0.25, value=1.25)
            notes_hr    = st.text_input("Notes")
            if st.form_submit_button("💾 Log Entry", use_container_width=True):
                reg_pay   = reg_hours * hourly_rate
                ot_pay    = ot_hours  * hourly_rate * ot_mult
                total_pay = reg_pay + ot_pay
                db.save_hr_log({"id":str(uuid.uuid4())[:8],"employee":emp_name,"date":work_date.isoformat(),"regular_hours":reg_hours,"overtime_hours":ot_hours,"hourly_rate":hourly_rate,"ot_multiplier":ot_mult,"regular_pay":round(reg_pay,2),"overtime_pay":round(ot_pay,2),"total_pay":round(total_pay,2),"notes":notes_hr,"logged_at":datetime.now().isoformat()})
                st.success(f"✅ Logged ₱{total_pay:,.2f} for {emp_name} on {work_date}.")


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.active_page
if   page == "Dashboard":        page_dashboard()
elif page == "New Order":        page_new_order()
elif page == "All Orders":       page_all_orders()
elif page == "Edit Order":       page_edit_order()
elif page == "Florist Board":    page_florist_board()
elif page == "Rider Board":      page_rider_board()
elif page == "Schedule":         page_schedule()
elif page == "Customers":        page_customers()
elif page == "Inventory":        page_inventory()
elif page == "Waste Tracker":    page_waste_tracker()
elif page == "Staff Management": page_staff_management()
elif page == "Reports":          page_reports()
elif page == "HR":               page_hr()

st.divider()
st.markdown("<div style='text-align:center; color:#C9A0B0; font-size:11px;'>🌸 Angie's Florist System v3.0 · Supabase Edition</div>", unsafe_allow_html=True)
