"""Sales aggregation toolkit.

Operates on a list of sales records. Each record is a dict like::

    {"date": "2026-01-15", "product": "Widget", "amount": 19.99}

Stdlib only. Run ``python sales.py`` to execute the self-checks.
"""

from collections import defaultdict


def total_revenue(records):
    """Return the total revenue across all records as a float.

    :param records: iterable of sale dicts with an "amount" key.
    :return: sum of all amounts as a float.
    """
    return float(sum(float(record["amount"]) for record in records))


def revenue_by_product(records):
    """Return a dict mapping each product to its total revenue.

    :param records: iterable of sale dicts with "product" and "amount" keys.
    :return: dict of {product: total_amount}.
    """
    totals = defaultdict(float)
    for record in records:
        totals[record["product"]] += float(record["amount"])
    return dict(totals)


def top_products(records, n):
    """Return the top ``n`` products by total revenue, descending.

    Ties are broken alphabetically by product name for deterministic output.

    :param records: iterable of sale dicts.
    :param n: number of products to return. Negative values are treated as 0.
    :return: list of (product, total) tuples, highest revenue first.
    """
    totals = revenue_by_product(records)
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    if n < 0:
        n = 0
    return ordered[:n]


def monthly_revenue(records):
    """Return a dict mapping 'YYYY-MM' to total revenue for that month.

    The month is derived from the first 7 characters of each record's "date"
    (an ISO-formatted 'YYYY-MM-DD' string).

    :param records: iterable of sale dicts with "date" and "amount" keys.
    :return: dict of {'YYYY-MM': total_amount}.
    """
    totals = defaultdict(float)
    for record in records:
        month = str(record["date"])[:7]
        totals[month] += float(record["amount"])
    return dict(totals)


def _self_check():
    """Run assert-based self-checks against a small sample dataset."""
    sample = [
        {"date": "2026-01-15", "product": "Widget", "amount": 19.99},
        {"date": "2026-01-20", "product": "Gadget", "amount": 5.50},
        {"date": "2026-01-31", "product": "Widget", "amount": 0.01},
        {"date": "2026-02-02", "product": "Gizmo", "amount": 100.00},
        {"date": "2026-02-14", "product": "Gadget", "amount": 4.50},
        {"date": "2026-03-01", "product": "Widget", "amount": 30.00},
    ]

    # total_revenue
    total = total_revenue(sample)
    assert isinstance(total, float)
    assert abs(total - 160.00) < 1e-9, total
    assert total_revenue([]) == 0.0

    # revenue_by_product
    by_product = revenue_by_product(sample)
    assert isinstance(by_product, dict)
    assert abs(by_product["Widget"] - 50.00) < 1e-9, by_product
    assert abs(by_product["Gadget"] - 10.00) < 1e-9, by_product
    assert abs(by_product["Gizmo"] - 100.00) < 1e-9, by_product
    assert set(by_product) == {"Widget", "Gadget", "Gizmo"}
    assert revenue_by_product([]) == {}

    # top_products
    top2 = top_products(sample, 2)
    assert top2 == [("Gizmo", 100.00), ("Widget", 50.00)], top2
    top_all = top_products(sample, 10)
    assert [p for p, _ in top_all] == ["Gizmo", "Widget", "Gadget"], top_all
    assert top_products(sample, 0) == []
    assert top_products([], 3) == []
    # tie-break is alphabetical by product name
    tie = [
        {"date": "2026-01-01", "product": "Beta", "amount": 10.0},
        {"date": "2026-01-01", "product": "Alpha", "amount": 10.0},
    ]
    assert top_products(tie, 2) == [("Alpha", 10.0), ("Beta", 10.0)]

    # monthly_revenue
    monthly = monthly_revenue(sample)
    assert isinstance(monthly, dict)
    assert abs(monthly["2026-01"] - 25.50) < 1e-9, monthly
    assert abs(monthly["2026-02"] - 104.50) < 1e-9, monthly
    assert abs(monthly["2026-03"] - 30.00) < 1e-9, monthly
    assert set(monthly) == {"2026-01", "2026-02", "2026-03"}
    assert monthly_revenue([]) == {}

    # totals are internally consistent
    assert abs(sum(by_product.values()) - total) < 1e-9
    assert abs(sum(monthly.values()) - total) < 1e-9

    print("All self-checks passed.")


if __name__ == "__main__":
    _self_check()
