"""
waybill_field_adapter.py
Maps angies_florist_v3.py order dict keys to waybill_generator keys.
"""

def adapt_order_for_waybill(order: dict) -> dict:
    # Flower items
    raw_flowers = order.get("flower_items", [])
    flowers = []
    if isinstance(raw_flowers, list):
        for f in raw_flowers:
            if not isinstance(f, dict):
                continue
            name  = f.get("name", f.get("flower", ""))
            color = ", ".join(f.get("colors", [])) if isinstance(f.get("colors"), list) else f.get("color", "")
            qty   = f.get("qty", f.get("quantity", 1))
            flowers.append({"name": name, "color": color, "qty": qty})

    # Inspo photos — all of them, not just first
    inspo_raw = order.get("inspo_pictures", [])
    inspo_urls = inspo_raw if isinstance(inspo_raw, list) else ([inspo_raw] if inspo_raw else [])

    # Payment
    total_price    = float(order.get("total_price", 0) or 0)
    down_payment   = float(order.get("down_payment_amount", 0) or 0)
    split_payment  = float(order.get("split_payment_amount", 0) or 0)
    total_balance  = float(order.get("total_balance", 0) or 0)
    payment_method = order.get("balance_payment_method") or order.get("payment_method", "")
    payment_status = order.get("payment_status", "")
    has_cod        = str(payment_method).upper() == "COD"

    # Substitution notes
    sub_notes = ""
    if order.get("allow_substitution"):
        sub_notes = "Substitution allowed"
        if order.get("substitution_notes"):
            sub_notes += f": {order['substitution_notes']}"

    # Notes — combine regular notes + substitution
    notes_parts = []
    if order.get("notes"):
        notes_parts.append(order["notes"])
    if sub_notes:
        notes_parts.append(sub_notes)
    combined_notes = "\n".join(notes_parts)

    return {
        # Identity
        "order_code":           order.get("order_code", ""),
        "branch":               order.get("branch", order.get("fulfillment_branch", "main")),
        "order_type":           "Rush" if order.get("priority_rush") else order.get("order_type", "Delivery"),
        "is_surprise":          order.get("is_surprise", False),

        # Arrangement + flowers
        "arrangement_name":     order.get("arrangement", ""),
        "arrangement_size":     f"Qty: {order.get('quantity', 1)}",
        "flowers":              flowers,
        "color_preference":     order.get("color_preference", ""),
        "allow_substitution":   order.get("allow_substitution", False),

        # Card
        "card_to":              order.get("message_card_to", ""),
        "card_message":         order.get("message_card_body", ""),
        "card_from":            order.get("message_card_from", ""),

        # Notes
        "special_instructions": combined_notes,

        # Occasion
        "occasion":             order.get("occasion", ""),
        "source_page":          order.get("source_page", ""),

        # Florist
        "assigned_florist":     order.get("assigned_florist", "Unassigned"),
        "inspo_photo_urls":     inspo_urls,   # all photos

        # Recipient
        "recipient_name":       order.get("recipient_name") or order.get("customer_name", ""),
        "recipient_phone":      order.get("recipient_contact") or order.get("customer_contact", ""),
        "delivery_address":     order.get("delivery_address", ""),
        "delivery_zone":        order.get("delivery_zone", ""),
        "delivery_time":        order.get("target_time", ""),
        "delivery_date":        str(order.get("target_date", "")),
        "landmark":             order.get("landmark", ""),

        # Sender
        "sender_name":          order.get("customer_name", ""),
        "sender_phone":         order.get("customer_contact", ""),

        # Payment
        "payment_method":       payment_method,
        "payment_status":       payment_status,
        "total_price":          total_price,
        "down_payment":         down_payment,
        "split_payment":        split_payment,
        "cod_amount":           total_balance if has_cod else 0,
        "total_balance":        total_balance,

        # Rider
        "assigned_rider":       order.get("assigned_rider", "Unassigned"),
        "rider_token":          order.get("rider_token", ""),
        "tracking_token":       order.get("tracking_token", ""),

        # Meta
        "encoded_by":           order.get("encoded_by", ""),
        "encoded_at":           order.get("encoded_at", ""),
    }
