"""
peak_features.py
Valentine's Day Peak Season Management for Angie's Florist
- Slot configuration (hourly or custom ranges)
- Capacity warnings on new orders
- V-Day mode toggle
- Slot availability widget
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date, time, timedelta
import db

from datetime import timezone, timedelta
PHT = timezone(timedelta(hours=8))

def now_pht() -> str:
    """Returns current Philippine Time as ISO string."""
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=8))).isoformat()

# ── V-DAY MODE ────────────────────────────────────────────────────────────────

VDAY_DATE = date(2027, 2, 14)

def is_vday_mode_on() -> bool:
    val = db.get_system_flag("vday_mode")
    return val == "on"

def get_vday_cutoff() -> date:
    val = db.get_system_flag("vday_cutoff")
    if val:
        try:
            return date.fromisoformat(val)
        except Exception:
            pass
    return date(2027, 2, 12)

def get_vday_max_per_slot() -> int:
    val = db.get_system_flag("vday_max_per_slot")
    if val:
        try:
            return int(val)
        except Exception:
            pass
    return 10

# ── SLOT AVAILABILITY WIDGET ──────────────────────────────────────────────────

def render_slot_availability(target_date: date, target_time_str: str,
                              branch: str = "All"):
    if not target_date or not target_time_str:
        return

    date_str = target_date.isoformat()
    configs  = db.get_slot_configs()

    # Find matching slot config for this date/branch
    matching = [
        c for c in configs
        if str(c.get("date",""))[:10] == date_str
        and (c.get("branch","All") in ("All", branch))
    ]

    if not matching:
        # No config for this date — show generic usage count
        usage = db.get_slot_usage(date_str, target_time_str, branch)
        if usage > 0:
            st.caption(f"📊 {usage} order(s) already in this time slot.")
        return

    max_cap = get_vday_max_per_slot()
    usage   = db.get_slot_usage(date_str, target_time_str, branch)
    pct     = usage / max_cap if max_cap > 0 else 0

    if pct == 0:
        color = "#2D7A4F"
        icon  = "🟢"
        msg   = f"Slot available — {usage}/{max_cap} orders"
    elif pct < 0.8:
        color = "#2D7A4F"
        icon  = "🟢"
        msg   = f"Slot available — {usage}/{max_cap} orders"
    elif pct < 1.0:
        color = "#D97706"
        icon  = "🟡"
        msg   = f"Slot almost full — {usage}/{max_cap} orders (filling up)"
    else:
        color = "#DC2626"
        icon  = "🔴"
        msg   = f"Slot FULL — {usage}/{max_cap} orders. You can still book but check with manager."

    st.markdown(
        f"<div style='background:{'#EAFAF1' if pct < 0.8 else '#FEF9E7' if pct < 1.0 else '#FDEDEC'}; "
        f"border-left: 4px solid {color}; border-radius:8px; "
        f"padding:8px 14px; margin:4px 0;'>"
        f"{icon} <strong>{msg}</strong>"
        f"<div style='background:#E8E3DC; border-radius:4px; height:6px; margin-top:6px;'>"
        f"<div style='background:{color}; width:{min(pct*100,100):.0f}%; "
        f"height:6px; border-radius:4px;'></div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ── V-DAY DASHBOARD BANNER ────────────────────────────────────────────────────

def render_vday_banner():
    if not is_vday_mode_on():
        return

    today    = date.today()
    cutoff   = get_vday_cutoff()
    days_to  = (VDAY_DATE - today).days
    past_cutoff = today > cutoff

    if days_to < 0:
        return  # V-Day passed

    # Count today's orders for V-Day date
    orders   = db.get_orders()
    vday_str = VDAY_DATE.isoformat()
    vday_orders = [o for o in orders
                   if str(o.get("target_date",""))[:10] == vday_str
                   and o.get("status") not in ("Cancelled",)]

    max_per_slot = get_vday_max_per_slot()

    color   = "#DC2626" if days_to <= 3 else "#D97706" if days_to <= 7 else "#C85C8E"
    bg      = "#FDEDEC" if days_to <= 3 else "#FEF9E7" if days_to <= 7 else "#FCEEF5"

    cutoff_label = "⛔ Past cutoff — no new V-Day orders" if past_cutoff else f"📅 Cutoff: {cutoff.strftime('%b %d, %Y')}"

    st.markdown(
        f"<div style='background:{bg}; border:2px solid {color}; "
        f"border-radius:12px; padding:14px 20px; margin-bottom:16px;'>"
        f"<div style='display:flex; align-items:center; gap:12px; flex-wrap:wrap;'>"
        f"<span style='font-size:1.8rem;'>🌹</span>"
        f"<div>"
        f"<div style='font-weight:700; font-size:1rem; color:{color};'>"
        f"Valentine's Day Mode — {days_to} day{'s' if days_to!=1 else ''} to go</div>"
        f"<div style='font-size:0.82rem; color:#555;'>"
        f"{cutoff_label}"
        f" &nbsp;·&nbsp; 📦 {len(vday_orders)} V-Day orders booked"
        f" &nbsp;·&nbsp; 🎯 Slot cap: {max_per_slot}/slot"
        f"</div></div></div></div>",
        unsafe_allow_html=True,
    )

# ── CUTOFF WARNING ────────────────────────────────────────────────────────────

def check_vday_cutoff_warning(target_date: date) -> str:
    if not is_vday_mode_on():
        return ""
    cutoff = get_vday_cutoff()
    if target_date == VDAY_DATE and date.today() > cutoff:
        return (f"⛔ Valentine's Day orders are past the cutoff date "
                f"({cutoff.strftime('%B %d')}). "
                f"Consult the manager before accepting.")
    return ""

# ── PAGE: V-DAY SETTINGS (Super Admin only) ───────────────────────────────────

def page_vday_settings():
    st.markdown(
        "<div class='section-header'>🌹 Valentine's Day Peak Settings</div>",
        unsafe_allow_html=True,
    )

    is_on    = is_vday_mode_on()
    cutoff   = get_vday_cutoff()
    max_slot = get_vday_max_per_slot()

    # ── V-Day toggle ──────────────────────────────────────────────────────────
    st.markdown("### 🔴 V-Day Mode")
    col_on, col_status = st.columns([1, 3])
    new_on = col_on.toggle("Enable V-Day Mode", value=is_on, key="vday_toggle")
    if new_on != is_on:
        db.set_system_flag("vday_mode", "on" if new_on else "off")
        st.success("✅ V-Day mode " + ("activated" if new_on else "deactivated"))
        st.rerun()
    col_status.markdown(
        f"**Status:** {'🔴 ACTIVE — V-Day mode is ON' if is_on else '⚫ Inactive'}"
    )

    st.divider()

    # ── Global settings ───────────────────────────────────────────────────────
    st.markdown("### ⚙️ Global Settings")
    g1, g2 = st.columns(2)

    new_cutoff = g1.date_input(
        "Order Cutoff Date",
        value=cutoff,
        help="No new Valentine's Day orders accepted after this date.",
        key="vday_cutoff_input",
    )
    new_max = g2.number_input(
        "Max Orders Per Slot",
        min_value=1, max_value=100,
        value=max_slot,
        step=1,
        help="Maximum orders per time slot across all branches.",
        key="vday_max_input",
    )
    if st.button("💾 Save Global Settings", key="vday_save_global"):
        db.set_system_flag("vday_cutoff",       new_cutoff.isoformat())
        db.set_system_flag("vday_max_per_slot", str(new_max))
        st.success("✅ Settings saved.")
        st.rerun()

    st.divider()

    # ── Slot configuration ────────────────────────────────────────────────────
    st.markdown("### 📅 Slot Configuration")
    st.caption(
        "Define delivery time slots for specific dates. "
        "Leave empty to use global slot cap without time restrictions."
    )

    tab_add, tab_view = st.tabs(["➕ Add Slots", "📋 View Slots"])

    with tab_add:
        st.markdown("**Quick add: Hourly slots**")
        qa1, qa2, qa3 = st.columns(3)
        qa_date    = qa1.date_input("Date", value=date(2027, 2, 14), key="qa_date")
        qa_start   = qa2.time_input("Start Time", value=time(7, 0), key="qa_start")
        qa_end     = qa3.time_input("End Time",   value=time(18, 0), key="qa_end")
        qa_branch  = st.selectbox(
            "Branch", ["All", "Main Branch", "San Pablo Branch", "Sta. Rosa Branch"],
            key="qa_branch"
        )
        qa_cap     = st.number_input(
            "Capacity per slot", min_value=1, value=max_slot, key="qa_cap"
        )
        slot_type  = st.radio(
            "Slot type", ["Hourly (1-hour intervals)", "Custom ranges"],
            horizontal=True, key="qa_type"
        )

        if slot_type == "Custom ranges":
            st.caption("Enter custom slot labels, one per line: e.g. '9:00 AM - 11:00 AM'")
            custom_slots_raw = st.text_area(
                "Custom Slots",
                placeholder="9:00 AM - 11:00 AM\n11:00 AM - 1:00 PM\n1:00 PM - 3:00 PM",
                key="qa_custom",
                height=120,
            )

        if st.button("➕ Generate & Save Slots", key="qa_generate", use_container_width=True):
            slots_to_save = []

            if slot_type == "Hourly (1-hour intervals)":
                # Generate hourly slots from start to end
                current = datetime.combine(qa_date, qa_start)
                end_dt  = datetime.combine(qa_date, qa_end)
                while current < end_dt:
                    slot_end = current + timedelta(hours=1)
                    label = current.strftime("%I:%M %p")
                    slots_to_save.append({
                        "id":           str(uuid.uuid4())[:8],
                        "branch":       qa_branch,
                        "date":         qa_date.isoformat(),
                        "slot_label":   label,
                        "slot_start":   current.strftime("%H:%M"),
                        "slot_end":     slot_end.strftime("%H:%M"),
                        "max_capacity": qa_cap,
                        "created_by":   st.session_state.get("auth_user", {}).get("name",""),
                        "created_at":   now_pht(),
                    })
                    current = slot_end
            else:
                # Custom ranges
                for line in (custom_slots_raw or "").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    slots_to_save.append({
                        "id":           str(uuid.uuid4())[:8],
                        "branch":       qa_branch,
                        "date":         qa_date.isoformat(),
                        "slot_label":   line,
                        "slot_start":   "00:00",
                        "slot_end":     "23:59",
                        "max_capacity": qa_cap,
                        "created_by":   st.session_state.get("auth_user", {}).get("name",""),
                        "created_at":   now_pht(),
                    })

            for s in slots_to_save:
                db.save_slot_config(s)

            st.success(f"✅ {len(slots_to_save)} slot(s) saved for {qa_date}.")
            st.rerun()

    with tab_view:
        configs = db.get_slot_configs()
        if not configs:
            st.info("No slots configured yet.")
        else:
            # Group by date
            dates = sorted(set(str(c.get("date",""))[:10] for c in configs), reverse=True)
            sel_date = st.selectbox("Filter by date", ["All"] + dates, key="vday_view_date")

            filtered = configs if sel_date == "All" else [
                c for c in configs if str(c.get("date",""))[:10] == sel_date
            ]

            rows = []
            for c in sorted(filtered, key=lambda x: (x.get("date",""), x.get("slot_start",""))):
                date_str  = str(c.get("date",""))[:10]
                usage     = db.get_slot_usage(date_str, c.get("slot_label",""), c.get("branch","All"))
                cap       = c.get("max_capacity", max_slot)
                rows.append({
                    "Date":     date_str,
                    "Slot":     c.get("slot_label",""),
                    "Branch":   c.get("branch","All"),
                    "Booked":   f"{usage}/{cap}",
                    "Status":   "🔴 FULL" if usage >= cap else "🟡 ALMOST" if usage >= cap*0.8 else "🟢 OK",
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if st.button("🗑️ Delete All Slots for Selected Date",
                        key="vday_del_slots",
                        disabled=(sel_date == "All")):
                to_del = [c for c in configs if str(c.get("date",""))[:10] == sel_date]
                for c in to_del:
                    db.delete_slot_config(c["id"])
                st.success(f"✅ Deleted {len(to_del)} slot(s) for {sel_date}.")
                st.rerun()
