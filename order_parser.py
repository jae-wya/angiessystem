"""
order_parser.py
Angie's Florist — Meta Order Form Parser
-----------------------------------------
Parses pasted order form text from Meta (Facebook/Instagram Messenger)
into structured data ready to populate the New Order form.

Handles:
  - Delivery form format
  - Pick Up form format
  - ORDER DETAILS block (arrangement, price, freebies, payment method)
  - Mixed Tagalog/English labels
  - Customers skipping fields (e.g. blank Sender Name)
  - "Short Card Message" label variation
  - Name pasted above ORDER FORM block (common customer behavior)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ── RESULT ────────────────────────────────────────────────────────────────────

@dataclass
class ParsedOrder:
    order_type:        Optional[str] = None   # "Delivery" or "Pick Up"
    delivery_date:     Optional[str] = None
    delivery_time:     Optional[str] = None
    pickup_branch:     Optional[str] = None

    recipient_name:    Optional[str] = None
    recipient_phone:   Optional[str] = None
    delivery_address:  Optional[str] = None
    delivery_zone:     Optional[str] = None
    landmark:          Optional[str] = None

    card_to:           Optional[str] = None
    card_message:      Optional[str] = None
    card_from:         Optional[str] = None

    sender_name:       Optional[str] = None
    sender_phone:      Optional[str] = None

    # Order details
    arrangement:       Optional[str] = None
    total_amount:      Optional[str] = None
    payment_method:    Optional[str] = None   # e.g. "GCash", "Cash", "Maya"
    payment_status:    Optional[str] = None   # "Paid" or None
    special_notes:     Optional[str] = None   # freebies + extras from ORDER DETAILS

    missing_fields:    list = field(default_factory=list)
    raw_text:          str  = ""


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _clean(value: str) -> Optional[str]:
    if not value:
        return None
    v = value.strip().strip("\t").strip()
    if v.lower() in {"n/a", "na", "none", "-", "—", "", "null", "wala", ":"}:
        return None
    # Remove leading colon artifacts
    v = re.sub(r'^:\s*', '', v).strip()
    return v if v else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r'(\+?63|0)\d{10}', text.replace(" ", "").replace("-", ""))
    if match:
        raw = match.group(0)
        if raw.startswith("+63"):
            raw = "0" + raw[3:]
        elif raw.startswith("63") and len(raw) == 12:
            raw = "0" + raw[2:]
        return raw
    return None


def _extract_total(text: str) -> Optional[str]:
    # "TOTAL: 1,500" or "TOTAL: 1,500 PAID GCASH"
    m = re.search(r'total\s*[:\-]?\s*[₱P]?\s*([\d,]+)', text, re.IGNORECASE)
    if m:
        return f"₱{m.group(1).replace(',', '')}"
    # "1,500 - BOUQUET..." at start of line
    m2 = re.search(r'^[₱P]?([\d,]+)\s*[-–]', text, re.MULTILINE)
    if m2:
        return f"₱{m2.group(1).replace(',', '')}"
    return None


def _extract_payment_method(text: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (method, status) e.g. ('GCash', 'Paid')"""
    text_upper = text.upper()
    method = None
    status = None
    if "GCASH" in text_upper:
        method = "GCash"
    elif "MAYA" in text_upper or "PAYMAYA" in text_upper:
        method = "Maya"
    elif "BANK" in text_upper or "BDO" in text_upper or "BPI" in text_upper:
        method = "Bank Transfer"
    elif "COD" in text_upper or "CASH ON DELIVERY" in text_upper:
        method = "COD"
    elif "CASH" in text_upper:
        method = "Cash"

    if "PAID" in text_upper:
        status = "Paid"
    elif "PARTIAL" in text_upper or "DOWN" in text_upper or "DP" in text_upper:
        status = "Partial"

    return method, status


def _extract_arrangement(details_block: str) -> Optional[str]:
    """Extract main arrangement name — first price-prefixed line."""
    m = re.search(
        r'^[₱P]?[\d,]+\s*[-–]\s*(.+?)(?:\n|$)',
        details_block, re.MULTILINE
    )
    if m:
        val = m.group(1).strip()
        # Strip inline parentheticals that are really notes e.g. (NEWSPRINT WRAPPER)
        val = re.sub(r'\(.*?\)', '', val).strip()
        return _clean(val)
    return None


def _extract_special_notes(details_block: str) -> Optional[str]:
    """
    Return the entire ORDER DETAILS block verbatim — exactly as the
    customer wrote it, including arrangement, freebies, and total.
    This is pasted as-is into Special Instructions / Notes.
    """
    lines = []
    for line in details_block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Skip Angie's Florist header line if it slipped in
        if "angie" in stripped.lower() and "florist" in stripped.lower():
            continue
        lines.append(stripped)
    return "\n".join(lines) if lines else None


# Zone alias map — maps variations in addresses to your DELIVERY_ZONES list
ZONE_ALIASES = {
    "santa rosa":   "Sta. Rosa",
    "sta rosa":     "Sta. Rosa",
    "sta. rosa":    "Sta. Rosa",
    "los banos":    "Los Baños",
    "los baños":    "Los Baños",
    "los baños":    "Los Baños",
    "san pablo":    "San Pablo",
    "san pedro":    "San Pedro",
    "sta. cruz":    "Sta. Cruz",
    "sta cruz":     "Sta. Cruz",
    "santa cruz":   "Sta. Cruz",
    "calamba":      "Calamba",
    "cabuyao":      "Cabuyao",
    "binan":        "Biñan",
    "biñan":        "Biñan",
    "calauan":      "Calauan",
    "alaminos":     "Alaminos",
    "victoria":     "Victoria",
    "pila":         "Pila",
    "bay":          "Bay",
    "nagcarlan":    "Nagcarlan",
    "liliw":        "Liliw",
    "lumban":       "Lumban",
    "pagsanjan":    "Pagsanjan",
    "rizal":        "Rizal",
    "quezon":       "Quezon",
    "batangas":     "Batangas",
}


def extract_zone_from_address(address: str) -> Optional[str]:
    """Match delivery zone from address string using alias map."""
    if not address:
        return None
    addr_lower = address.lower()
    for alias, zone in ZONE_ALIASES.items():
        if alias in addr_lower:
            return zone
    return None


def detect_order_type(text: str) -> str:
    text_lower = text.lower()
    if any(x in text_lower for x in ["pick up", "pickup", "pick-up", "for pick up", "kukuha"]):
        return "Pick Up"
    return "Delivery"


# ── MAIN PARSER ───────────────────────────────────────────────────────────────

def parse_order_paste(raw_text: str) -> ParsedOrder:
    order = ParsedOrder()
    order.raw_text = raw_text
    order.order_type = detect_order_type(raw_text)

    lines = raw_text.splitlines()

    # ── ORDER DETAILS block ───────────────────────────────────────────────────
    details_match = re.search(
        r'ORDER DETAILS?\s*\n(.*?)(?=ORDER FORM|SENDER DETAILS|$)',
        raw_text, re.IGNORECASE | re.DOTALL
    )
    if details_match:
        details_block = details_match.group(1)
        order.arrangement   = _extract_arrangement(details_block)
        order.total_amount  = _extract_total(details_block)
        order.special_notes = _extract_special_notes(details_block)
        order.payment_method, order.payment_status = _extract_payment_method(details_block)

    # If no payment found in details block, check full text
    if not order.payment_method:
        order.payment_method, order.payment_status = _extract_payment_method(raw_text)

    # ── Line-by-line field parsing ────────────────────────────────────────────
    in_sender_section  = False
    in_card_section    = False
    recipient_phone_set = False

    for i, line in enumerate(lines):
        stripped = line.strip().strip("\t")
        lower    = stripped.lower()

        if not stripped:
            continue

        # Section markers
        if any(x in lower for x in ["sender details", "sender name", "nagpadala"]):
            in_sender_section = True

        # ── Delivery Date ──
        if not order.delivery_date and re.match(r'delivery\s*date\s*[:\-]?\s*(.+)', stripped, re.I):
            m = re.match(r'delivery\s*date\s*[:\-\t]+\s*(.+)', stripped, re.I)
            if m: order.delivery_date = _clean(m.group(1))

        # ── Time ──
        elif not order.delivery_time and re.match(r'time\s*[\(\[]?', stripped, re.I):
            m = re.match(r'time[^:]*[:\-\t]+\s*(.+)', stripped, re.I)
            if m:
                val = m.group(1)
                # Strip hint text remnant like "to 6pm):"
                val = re.sub(r'^[^)]*\)\s*:?\s*', '', val).strip()
                order.delivery_time = _clean(val)

        # ── Pick Up Branch ──
        elif not order.pickup_branch and "pick up branch" in lower:
            m = re.match(r'pick\s*up\s*branch[^:]*[:\-\t]+\s*(.+)', stripped, re.I)
            if m:
                val = re.sub(r'^\(.*?\)\s*:?\s*', '', m.group(1)).strip()
                order.pickup_branch = _clean(val)

        # ── Recipient Name ──
        elif not order.recipient_name and re.match(
            r'(name of receiver|receiver|recipient|customer name)\s*[:\-\t]', stripped, re.I
        ):
            m = re.match(r'[^:\-\t]+[:\-\t]+\s*(.+)', stripped, re.I)
            if m: order.recipient_name = _clean(m.group(1))

        # ── Contact Number ──
        elif re.match(r'contact\s*(no\.?|number)?\s*[:\-\t]', stripped, re.I):
            phone = _extract_phone(stripped)
            if phone:
                if in_sender_section:
                    order.sender_phone = phone
                elif not recipient_phone_set:
                    order.recipient_phone = phone
                    recipient_phone_set = True

        # ── Delivery Address ──
        elif not order.delivery_address and re.match(
            r'(complete\s*)?address\s*[:\-\t]', stripped, re.I
        ):
            m = re.match(r'[^:\-\t]+[:\-\t]+\s*(.+)', stripped, re.I)
            if m: order.delivery_address = _clean(m.group(1))

        # ── Landmark ──
        elif not order.landmark and re.match(r'landmark\s*[:\-\t]', stripped, re.I):
            m = re.match(r'landmark\s*[:\-\t]+\s*(.+)', stripped, re.I)
            if m: order.landmark = _clean(m.group(1))

        # ── Card: To ──
        # Must be inside the form block, not ORDER DETAILS
        # Only match if line is exactly "To: <name>" and not near TOTAL
        elif not order.card_to and re.match(r'^to\s*[:\-\t]\s*\S', stripped, re.I):
            # Guard: skip if this is near a TOTAL line
            context = " ".join(lines[max(0,i-3):i+3]).lower()
            if "total" not in context and "paid" not in context:
                m = re.match(r'^to\s*[:\-\t]+\s*(.+)', stripped, re.I)
                if m: order.card_to = _clean(m.group(1))

        # ── Card: Message ──
        elif not order.card_message and re.match(
            r'(short\s+)?card\s*message\s*[💌:\-\t]', stripped, re.I
        ):
            m = re.match(r'[^:\-\t💌]+[:\-\t💌]+\s*(.+)', stripped, re.I)
            if m: order.card_message = _clean(m.group(1))

        # ── Card: From ──
        elif not order.card_from and re.match(r'^from\s*[:\-\t]\s*\S', stripped, re.I):
            context = " ".join(lines[max(0,i-3):i+3]).lower()
            if "total" not in context and "paid" not in context:
                m = re.match(r'^from\s*[:\-\t]+\s*(.+)', stripped, re.I)
                if m: order.card_from = _clean(m.group(1))

        # ── Sender Name ──
        elif in_sender_section and not order.sender_name:
            if re.match(r'sender\s*name\s*[:\-\t]', stripped, re.I):
                m = re.match(r'sender\s*name\s*[:\-\t]+\s*(.*)', stripped, re.I)
                if m: order.sender_name = _clean(m.group(1))

    # ── Sender name fallback: first line of paste if not found ───────────────
    # Common pattern: customer pastes their name above ORDER DETAILS
    if not order.sender_name:
        first_line = _clean(lines[0]) if lines else None
        if first_line and len(first_line.split()) <= 4:
            # Looks like a name (short, no digits, not a keyword)
            if not any(kw in first_line.lower() for kw in
                       ["order", "angie", "delivery", "pick", "form", "details"]):
                if not re.search(r'\d', first_line):
                    order.sender_name = first_line

    # ── Missing fields ────────────────────────────────────────────────────────
    required = (
        ["delivery_date", "delivery_time", "recipient_name",
         "recipient_phone", "delivery_address", "sender_phone"]
        if order.order_type == "Delivery"
        else ["pickup_branch", "delivery_date", "delivery_time",
              "recipient_name", "recipient_phone", "sender_phone"]
    )
    # Auto-detect zone from address if not already set
    if order.delivery_address and not getattr(order, 'delivery_zone', None):
        order.delivery_zone = extract_zone_from_address(order.delivery_address)

    order.missing_fields = [f for f in required if not getattr(order, f)]

    return order


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = """Frank Castle

ORDER DETAILS
1,500 - BOUQUET OF 3 STEMS OF SUNFLOWER
(NEWSPRINT WRAPPER) (GYPSO FILLERS)
FREE TOTE BAG
FREE MESSAGE CARD
FREE DELIVERY FEE STA ROSA
TOTAL: 1,500 PAID GCASH

ORDER FORM 
Angie's Florist\t💐
Delivery Information 🏍️\t
Delivery Date:\tJuly 29, 2026
Time (9am to 6pm): 9am
Name of Receiver: frank castle
Contact No.: 0915417109089
Complete Address: 15 Sonantela Street La puresma, Santa Rosa Laguna
Landmark:\tVista Mall
To: Annika
Short Card Message 💌: Happy Birthdayyy
From: Kings

\t
Sender Details\t
Sender Name:\t
Contact No.: 0915417108989"""

    r = parse_order_paste(sample)
    print("=" * 50)
    print(f"Type:          {r.order_type}")
    print(f"Date:          {r.delivery_date}")
    print(f"Time:          {r.delivery_time}")
    print(f"Recipient:     {r.recipient_name} / {r.recipient_phone}")
    print(f"Address:       {r.delivery_address}")
    print(f"Landmark:      {r.landmark}")
    print(f"Card To:       {r.card_to}")
    print(f"Card Message:  {r.card_message}")
    print(f"Card From:     {r.card_from}")
    print(f"Sender:        {r.sender_name} / {r.sender_phone}")
    print(f"Arrangement:   {r.arrangement}")
    print(f"Total:         {r.total_amount}")
    print(f"Payment:       {r.payment_method} / {r.payment_status}")
    print(f"Special Notes: {r.special_notes}")
    print(f"Missing:       {r.missing_fields}")
    print("=" * 50)