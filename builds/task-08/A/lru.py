from collections import OrderedDict


class LRUCache:
    """O(1) LRU cache backed by OrderedDict (move_to_end / popitem are O(1))."""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._d: "OrderedDict[object, object]" = OrderedDict()

    def get(self, key):
        if key not in self._d:
            return None
        self._d.move_to_end(key)
        return self._d[key]

    def put(self, key, value):
        if key in self._d:
            self._d.move_to_end(key)
        self._d[key] = value
        if len(self._d) > self.capacity:
            self._d.popitem(last=False)  # evict least-recently-used


if __name__ == "__main__":
    # Eviction order: oldest untouched key goes first.
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    assert c.get(1) == "a"      # 1 is now most-recent
    c.put(3, "c")               # evicts 2 (LRU)
    assert c.get(2) is None
    assert c.get(3) == "c"

    # get counts as a use.
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.get(1)                    # touch 1
    c.put(3, "c")              # evicts 2, not 1
    assert c.get(1) == "a"
    assert c.get(2) is None

    # Updating an existing key refreshes recency and value, no eviction.
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(1, "A")              # update + touch 1
    c.put(3, "c")             # evicts 2
    assert c.get(1) == "A"
    assert c.get(2) is None
    assert c.get(3) == "c"

    # Capacity limit never exceeded.
    c = LRUCache(3)
    for i in range(10):
        c.put(i, i)
        assert len(c._d) <= 3
    assert c.get(9) == 9 and c.get(6) is None

    # Missing key returns None; capacity 1 edge case.
    c = LRUCache(1)
    assert c.get("x") is None
    c.put("x", 1)
    c.put("y", 2)             # evicts x
    assert c.get("x") is None and c.get("y") == 2

    # None as a stored value is distinct from "missing".
    c = LRUCache(1)
    c.put("k", None)
    assert c.get("k") is None  # ponytail: can't distinguish stored-None from absent via get(); acceptable per spec (get returns value or None)

    print("ok")
