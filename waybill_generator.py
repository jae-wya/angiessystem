"""
waybill_generator.py
Angie's Florist — Waybill Generator (A5, single page)
-------------------------------------------------------
Layout:
  TOP (Florist): inspo photo, arrangement, flowers, card, notes, occasion
  BOTTOM STRIP (Rider): recipient, address, contact, zone, COD, add-ons, QR
"""

import qrcode
from io import BytesIO
import base64
import secrets
from datetime import datetime

RIDER_PAGE_BASE_URL = "https://yvbfggxavlaaohzupnqf.supabase.co/functions/v1/rider-delivery"

BRANCH_NAMES = {
    "main":      "Main Branch",
    "san_pablo": "San Pablo Branch",
    "sta_rosa":  "Sta. Rosa Branch",
}


def generate_order_token() -> str:
    return secrets.token_urlsafe(6)


def generate_qr_base64(order_code: str, token: str) -> str:
    url = f"{RIDER_PAGE_BASE_URL}?order={order_code}&token={token}"
    qr  = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a1a", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _fmt(amount) -> str:
    try:
        return f"₱{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₱0.00"


def _fmt_phone(phone: str) -> str:
    p = str(phone).replace(" ", "")
    if len(p) == 11:
        return f"{p[:4]} {p[4:7]} {p[7:]}"
    return p


def _extract_addons(notes: str) -> str:
    """Pull freebie/add-on lines from the order details notes block."""
    if not notes:
        return ""
    addons = []
    for line in notes.splitlines():
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        # Skip the arrangement/price line and total line
        import re
        if re.match(r'^[₱P]?[\d,]+\s*[-–]', line):
            continue
        if lower.startswith("total"):
            continue
        addons.append(line)
    return " · ".join(addons) if addons else ""


def generate_waybill_html(order: dict, token: str = None) -> str:
    if not token:
        token = generate_order_token()

    import re

    qr_b64       = generate_qr_base64(order.get("order_code", "PREVIEW"), token)
    branch_label = BRANCH_NAMES.get(order.get("branch", ""), order.get("branch", "Main Branch"))
    is_rush      = str(order.get("order_type", "")).lower() == "rush"
    is_surprise  = bool(order.get("is_surprise", False))
    has_cod      = str(order.get("payment_method", "")).upper() == "COD"
    print_time   = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    rush_badge   = '<span class="rush">RUSH</span>' if is_rush else ""

    # ── Inspo photos ──────────────────────────────────────────
    inspo_urls = order.get("inspo_photo_urls", [])
    if not inspo_urls and order.get("inspo_photo_url"):
        inspo_urls = [order["inspo_photo_url"]]

    if inspo_urls:
        # Side by side if multiple, single full-width if one
        if len(inspo_urls) == 1:
            imgs_html = f'<img src="{inspo_urls[0]}" class="inspo-img" alt="Inspo">'
        else:
            cols = "".join(
                f'<img src="{u}" class="inspo-img inspo-multi" alt="Inspo {i+1}">'
                for i, u in enumerate(inspo_urls)
            )
            imgs_html = f'<div class="inspo-row">{cols}</div>'
        inspo_section = f'<div class="inspo-wrap">{imgs_html}</div>'
    else:
        inspo_section = '<div class="inspo-empty">No inspo photo uploaded</div>'

    # ── Flower breakdown ──────────────────────────────────────
    flowers = order.get("flowers", [])
    if flowers:
        items = ""
        for f in flowers:
            name  = f.get("name", "")
            color = f.get("color", "")
            qty   = f.get("qty", 1)
            items += f'<li><span class="dot">·</span> <b>×{qty}</b> {name}' + (f' <span class="clr">({color})</span>' if color else '') + '</li>'
        flowers_html = f'<ul class="flist">{items}</ul>'
    else:
        flowers_html = '<span class="muted">See arrangement</span>'

    # ── Card message ──────────────────────────────────────────
    card_to   = order.get("card_to", "")
    card_msg  = order.get("card_message", "")
    card_from = order.get("card_from", "")
    if card_to or card_msg or card_from:
        card_html = f'''<div class="card-msg">
          {"<div class='card-line'><span class='cl'>To:</span> <b>" + card_to + "</b></div>" if card_to else ""}
          {"<div class='card-body'>\"" + card_msg + "\"</div>" if card_msg else ""}
          {"<div class='card-line'><span class='cl'>From:</span> <b>" + card_from + "</b></div>" if card_from else ""}
        </div>'''
    else:
        card_html = '<span class="muted">No card message</span>'

    # ── Order details / notes ─────────────────────────────────
    notes = order.get("special_instructions", "")
    notes_html = ""
    if notes:
        lines_html = "".join(f"<div>{l}</div>" for l in notes.splitlines() if l.strip())
        notes_html = f'<div class="notes-block">{lines_html}</div>'

    # ── Add-ons for rider strip ───────────────────────────────
    addons = _extract_addons(notes)

    # ── Payment / COD ─────────────────────────────────────────
    total_price  = order.get("total_price", 0)
    total_bal    = order.get("total_balance", 0)
    down_pay     = order.get("down_payment", 0)
    split_pay    = order.get("split_payment", 0)

    if has_cod:
        cod_html = f'<span class="badge-cod">COD ₱{float(total_bal):,.0f} to collect</span>'
    else:
        cod_html = f'<span class="badge-paid">Paid — No COD</span>'

    # ── Substitution ──────────────────────────────────────────
    if order.get("allow_substitution"):
        sub_html = '<span class="badge-sub-ok">Substitution OK</span>'
    else:
        sub_html = '<span class="badge-sub-no">No Substitution</span>'

    # ── Occasion / source ─────────────────────────────────────
    occasion = order.get("occasion", "")
    source   = order.get("source_page", "")
    occ_html = ""
    if occasion or source:
        occ_html = f'<div class="f-row"><span class="fl">Occasion:</span> {occasion or "—"} &nbsp;|&nbsp; <span class="fl">Source:</span> {source or "—"}</div>'

    # ── Surprise ──────────────────────────────────────────────
    sender_disp = "🎁 Surprise — Hidden" if is_surprise else (order.get("sender_name","") or "—")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Waybill — {order.get('order_code','')}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap');

  *{{margin:0;padding:0;box-sizing:border-box;}}

  /* ── Screen view ── */
  body{{
    background:#e8e4df;
    font-family:'Inter',sans-serif;
    display:flex;
    flex-direction:column;
    align-items:center;
    padding:24px 16px;
    gap:16px;
  }}
  .hint{{font-size:11px;color:#888;letter-spacing:.08em;text-transform:uppercase;}}

  /* ── Waybill shell — A5 148×210mm ── */
  .wb{{
    width:148mm;
    min-height:210mm;
    max-height:210mm;
    background:#fff;
    border-radius:4px;
    overflow:hidden;
    box-shadow:0 2px 20px rgba(0,0,0,.12);
    display:flex;
    flex-direction:column;
  }}

  /* ── Header ── */
  .hdr{{
    background:#1a1a1a;
    color:#fff;
    padding:9px 14px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    flex-shrink:0;
  }}
  .brand{{font-family:'DM Serif Display',serif;font-size:16px;line-height:1;}}
  .brand-sub{{font-size:7px;color:#aaa;letter-spacing:.12em;text-transform:uppercase;margin-top:2px;}}
  .oc-label{{font-size:7px;color:#888;letter-spacing:.1em;text-transform:uppercase;text-align:right;}}
  .oc-val{{font-size:13px;font-weight:800;color:#c8a96e;letter-spacing:.04em;text-align:right;}}

  /* ── Type strip ── */
  .tstrip{{
    background:#c8a96e;
    padding:4px 14px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-size:8px;
    font-weight:700;
    letter-spacing:.14em;
    text-transform:uppercase;
    color:#fff;
    flex-shrink:0;
  }}
  .rush{{background:#e53e3e;color:#fff;font-size:7px;font-weight:700;padding:2px 6px;border-radius:2px;}}

  /* ── Florist body ── */
  .florist-body{{
    flex:1;
    overflow:hidden;
    display:flex;
    flex-direction:column;
    padding:10px 14px 6px;
    gap:6px;
  }}

  /* ── Inspo ── */
  .inspo-wrap{{flex-shrink:0;}}
  .inspo-row{{display:flex;gap:6px;}}
  .inspo-img{{
    width:100%;
    max-height:78mm;
    object-fit:cover;
    border-radius:5px;
    border:1.5px solid #e0dbd4;
    display:block;
  }}
  .inspo-multi{{flex:1;width:auto;max-height:50mm;}}
  .inspo-empty{{
    background:#f7f4f0;
    border:1.5px dashed #d0cbc3;
    border-radius:5px;
    padding:14px;
    text-align:center;
    color:#bbb;
    font-size:10px;
  }}

  /* ── Two-column florist grid ── */
  .fgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;}}
  .fgrid.full{{grid-column:1/-1;}}
  .fl{{font-size:7px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#c8a96e;display:block;margin-bottom:2px;}}
  .fval{{font-size:11px;font-weight:600;color:#1a1a1a;line-height:1.3;}}
  .fval.lg{{font-size:12px;font-weight:800;}}
  .muted{{font-size:10px;color:#888;font-weight:400;}}
  .f-row{{font-size:10px;color:#555;}}
  .clr{{color:#888;font-size:10px;}}

  /* ── Flower list ── */
  .flist{{list-style:none;}}
  .flist li{{font-size:10px;color:#333;line-height:1.6;display:flex;gap:4px;align-items:baseline;}}
  .dot{{color:#c8a96e;font-weight:700;flex-shrink:0;}}

  /* ── Card message ── */
  .card-msg{{border-left:2.5px solid #c8a96e;padding-left:8px;}}
  .card-line{{font-size:9px;color:#888;}}
  .card-line b{{color:#333;}}
  .cl{{color:#aaa;}}
  .card-body{{font-size:10px;color:#444;font-style:italic;line-height:1.4;margin:2px 0;}}

  /* ── Notes ── */
  .notes-block{{font-size:9px;color:#555;line-height:1.6;}}
  .notes-block div{{padding:0;}}

  /* ── Badges ── */
  .badge-sub-ok{{display:inline-block;background:#e8f5ee;border:1px solid #2d6a4f;color:#2d6a4f;font-size:8px;font-weight:700;padding:1px 6px;border-radius:2px;}}
  .badge-sub-no{{display:inline-block;background:#fce8e8;border:1px solid #c0392b;color:#c0392b;font-size:8px;font-weight:700;padding:1px 6px;border-radius:2px;}}
  .badge-cod{{display:inline-block;background:#fff3cd;border:1px solid #e6c200;color:#7a6000;font-size:8px;font-weight:700;padding:1px 7px;border-radius:2px;}}
  .badge-paid{{display:inline-block;background:#e8f5ee;border:1px solid #2d6a4f;color:#2d6a4f;font-size:8px;font-weight:700;padding:1px 7px;border-radius:2px;}}

  /* ── Divider ── */
  .div-dark{{
    height:5px;
    background:#e0dbd4;
    position:relative;
    flex-shrink:0;
    margin:0 -14px;
  }}
  .div-dark::before,.div-dark::after{{
    content:'';position:absolute;top:50%;transform:translateY(-50%);
    width:10px;height:10px;background:#fff;border-radius:50%;
  }}
  .div-dark::before{{left:-5px;}}
  .div-dark::after{{right:-5px;}}

  /* ── Rider strip ── */
  .rider-strip{{
    flex-shrink:0;
    background:#faf9f7;
    border-top:1px solid #e8e3dc;
    padding:8px 14px;
    display:grid;
    grid-template-columns:1fr auto;
    gap:8px;
    align-items:start;
  }}
  .rider-left{{display:flex;flex-direction:column;gap:4px;}}
  .rider-label{{font-size:7px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#c8a96e;margin-bottom:1px;display:block;}}
  .rider-name{{font-size:13px;font-weight:800;color:#1a1a1a;line-height:1.2;}}
  .rider-contact{{font-size:10px;color:#555;font-weight:500;}}
  .rider-address{{font-size:10px;color:#333;line-height:1.4;font-weight:500;}}
  .rider-zone{{font-size:9px;color:#888;margin-top:1px;}}
  .rider-addons{{font-size:9px;color:#555;font-style:italic;margin-top:2px;}}
  .rider-right{{display:flex;flex-direction:column;align-items:center;gap:3px;}}
  .rider-right img{{width:100px;height:100px;border-radius:3px;}}
  .qr-label{{font-size:6.5px;color:#999;letter-spacing:.08em;text-transform:uppercase;text-align:center;}}

  /* ── Footer bar ── */
  .ftr{{
    background:#1a1a1a;
    padding:4px 14px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-shrink:0;
  }}
  .ftr-branch{{font-size:7px;color:#777;letter-spacing:.08em;text-transform:uppercase;}}
  .ftr-date{{font-size:7px;color:#666;}}

  /* ── Print ── */
  @media print{{
    @page{{
      size:148mm 210mm;
      margin:0;
    }}
    html,body{{
      width:148mm;
      height:210mm;
      margin:0;
      padding:0;
      background:none;
    }}
    .hint{{display:none!important;}}
    .wb{{
      width:148mm;
      height:210mm;
      min-height:unset;
      max-height:210mm;
      box-shadow:none;
      border-radius:0;
      overflow:hidden;
    }}
  }}
</style>
</head>
<body>

<p class="hint">A5 · Ctrl+P or ⌘+P to print</p>

<div class="wb">

  <!-- Header -->
  <div class="hdr">
    <div>
      <div class="brand">Angie's Florist</div>
      <div class="brand-sub">Delivery Waybill</div>
    </div>
    <div>
      <div class="oc-label">Order</div>
      <div class="oc-val">{order.get('order_code','—')}</div>
    </div>
  </div>

  <!-- Type strip -->
  <div class="tstrip">
    <span>{order.get('order_type','Delivery')} · {branch_label}</span>
    {rush_badge}
  </div>

  <!-- Florist body -->
  <div class="florist-body">

    <!-- Inspo -->
    {inspo_section}

    <!-- Arrangement + substitution -->
    <div>
      <span class="fl">🌹 Arrangement</span>
      <span class="fval lg">{order.get('arrangement_name','—')}</span>
      &nbsp; {sub_html}
    </div>

    <!-- Flowers -->
    <div class="fgrid">
      <div>
        <span class="fl">Flowers & Colors</span>
        {flowers_html}
      </div>
      <div>
        <span class="fl">Color Preference</span>
        <span class="fval">{order.get('color_preference','Any') or 'Any'}</span>
        <div style="margin-top:6px;">
          <span class="fl">Florist</span>
          <span class="fval">{order.get('assigned_florist','Unassigned')}</span>
        </div>
      </div>
    </div>

    <!-- Card message -->
    <div>
      <span class="fl">💌 Card Message</span>
      {card_html}
    </div>

    <!-- Order details / notes -->
    {'<div><span class="fl">📋 Order Details</span>' + notes_html + '</div>' if notes_html else ''}

    <!-- Occasion + source -->
    {occ_html}

    <!-- Encoded by -->
    <div class="f-row" style="color:#bbb;font-size:9px;">
      Encoded by {order.get('encoded_by','—')} · {order.get('encoded_at','')}
    </div>

  </div><!-- end florist-body -->

  <!-- Rider strip -->
  <div class="rider-strip">
    <div class="rider-left">
      <div>
        <span class="rider-label">🚴 Recipient</span>
        <div class="rider-name">{order.get('recipient_name','—')}</div>
        <div class="rider-contact">{_fmt_phone(order.get('recipient_phone',''))}</div>
      </div>
      <div>
        <span class="rider-label">Address</span>
        <div class="rider-address">{order.get('delivery_address','—')}</div>
        <div class="rider-zone">Zone: {order.get('delivery_zone','—')} {'· Landmark: ' + order.get('landmark','') if order.get('landmark') else ''}</div>
      </div>
      {'<div class="rider-addons">Add-ons: ' + addons + '</div>' if addons else ''}
      <div style="margin-top:2px;">{cod_html}</div>
    </div>
    <div class="rider-right">
      <img src="data:image/png;base64,{qr_b64}" alt="QR">
      <span class="qr-label">Scan to deliver</span>
    </div>
  </div>

  <!-- Footer -->
  <div class="ftr">
    <span class="ftr-branch">{branch_label} · Angie's Florist</span>
    <span class="ftr-date">{print_time}</span>
  </div>

</div><!-- end wb -->

</body>
</html>"""

    return html


def render_waybill_in_streamlit(order: dict, token: str = None):
    try:
        import streamlit as st
        import streamlit.components.v1 as components
        import base64 as b64lib

        html = generate_waybill_html(order, token)
        b64  = b64lib.b64encode(html.encode("utf-8")).decode("utf-8")
        js   = (
            "<script>(function(){"
            "var b=atob('" + b64 + "');"
            "var by=new Uint8Array(b.length);"
            "for(var i=0;i<b.length;i++){by[i]=b.charCodeAt(i);}"
            "var bl=new Blob([by],{type:'text/html;charset=utf-8'});"
            "var u=URL.createObjectURL(bl);"
            "var w=window.open(u,'_blank');"
            "if(!w){alert('Pop-up blocked — please allow pop-ups for this site.');}"
            "})();</script>"
        )
        components.html(js, height=0, scrolling=False)

    except ImportError:
        print("Streamlit not available")


if __name__ == "__main__":
    sample = {
        "order_code":           "AF-20260729-001",
        "branch":               "sta_rosa",
        "order_type":           "Delivery",
        "is_surprise":          False,
        "arrangement_name":     "BOUQUET OF 3 STEMS OF SUNFLOWER",
        "flowers":              [{"name":"Sunflower","color":"Yellow","qty":3}],
        "color_preference":     "Yellow",
        "allow_substitution":   False,
        "card_to":              "Annika",
        "card_message":         "Happy Birthdayyy",
        "card_from":            "Kings",
        "special_instructions": "1,500 - BOUQUET OF 3 STEMS OF SUNFLOWER\n(NEWSPRINT WRAPPER) (GYPSO FILLERS)\nFREE TOTE BAG\nFREE MESSAGE CARD\nFREE DELIVERY FEE STA ROSA\nTOTAL: 1,500 PAID GCASH",
        "assigned_florist":     "Ate Claire",
        "inspo_photo_urls":     ["https://images.unsplash.com/photo-1490750967868-88df5691cc19?w=400&q=80"],
        "recipient_name":       "Frank Castle",
        "recipient_phone":      "09154171090",
        "delivery_address":     "15 Sonantela Street La Puresma, Santa Rosa Laguna",
        "delivery_zone":        "Sta. Rosa",
        "delivery_time":        "9:00 AM",
        "delivery_date":        "2026-07-29",
        "landmark":             "Vista Mall",
        "sender_name":          "Frank Castle",
        "sender_phone":         "09154171089",
        "payment_method":       "GCash",
        "payment_status":       "Fully Paid",
        "total_price":          1500,
        "down_payment":         0,
        "split_payment":        0,
        "cod_amount":           0,
        "total_balance":        0,
        "assigned_rider":       "Kuya Mark",
        "rider_token":          "testtoken123",
        "encoded_by":           "Jr",
        "encoded_at":           "July 29, 2026 09:00 AM",
        "occasion":             "Birthday",
        "source_page":          "Facebook",
    }
    html = generate_waybill_html(sample, "testtoken123")
    with open("waybill_test.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ waybill_test.html — open in browser to preview")
