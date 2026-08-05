"""
cash_count.py
Angie's Florist — End-of-Day Cash Count
Covers all payment channels: GCash, Maya, Cash, COD, Bank Transfer, walk-ins.
Saves a digital record per day per branch to Supabase.
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
import db

from datetime import timezone, timedelta
PHT = timezone(timedelta(hours=8))

def now_pht() -> str:
    """Returns current Philippine Time as ISO string."""
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


PAYMENT_CHANNELS = [
    "GCash",
    "Maya",
    "Cash",
    "COD",
    "BDO Transfer",
    "BPI Transfer",
    "Other Bank Transfer",
    "Other",
]


def _get_cash_count_sessions() -> list:
    try:
        return db._select("cash_count_sessions")
    except Exception:
        return []


def _save_cash_count_session(session: dict) -> dict:
    try:
        result = db._insert("cash_count_sessions", session)
        return result
    except Exception as e:
        st.error(f"⚠️ Failed to save: {e}")
        return {}


def _delete_cash_count_session(session_id: str):
    try:
        db._delete("cash_count_sessions", session_id)
    except Exception:
        pass


def page_cash_count(CURRENT_USER, CURRENT_ROLE, CURRENT_BRANCH, BRANCHES, scope_by_branch):
    st.markdown("<div class='section-header'>💵 End-of-Day Cash Count</div>", unsafe_allow_html=True)

    tab_count, tab_history = st.tabs(["📋 Daily Count", "🗂️ History"])

    # ── TAB 1: DAILY COUNT ────────────────────────────────────────────────────
    with tab_count:

        # ── Filters ───────────────────────────────────────────────────────────
        f1, f2 = st.columns(2)
        count_date   = f1.date_input("📅 Date", value=date.today(), key="cc_date")
        branch_opts  = BRANCHES if CURRENT_ROLE in ("Super Admin", "Branch Manager") else [CURRENT_BRANCH]
        count_branch = f2.selectbox("🏢 Branch", branch_opts, key="cc_branch")
        count_date_str = count_date.isoformat()

        # ── Check if already submitted ────────────────────────────────────────
        sessions     = _get_cash_count_sessions()
        existing     = next((s for s in sessions
                             if s.get("date") == count_date_str
                             and s.get("branch") == count_branch), None)

        if existing:
            st.success(f"✅ Cash count for **{count_branch}** on **{count_date_str}** already submitted by **{existing.get('submitted_by','—')}** at **{str(existing.get('submitted_at',''))[:16]}**.")
            breakdown = existing.get("breakdown") or {}
            st.markdown("##### Submitted Breakdown")
            rows = []
            for ch, vals in breakdown.items():
                rows.append({
                    "Channel":       ch,
                    "Order Revenue": f"₱{float(vals.get('order_revenue',0)):,.2f}",
                    "Walk-in Cash":  f"₱{float(vals.get('walk_in',0)):,.2f}",
                    "Total":         f"₱{float(vals.get('total',0)):,.2f}",
                    "Order Count":   vals.get("order_count", 0),
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Order Revenue",  f"₱{float(existing.get('order_total',0)):,.2f}")
            c2.metric("Walk-in Cash",   f"₱{float(existing.get('walk_in_total',0)):,.2f}")
            c3.metric("Grand Total",    f"₱{float(existing.get('grand_total',0)):,.2f}")
            if existing.get("notes"):
                st.info(f"📝 Notes: {existing['notes']}")

            if CURRENT_ROLE in ("Super Admin",):
                if st.button("🗑️ Delete & Redo", key="cc_delete"):
                    _delete_cash_count_session(existing["id"])
                    st.success("Deleted. Reload to redo.")
                    st.rerun()
            return

        # ── Pull orders for the day ───────────────────────────────────────────
        all_orders   = db.get_orders()
        COMPLETED    = {"Delivered", "Picked Up"}

        day_orders = [
            o for o in all_orders
            if str(o.get("target_date",""))[:10] == count_date_str
            and (o.get("fulfillment_branch", o.get("branch","")) == count_branch
                 or o.get("branch") == count_branch)
            and o.get("status") not in {"Cancelled"}
        ]

        completed_orders = [o for o in day_orders if o.get("status") in COMPLETED]
        pending_orders   = [o for o in day_orders if o.get("status") not in COMPLETED]

        # ── Summary metrics ───────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        m1.metric("📦 Total Orders Today", len(day_orders))
        m2.metric("✅ Completed",           len(completed_orders))
        m3.metric("⏳ Still Pending",       len(pending_orders),
                  delta=f"{len(pending_orders)} not yet done" if pending_orders else None,
                  delta_color="inverse" if pending_orders else "normal")

        if pending_orders:
            st.warning(f"⚠️ **{len(pending_orders)} order(s) not yet completed.** Cash count below includes completed orders only.")

        st.divider()

        # ── Build channel breakdown from orders ───────────────────────────────
        channel_data = {ch: {"order_count": 0, "order_revenue": 0.0, "walk_in": 0.0} for ch in PAYMENT_CHANNELS}

        for o in completed_orders:
            total   = float(o.get("total_price", 0) or 0)
            balance = float(o.get("total_balance", 0) or 0)
            down    = float(o.get("down_payment_amount", 0) or 0)
            split   = float(o.get("split_payment_amount", 0) or 0)
            split_method = o.get("split_payment_method", "")
            bal_method   = o.get("balance_payment_method", "") or ""

            # Down payment channel
            # We don't store the down payment channel separately — use balance method as proxy
            # Primary: balance payment method gets the full total
            primary_ch = bal_method if bal_method in PAYMENT_CHANNELS else "Other"

            # If fully paid (balance = 0), revenue goes to the primary channel
            if balance == 0:
                ch = primary_ch if primary_ch != "N/A" else "GCash"
                if ch not in channel_data: ch = "Other"
                channel_data[ch]["order_count"]   += 1
                channel_data[ch]["order_revenue"] += total

            else:
                # Balance still pending — count what's been collected
                collected = total - balance
                ch = primary_ch if primary_ch in channel_data else "Other"
                channel_data[ch]["order_count"]   += 1
                channel_data[ch]["order_revenue"] += collected

                # Balance method
                if bal_method in channel_data:
                    channel_data[bal_method]["order_revenue"] += balance

            # Split payment
            if split > 0 and split_method in channel_data:
                channel_data[split_method]["order_revenue"] += split

        # ── Walk-in cash entry ────────────────────────────────────────────────
        st.markdown("### 📊 Channel Breakdown")
        st.caption("Order revenue is auto-calculated. Add walk-in cash for each channel below.")

        walk_in_inputs = {}
        rows_display   = []

        for ch in PAYMENT_CHANNELS:
            data        = channel_data[ch]
            order_rev   = data["order_revenue"]
            order_count = data["order_count"]

            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            col1.markdown(f"**{ch}**" + (f"\n\n_{order_count} order(s)_" if order_count > 0 else ""))
            col2.markdown(f"₱{order_rev:,.2f}" if order_rev > 0 else "—")
            walk_in = col3.number_input(
                f"Walk-in ({ch})",
                min_value=0.0, step=50.0, value=0.0,
                key=f"cc_walkin_{ch}",
                label_visibility="collapsed",
            )
            walk_in_inputs[ch] = walk_in
            total_ch = order_rev + walk_in
            col4.markdown(f"**₱{total_ch:,.2f}**" if total_ch > 0 else "—")

            if order_rev > 0 or walk_in > 0:
                rows_display.append({
                    "Channel":       ch,
                    "Order Revenue": order_rev,
                    "Walk-in":       walk_in,
                    "Total":         total_ch,
                    "Orders":        order_count,
                })

        st.divider()

        # ── Totals ────────────────────────────────────────────────────────────
        total_order_rev  = sum(channel_data[ch]["order_revenue"] for ch in PAYMENT_CHANNELS)
        total_walk_in    = sum(walk_in_inputs[ch] for ch in PAYMENT_CHANNELS)
        grand_total      = total_order_rev + total_walk_in

        t1, t2, t3 = st.columns(3)
        t1.metric("💳 Order Revenue",  f"₱{total_order_rev:,.2f}")
        t2.metric("🚶 Walk-in Cash",   f"₱{total_walk_in:,.2f}")
        t3.metric("💰 Grand Total",    f"₱{grand_total:,.2f}")

        st.divider()

        # ── Notes + Submit ────────────────────────────────────────────────────
        notes = st.text_area("📝 Notes (optional)", placeholder="e.g. Short ₱200 — rider Kuya Mark pending, 1 failed delivery refund pending", key="cc_notes")

        if st.button("✅ Submit Cash Count", use_container_width=True, key="cc_submit"):
            breakdown = {}
            for ch in PAYMENT_CHANNELS:
                rev  = channel_data[ch]["order_revenue"]
                wi   = walk_in_inputs[ch]
                cnt  = channel_data[ch]["order_count"]
                if rev > 0 or wi > 0:
                    breakdown[ch] = {
                        "order_revenue": rev,
                        "walk_in":       wi,
                        "total":         rev + wi,
                        "order_count":   cnt,
                    }

            session = {
                "id":            str(uuid.uuid4())[:8],
                "date":          count_date_str,
                "branch":        count_branch,
                "submitted_by":  CURRENT_USER.get("name", ""),
                "submitted_at":  now_pht(),
                "order_total":   round(total_order_rev, 2),
                "walk_in_total": round(total_walk_in, 2),
                "grand_total":   round(grand_total, 2),
                "breakdown":     breakdown,
                "notes":         notes,
                "created_at":    now_pht(),
            }
            _save_cash_count_session(session)
            st.success(f"✅ Cash count submitted for **{count_branch}** · **{count_date_str}** · Total: **₱{grand_total:,.2f}**")
            st.rerun()

        # ── CSV Export ────────────────────────────────────────────────────────
        if rows_display:
            st.divider()
            df = pd.DataFrame(rows_display)
            df["Order Revenue"] = df["Order Revenue"].map(lambda x: f"₱{x:,.2f}")
            df["Walk-in"]       = df["Walk-in"].map(lambda x: f"₱{x:,.2f}")
            df["Total"]         = df["Total"].map(lambda x: f"₱{x:,.2f}")
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export as CSV",
                data=csv,
                file_name=f"cash_count_{count_branch.replace(' ','_')}_{count_date_str}.csv",
                mime="text/csv",
                key="cc_export",
            )

    # ── TAB 2: HISTORY ────────────────────────────────────────────────────────
    with tab_history:
        sessions = _get_cash_count_sessions()
        if not sessions:
            st.info("No cash count records yet.")
            return

        sessions = sorted(sessions, key=lambda x: (x.get("date",""), x.get("branch","")), reverse=True)

        # Filters
        h1, h2 = st.columns(2)
        hist_branch = h1.selectbox("Branch", ["All"] + BRANCHES, key="cc_hist_branch")
        hist_month  = h2.selectbox("Month", ["All"] + [
            f"{y}-{str(m).zfill(2)}"
            for y in [2026, 2027]
            for m in range(1, 13)
        ], key="cc_hist_month")

        filtered = sessions
        if hist_branch != "All":
            filtered = [s for s in filtered if s.get("branch") == hist_branch]
        if hist_month != "All":
            filtered = [s for s in filtered if str(s.get("date","")).startswith(hist_month)]

        if not filtered:
            st.info("No records match the filter.")
            return

        # Summary table
        rows = []
        for s in filtered:
            rows.append({
                "Date":          str(s.get("date",""))[:10],
                "Branch":        s.get("branch",""),
                "Order Revenue": f"₱{float(s.get('order_total',0)):,.2f}",
                "Walk-in":       f"₱{float(s.get('walk_in_total',0)):,.2f}",
                "Grand Total":   f"₱{float(s.get('grand_total',0)):,.2f}",
                "Submitted By":  s.get("submitted_by",""),
                "Time":          str(s.get("submitted_at",""))[:16],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Period total
        period_total = sum(float(s.get("grand_total",0)) for s in filtered)
        st.metric("Period Total", f"₱{period_total:,.2f}")

        # Export history
        st.divider()
        df_hist = pd.DataFrame(rows)
        csv_hist = df_hist.to_csv(index=False)
        label = f"{hist_month if hist_month != 'All' else 'all'}_{hist_branch.replace(' ','_') if hist_branch != 'All' else 'all_branches'}"
        st.download_button(
            "📥 Export History CSV",
            data=csv_hist,
            file_name=f"cash_count_history_{label}.csv",
            mime="text/csv",
            key="cc_hist_export",
        )
