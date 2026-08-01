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
import urllib.parse
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
    """Legacy — kept for compatibility."""
    url = f"{RIDER_PAGE_BASE_URL}?order={order_code}&token={token}"
    qr  = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a1a", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _build_rider_page(order: dict, token: str) -> str:
    """
    Returns a self-contained HTML delivery page for riders.
    Embedded into the QR as a data:text/html URL and linked via the test link.
    Riders can: call recipient, open maps, take photo, confirm delivery.
    Confirm uploads photo to Supabase Storage and patches order status to Delivered.
    """
    SUPABASE_URL     = "https://yvbfggxavlaaohzupnqf.supabase.co"
    SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl2YmZnZ3hhdmxhYW9oenVwbnFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMwNzI3NTIsImV4cCI6MjA1ODY0ODc1Mn0.MBLn7JRHbLCGwFYlwFR-5YBFbvqaZRvP2z0o5x2J1Oo"
    STORAGE_BUCKET   = "angies-florist-uploads"

    order_code   = order.get("order_code", "")
    recip_name   = order.get("recipient_name") or order.get("customer_name", "")
    recip_phone  = (order.get("recipient_phone") or order.get("customer_contact", "")).replace(" ", "")
    recip_fmt    = recip_phone
    if len(recip_phone) == 11:
        recip_fmt = f"{recip_phone[:4]} {recip_phone[4:7]} {recip_phone[7:]}"
    address      = order.get("delivery_address", "")
    zone         = order.get("delivery_zone", "—")
    landmark     = order.get("landmark", "")
    target_date  = order.get("delivery_date", "")
    target_time  = order.get("delivery_time", "")
    arrangement  = order.get("arrangement_name", "")
    balance      = float(order.get("total_balance", 0) or 0)
    pay_method   = str(order.get("payment_method", ""))
    pay_status   = str(order.get("payment_status", "Paid"))
    is_cod       = pay_method.upper() == "COD" and balance > 0
    is_surprise  = bool(order.get("is_surprise", False))
    is_rush      = bool(order.get("priority_rush", False)) or str(order.get("order_type", "")).lower() == "rush"
    card_to      = order.get("card_to", "")
    card_msg     = order.get("card_message", "")
    card_from    = order.get("card_from", "")
    notes        = order.get("special_instructions", "") or ""
    _maps_dest   = " ".join(filter(None, [address, landmark]))
    maps_q       = urllib.parse.quote(_maps_dest)
    rush_badge   = '<span class="rush-badge">RUSH</span>' if is_rush else ""

    # Payment row
    if is_cod:
        payment_row = f'<div class="detail-row"><span class="detail-label">COD Amount</span><span class="detail-value"><span class="cod-highlight">&#8369;{balance:,.0f} — Collect cash</span></span></div>'
    else:
        payment_row = f'<div class="detail-row"><span class="detail-label">Payment</span><span class="detail-value">{pay_method} — {pay_status} &#10003;</span></div>'

    surprise_row = '<div class="detail-row"><span class="detail-label">Sender</span><span class="detail-value"><span class="surprise-tag">&#127873; Surprise — Hidden</span></span></div>' if is_surprise else ""
    landmark_row = f'<div class="detail-row"><span class="detail-label">Landmark</span><span class="detail-value muted">{landmark}</span></div>' if landmark else ""
    notes_row    = f'<div class="detail-row"><span class="detail-label">Special note</span><span class="detail-value muted">{notes}</span></div>' if notes else ""
    card_row     = ""
    if card_to or card_msg or card_from:
        card_inner = " | ".join(filter(None, [
            f"To: {card_to}" if card_to else "",
            card_msg,
            f"From: {card_from}" if card_from else "",
        ]))
        card_row = f'<div class="detail-row"><span class="detail-label">Card</span><span class="detail-value muted">{card_inner}</span></div>'

    # Escape notes for JS string (used in PATCH body)
    notes_js = notes.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Angie's Florist — Delivery</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
  :root{{--gold:#c8a96e;--dark:#1a1a1a;--mid:#555;--light:#f7f4f0;--border:#e8e3dc;--green:#2d6a4f;--red:#c0392b}}
  body{{font-family:'Inter',sans-serif;background:#f0ede8;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:0 0 48px}}
  .page-header{{width:100%;background:var(--dark);padding:16px 20px 14px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}}
  .header-brand{{font-family:'DM Serif Display',serif;font-size:20px;color:#fff}}
  .header-order{{text-align:right}}
  .header-order .order-label{{font-size:9px;color:#888;letter-spacing:.12em;text-transform:uppercase}}
  .header-order .order-code{{font-size:14px;font-weight:700;color:var(--gold);letter-spacing:.06em}}
  .status-bar{{width:100%;background:var(--gold);padding:8px 20px;display:flex;align-items:center;justify-content:space-between}}
  .status-bar .status-text{{font-size:11px;font-weight:600;color:#fff;letter-spacing:.1em;text-transform:uppercase}}
  .rush-badge{{background:#e53e3e;color:#fff;font-size:9px;font-weight:700;padding:3px 8px;border-radius:2px;letter-spacing:.08em}}
  .card{{width:100%;max-width:420px;background:#fff;overflow:hidden;margin-bottom:12px}}
  .card-header{{padding:12px 20px 10px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}}
  .card-icon{{font-size:16px}}.card-title{{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}}
  .card-body{{padding:16px 20px}}
  .recipient-name{{font-size:24px;font-weight:700;color:var(--dark);line-height:1.1;margin-bottom:4px}}
  .recipient-number{{font-size:16px;color:var(--mid);font-weight:500;margin-bottom:14px}}
  .call-btn{{display:flex;align-items:center;gap:8px;background:var(--light);border:1.5px solid var(--border);border-radius:8px;padding:10px 16px;font-size:14px;font-weight:600;color:var(--dark);text-decoration:none;width:fit-content}}
  .address-text{{font-size:17px;font-weight:500;color:var(--dark);line-height:1.5;margin-bottom:6px}}
  .zone-tag{{display:inline-block;background:var(--light);border:1px solid var(--border);color:var(--mid);font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:3px;margin-bottom:14px}}
  .maps-btn{{display:flex;align-items:center;justify-content:center;gap:10px;background:var(--dark);color:#fff;border:none;border-radius:10px;padding:14px 20px;font-size:15px;font-weight:600;width:100%;cursor:pointer;text-decoration:none}}
  .detail-row{{display:flex;justify-content:space-between;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--border);gap:12px}}
  .detail-row:last-child{{border-bottom:none}}
  .detail-label{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#aaa;min-width:90px;padding-top:1px}}
  .detail-value{{font-size:13px;font-weight:500;color:var(--dark);text-align:right;line-height:1.4}}
  .detail-value.muted{{color:var(--mid);font-weight:400}}
  .cod-highlight{{background:#fff3cd;border:1px solid #e6c200;color:#7a6000;font-size:13px;font-weight:700;padding:3px 10px;border-radius:3px}}
  .surprise-tag{{background:#fce8ff;border:1px solid #d4a0e0;color:#7b3f8c;font-size:11px;font-weight:600;padding:2px 8px;border-radius:3px;letter-spacing:.06em}}
  .pod-section{{padding:20px}}
  .pod-title{{font-size:16px;font-weight:700;color:var(--dark);margin-bottom:4px}}
  .pod-sub{{font-size:13px;color:var(--mid);margin-bottom:18px;line-height:1.5}}
  .upload-zone{{border:2px dashed var(--gold);border-radius:12px;padding:28px 20px;text-align:center;background:#fdfaf6;cursor:pointer;position:relative;margin-bottom:16px}}
  .upload-zone input[type="file"]{{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}}
  .upload-icon{{font-size:36px;margin-bottom:8px}}
  .upload-label{{font-size:15px;font-weight:600;color:var(--dark);margin-bottom:4px}}
  .upload-hint{{font-size:12px;color:#aaa}}
  .preview-wrap{{display:none;position:relative;margin-bottom:16px;border-radius:10px;overflow:hidden;border:2px solid var(--gold)}}
  .preview-wrap img{{width:100%;max-height:240px;object-fit:cover;display:block}}
  .preview-remove{{position:absolute;top:8px;right:8px;background:rgba(0,0,0,.6);color:#fff;border:none;border-radius:50%;width:28px;height:28px;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center}}
  .notes-label{{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin-bottom:6px;display:block}}
  .notes-input{{width:100%;border:1.5px solid var(--border);border-radius:8px;padding:10px 14px;font-size:14px;font-family:'Inter',sans-serif;color:var(--dark);background:var(--light);resize:none;outline:none;margin-bottom:20px}}
  .notes-input:focus{{border-color:var(--gold)}}
  .submit-btn{{width:100%;background:var(--green);color:#fff;border:none;border-radius:12px;padding:16px;font-size:16px;font-weight:700;cursor:pointer;letter-spacing:.04em;transition:opacity .15s}}
  .submit-btn:disabled{{opacity:.4;cursor:not-allowed}}
  .submit-btn:not(:disabled):active{{opacity:.85}}
  .error-msg{{background:#fce8e8;border:1px solid var(--red);color:var(--red);border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:12px;display:none}}
  .success-screen{{display:none;width:100%;max-width:420px;flex-direction:column;align-items:center;padding:48px 24px;text-align:center}}
  .success-icon{{font-size:64px;margin-bottom:16px}}
  .success-title{{font-family:'DM Serif Display',serif;font-size:28px;color:var(--dark);margin-bottom:8px}}
  .success-sub{{font-size:15px;color:var(--mid);line-height:1.6;margin-bottom:24px}}
  .success-order{{font-size:13px;font-weight:600;color:var(--gold);letter-spacing:.1em}}
  .success-timestamp{{font-size:12px;color:#bbb;margin-top:4px}}
  .loading-overlay{{display:none;position:fixed;inset:0;background:rgba(26,26,26,.7);z-index:100;align-items:center;justify-content:center;flex-direction:column;gap:16px}}
  .loading-overlay.active{{display:flex}}
  .spinner{{width:40px;height:40px;border:3px solid rgba(200,169,110,.3);border-top-color:var(--gold);border-radius:50%;animation:spin .8s linear infinite}}
  .loading-text{{color:#fff;font-size:14px;font-weight:500}}
  @keyframes spin{{to{{transform:rotate(360deg)}}}}
  .content{{width:100%;max-width:420px;display:flex;flex-direction:column}}
</style>
</head>
<body>

<div class="loading-overlay" id="loadingOverlay">
  <div class="spinner"></div>
  <div class="loading-text" id="loadingText">Confirming delivery…</div>
</div>

<div class="page-header">
  <div class="header-brand">Angie's Florist</div>
  <div class="header-order">
    <div class="order-label">Order</div>
    <div class="order-code">{order_code}</div>
  </div>
</div>
<div class="status-bar">
  <span class="status-text">&#128692; Out for Delivery</span>
  {rush_badge}
</div>

<div class="content" id="mainContent">

  <div class="card">
    <div class="card-header"><span class="card-icon">&#128100;</span><span class="card-title">Recipient</span></div>
    <div class="card-body">
      <div class="recipient-name">{recip_name}</div>
      <div class="recipient-number">{recip_fmt}</div>
      <a href="tel:{recip_phone}" class="call-btn"><span class="call-icon">&#128222;</span> Call recipient</a>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">&#128205;</span><span class="card-title">Delivery Address</span></div>
    <div class="card-body">
      <div class="address-text">{address}</div>
      <div class="zone-tag">Zone: {zone}</div>
      <a href="https://www.google.com/maps/dir/?api=1&destination={maps_q}" target="_blank" class="maps-btn">
        &#128506; Open in Google Maps
      </a>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">&#128230;</span><span class="card-title">Order Details</span></div>
    <div class="card-body" style="padding:0 20px">
      <div class="detail-row"><span class="detail-label">Arrangement</span><span class="detail-value">{arrangement}</span></div>
      <div class="detail-row"><span class="detail-label">Deliver by</span><span class="detail-value">{target_date} &middot; {target_time}</span></div>
      {payment_row}
      {surprise_row}
      {card_row}
      {landmark_row}
      {notes_row}
    </div>
  </div>

  <div class="card">
    <div class="card-header"><span class="card-icon">&#128248;</span><span class="card-title">Proof of Delivery</span></div>
    <div class="pod-section">
      <div class="pod-title">Take a photo to confirm</div>
      <div class="pod-sub">Photo with the recipient or at the door. This marks the order as Delivered.</div>
      <div class="upload-zone" id="uploadZone">
        <input type="file" accept="image/*" capture="environment" id="photoInput" onchange="handlePhoto(this)">
        <div class="upload-icon">&#128247;</div>
        <div class="upload-label">Tap to take photo</div>
        <div class="upload-hint">or choose from gallery</div>
      </div>
      <div class="preview-wrap" id="previewWrap">
        <img id="previewImg" src="" alt="Proof">
        <button class="preview-remove" onclick="removePhoto()">&#10005;</button>
      </div>
      <label class="notes-label" for="deliveryNotes">Delivery notes (optional)</label>
      <textarea class="notes-input" id="deliveryNotes" rows="2" placeholder="e.g. Left with guard, recipient was not home…"></textarea>
      <div class="error-msg" id="errorMsg"></div>
      <button class="submit-btn" id="submitBtn" disabled onclick="confirmDelivery()">&#10003; Confirm Delivery</button>
    </div>
  </div>

</div>

<div class="success-screen" id="successScreen">
  <div class="success-icon">&#9989;</div>
  <div class="success-title">Delivered!</div>
  <div class="success-sub">Order marked as delivered. Great work!</div>
  <div class="success-order">{order_code}</div>
  <div class="success-timestamp" id="successTimestamp"></div>
</div>

<script>
const SUPA_URL    = "{SUPABASE_URL}";
const SUPA_KEY    = "{SUPABASE_ANON_KEY}";
const BUCKET      = "{STORAGE_BUCKET}";
const ORDER_CODE  = "{order_code}";
const ORIG_NOTES  = "{notes_js}";
let photoFile = null;

function handlePhoto(input) {{
  if (!input.files || !input.files[0]) return;
  photoFile = input.files[0];
  const reader = new FileReader();
  reader.onload = e => {{
    document.getElementById('previewImg').src = e.target.result;
    document.getElementById('previewWrap').style.display = 'block';
    document.getElementById('uploadZone').style.display  = 'none';
    document.getElementById('submitBtn').disabled = false;
  }};
  reader.readAsDataURL(photoFile);
}}

function removePhoto() {{
  photoFile = null;
  document.getElementById('previewImg').src = '';
  document.getElementById('previewWrap').style.display = 'none';
  document.getElementById('uploadZone').style.display  = 'block';
  document.getElementById('photoInput').value = '';
  document.getElementById('submitBtn').disabled = true;
}}

function showError(msg) {{
  const el = document.getElementById('errorMsg');
  el.textContent = msg;
  el.style.display = 'block';
}}

async function confirmDelivery() {{
  if (!photoFile) return;
  document.getElementById('errorMsg').style.display = 'none';
  document.getElementById('loadingOverlay').classList.add('active');
  document.getElementById('loadingText').textContent = 'Uploading photo…';
  try {{
    // 1. Upload photo
    const ext  = (photoFile.name.split('.').pop() || 'jpg').toLowerCase();
    const path = `orders/${{ORDER_CODE}}/delivery_proof/${{Date.now()}}.${{ext}}`;
    const upRes = await fetch(`${{SUPA_URL}}/storage/v1/object/${{BUCKET}}/${{path}}`, {{
      method: 'POST',
      headers: {{
        'Authorization': `Bearer ${{SUPA_KEY}}`,
        'Content-Type': photoFile.type || 'image/jpeg',
        'x-upsert': 'true',
      }},
      body: photoFile,
    }});
    if (!upRes.ok) throw new Error('Photo upload failed: ' + await upRes.text());
    const photoUrl = `${{SUPA_URL}}/storage/v1/object/public/${{BUCKET}}/${{path}}`;

    // 2. Find order row
    document.getElementById('loadingText').textContent = 'Updating order…';
    const findRes = await fetch(
      `${{SUPA_URL}}/rest/v1/orders?order_code=eq.${{ORDER_CODE}}&select=id`,
      {{ headers: {{ apikey: SUPA_KEY, Authorization: `Bearer ${{SUPA_KEY}}` }} }}
    );
    const rows = await findRes.json();
    if (!rows || !rows.length) throw new Error('Order not found in system.');
    const orderId = rows[0].id;

    // 3. Patch order
    const riderNotes = document.getElementById('deliveryNotes').value.trim();
    const combinedNotes = riderNotes
      ? (ORIG_NOTES ? ORIG_NOTES + '\\n[Rider] ' + riderNotes : '[Rider] ' + riderNotes)
      : ORIG_NOTES;
    const now = new Date().toISOString();
    const patchRes = await fetch(`${{SUPA_URL}}/rest/v1/orders?id=eq.${{orderId}}`, {{
      method: 'PATCH',
      headers: {{
        apikey: SUPA_KEY,
        Authorization: `Bearer ${{SUPA_KEY}}`,
        'Content-Type': 'application/json',
        Prefer: 'return=minimal',
      }},
      body: JSON.stringify({{
        status: 'Delivered',
        proof_of_delivery: photoUrl,
        delivered_at: now,
        updated_at: now,
        notes: combinedNotes,
      }}),
    }});
    if (!patchRes.ok) throw new Error('Order update failed: ' + await patchRes.text());

    // 4. Success
    document.getElementById('loadingOverlay').classList.remove('active');
    document.getElementById('mainContent').style.display = 'none';
    const sc = document.getElementById('successScreen');
    sc.style.display = 'flex';
    const ts = new Date();
    document.getElementById('successTimestamp').textContent =
      'Confirmed at ' + ts.toLocaleTimeString('en-PH', {{hour:'2-digit',minute:'2-digit'}}) +
      ' · ' + ts.toLocaleDateString('en-PH', {{month:'short',day:'numeric',year:'numeric'}});
    window.scrollTo({{top:0,behavior:'smooth'}});
  }} catch(err) {{
    document.getElementById('loadingOverlay').classList.remove('active');
    showError('&#9888; ' + err.message + ' — please try again or contact the shop.');
  }}
}}
</script>
</body>
</html>"""


def generate_qr_for_order(order: dict, token: str) -> tuple:
    order_code   = order.get("order_code", "")
    delivery_url = f"{RIDER_PAGE_BASE_URL}?order={order_code}&token={token}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(delivery_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1a1a", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8"), delivery_url

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

    qr_b64, delivery_data_url = generate_qr_for_order(order, token)
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

    def _inspo_block(url, idx, multi=False):
        img_id    = f"inspo-img-{idx}"
        img_class = "inspo-img inspo-multi" if multi else "inspo-img"
        item_class = "inspo-item inspo-item-multi" if multi else "inspo-item"
        return f'''<div class="{item_class}">
          <img id="{img_id}" src="{url}" class="{img_class}" alt="Inspo {idx+1}">
          <div class="inspo-crop-controls">
            <button type="button" class="crop-btn no-print" id="{img_id}-btn" onclick="startCrop('{img_id}')">&#9986;&#65039; Adjust Photo</button>
            <span class="crop-actions no-print" id="{img_id}-actions" style="display:none;">
              <button type="button" class="crop-apply-btn no-print" onclick="applyCrop('{img_id}')">&#9989; Apply</button>
              <button type="button" class="crop-cancel-btn no-print" onclick="cancelCrop('{img_id}')">&#10007; Cancel</button>
            </span>
          </div>
        </div>'''

    if inspo_urls:
        # Side by side if multiple, single full-width if one
        if len(inspo_urls) == 1:
            imgs_html = _inspo_block(inspo_urls[0], 0)
        else:
            cols = "".join(_inspo_block(u, i, multi=True) for i, u in enumerate(inspo_urls))
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
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
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

  /* ── Waybill shell — A5 148×210mm ──
     On screen this only sets a MINIMUM height so the page still looks like an
     A5 sheet by default. It must NOT cap height / hide overflow here — with
     multiple inspo photos (or more text), content that doesn't fit in exactly
     210mm was silently clipped, which is what made photos/details disappear
     depending on how much content a given order had. The hard 210mm cap +
     overflow:hidden is reintroduced ONLY inside @media print below, where a
     single fixed A5 page is actually required for printing. */
  .wb{{
    width:148mm;
    min-height:210mm;
    background:#fff;
    border-radius:4px;
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
    display:flex;
    flex-direction:column;
    padding:10px 14px 6px;
    gap:6px;
  }}

  /* ── Inspo ── */
  .inspo-wrap{{flex-shrink:0;}}
  .inspo-row{{display:flex;gap:6px;}}
  .inspo-item{{position:relative;}}
  .inspo-item-multi{{flex:1;}}
  .inspo-img{{
    width:100%;
    max-height:78mm;
    object-fit:contain;
    border-radius:5px;
    border:1.5px solid #e0dbd4;
    display:block;
    background:#f7f4f0;
  }}
  .inspo-multi{{max-height:50mm;}}
  .inspo-empty{{
    background:#f7f4f0;
    border:1.5px dashed #d0cbc3;
    border-radius:5px;
    padding:14px;
    text-align:center;
    color:#bbb;
    font-size:10px;
  }}
  .inspo-crop-controls{{margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;}}
  .crop-btn,.crop-apply-btn,.crop-cancel-btn{{
    font-size:9px;font-weight:600;padding:3px 9px;border-radius:4px;cursor:pointer;
    border:1px solid #c8a96e;background:#fff;color:#8a6d3b;
  }}
  .crop-apply-btn{{border-color:#2d6a4f;color:#2d6a4f;}}
  .crop-cancel-btn{{border-color:#c0392b;color:#c0392b;}}
  /* Cropper.js needs the image visible to size its canvas correctly on this print-oriented layout */
  .cropper-container{{max-width:100%;}}

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
  .qr-test-link{{font-size:7px;color:#c8a96e;text-align:center;text-decoration:none;display:block;margin-top:3px;}}
  .qr-test-link:hover{{text-decoration:underline;}}

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
    @page{{size:148mm 210mm;margin:0!important;}}
    html{{width:148mm!important;height:210mm!important;margin:0!important;padding:0!important;}}
    body{{width:148mm!important;height:210mm!important;margin:0!important;padding:0!important;background:none!important;display:block!important;}}
    .hint{{display:none!important;}}
    .no-print{{display:none!important;}}
    .wb{{width:148mm!important;height:210mm!important;min-height:unset!important;max-height:210mm!important;box-shadow:none!important;border-radius:0!important;overflow:hidden!important;}}
  }}
</style>
</head>
<body>

<p class="hint">A5 · <button onclick="window.print()" style="background:#1a1a1a;color:#fff;border:none;padding:4px 12px;border-radius:4px;cursor:pointer;font-size:11px;">&#128424; Print</button> — set paper to <strong>A5</strong> in print dialog</p>

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
      <a href="{delivery_data_url}" target="_blank" class="qr-test-link no-print">&#128279; Test link</a>
    </div>
  </div>

  <!-- Footer -->
  <div class="ftr">
    <span class="ftr-branch">{branch_label} · Angie's Florist</span>
    <span class="ftr-date">{print_time}</span>
  </div>

</div><!-- end wb -->

<script>
(function() {{
  var cropperInstances = {{}};
  var originalSrcs = {{}};

  window.startCrop = function(id) {{
    var img = document.getElementById(id);
    if (!img) return;
    if (!originalSrcs[id]) originalSrcs[id] = img.src;
    document.getElementById(id + '-actions').style.display = 'inline-flex';
    document.getElementById(id + '-btn').style.display = 'none';
    cropperInstances[id] = new Cropper(img, {{
      viewMode: 1,
      dragMode: 'move',
      zoomable: true,
      rotatable: true,
      scalable: true,
      autoCropArea: 1,
    }});
  }};

  window.applyCrop = function(id) {{
    var cropper = cropperInstances[id];
    if (!cropper) return;
    var canvas = cropper.getCroppedCanvas();
    var img = document.getElementById(id);
    if (canvas) {{
      img.src = canvas.toDataURL('image/jpeg', 0.92);
    }}
    cropper.destroy();
    delete cropperInstances[id];
    document.getElementById(id + '-actions').style.display = 'none';
    document.getElementById(id + '-btn').style.display = 'inline-block';
  }};

  window.cancelCrop = function(id) {{
    var cropper = cropperInstances[id];
    if (cropper) {{
      cropper.destroy();
      delete cropperInstances[id];
    }}
    var img = document.getElementById(id);
    if (originalSrcs[id]) img.src = originalSrcs[id];
    document.getElementById(id + '-actions').style.display = 'none';
    document.getElementById(id + '-btn').style.display = 'inline-block';
  }};
}})();
</script>

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
