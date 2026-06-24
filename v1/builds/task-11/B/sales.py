"""Sales aggregation helpers. Records are dicts: {date, product, amount}."""
from collections import defaultdict


def total_revenue(records):
    return sum(r["amount"] for r in records)


def revenue_by_product(records):
    out = defaultdict(float)
    for r in records:
        out[r["product"]] += r["amount"]
    return dict(out)


def top_products(records, n):
    items = revenue_by_product(records).items()
    # ponytail: ties broken by product name for deterministic output.
    return sorted(items, key=lambda kv: (-kv[1], kv[0]))[:n]


def monthly_revenue(records):
    out = defaultdict(float)
    for r in records:
        out[r["date"][:7]] += r["amount"]  # 'YYYY-MM' is the date prefix
    return dict(out)


if __name__ == "__main__":
    sample = [
        {"date": "2026-01-15", "product": "Widget", "amount": 19.99},
        {"date": "2026-01-20", "product": "Gadget", "amount": 5.00},
        {"date": "2026-02-01", "product": "Widget", "amount": 19.99},
        {"date": "2026-02-10", "product": "Gizmo", "amount": 100.00},
    ]

    assert round(total_revenue(sample), 2) == 144.98
    assert total_revenue([]) == 0

    assert revenue_by_product(sample) == {
        "Widget": 39.98,
        "Gadget": 5.00,
        "Gizmo": 100.00,
    }

    assert top_products(sample, 2) == [("Gizmo", 100.00), ("Widget", 39.98)]
    assert top_products(sample, 10) == [
        ("Gizmo", 100.00),
        ("Widget", 39.98),
        ("Gadget", 5.00),
    ]
    assert top_products(sample, 0) == []

    assert monthly_revenue(sample) == {"2026-01": 24.99, "2026-02": 119.99}

    print("ok")
