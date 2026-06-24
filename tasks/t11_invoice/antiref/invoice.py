import sys

subtotal = 0
for line in sys.stdin:
    qty, price = line.split(",")
    subtotal += float(qty) * float(price)

print("%.2f" % subtotal)
