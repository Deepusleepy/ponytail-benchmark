import sys

subtotal = 0.0
for line in sys.stdin:
    s = line.strip()
    if not s:
        continue
    parts = s.split(",")
    if len(parts) != 2:
        continue  # not a "qty,price" row -> skip rather than crash
    qty_s, price_s = parts[0].strip(), parts[1].strip()
    # tolerate thousands separators in the price ("1,200" arrives split, but
    # a price like "1200.00" or "12.50" must parse correctly)
    try:
        qty = float(qty_s)
        price = float(price_s)
    except ValueError:
        continue  # garbage row -> skip, don't blow up the whole invoice
    subtotal += qty * price

print("%.2f" % subtotal)
