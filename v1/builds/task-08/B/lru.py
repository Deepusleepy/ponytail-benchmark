"""O(1) LRU (Least Recently Used) cache.

Implementation uses a hash map (dict) for O(1) lookups plus an intrusive
doubly linked list to track recency in O(1). The most-recently-used node sits
next to ``head``; the least-recently-used node sits next to ``tail``. Both
``get`` and ``put`` count as a "use" and move the touched node to the front.
"""

from __future__ import annotations

from typing import Any, Optional


class _Node:
    """A node in the doubly linked list."""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: Any = None, value: Any = None) -> None:
        self.key = key
        self.value = value
        self.prev: Optional["_Node"] = None
        self.next: Optional["_Node"] = None


class LRUCache:
    """A fixed-capacity cache that evicts the least-recently-used entry.

    All operations (``get`` and ``put``) run in O(1) time.
    """

    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self.capacity = capacity
        self._map: dict[Any, _Node] = {}

        # Sentinel head/tail simplify edge cases (empty list, single node).
        # Order: head <-> (most recent) ... (least recent) <-> tail
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    # -- internal linked-list helpers -------------------------------------

    def _remove(self, node: _Node) -> None:
        """Unlink ``node`` from the list."""
        prev_node = node.prev
        next_node = node.next
        assert prev_node is not None and next_node is not None
        prev_node.next = next_node
        next_node.prev = prev_node
        node.prev = None
        node.next = None

    def _add_to_front(self, node: _Node) -> None:
        """Insert ``node`` right after the head (most-recently-used spot)."""
        first = self._head.next
        assert first is not None
        node.prev = self._head
        node.next = first
        self._head.next = node
        first.prev = node

    def _move_to_front(self, node: _Node) -> None:
        self._remove(node)
        self._add_to_front(node)

    # -- public API -------------------------------------------------------

    def get(self, key: Any) -> Optional[Any]:
        """Return the value for ``key`` (marking it used) or ``None``."""
        node = self._map.get(key)
        if node is None:
            return None
        self._move_to_front(node)
        return node.value

    def put(self, key: Any, value: Any) -> None:
        """Insert or update ``key`` with ``value``, marking it used.

        Evicts the least-recently-used entry if capacity is exceeded.
        """
        node = self._map.get(key)
        if node is not None:
            node.value = value
            self._move_to_front(node)
            return

        new_node = _Node(key, value)
        self._map[key] = new_node
        self._add_to_front(new_node)

        if len(self._map) > self.capacity:
            self._evict_lru()

    def _evict_lru(self) -> None:
        """Remove the least-recently-used entry (the one before the tail)."""
        lru = self._tail.prev
        assert lru is not None and lru is not self._head
        self._remove(lru)
        del self._map[lru.key]

    # -- convenience / introspection --------------------------------------

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: Any) -> bool:
        return key in self._map

    def keys_most_to_least_recent(self) -> list[Any]:
        """Return keys ordered from most- to least-recently-used."""
        result = []
        node = self._head.next
        while node is not None and node is not self._tail:
            result.append(node.key)
            node = node.next
        return result


if __name__ == "__main__":
    # 1. Basic put/get.
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    assert c.get(2) == 2

    # 2. Missing key returns None.
    assert c.get(99) is None

    # 3. Eviction order: capacity 2, inserting a 3rd evicts the LRU.
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(3, "c")  # evicts key 1 (least recently used)
    assert c.get(1) is None
    assert c.get(2) == "b"
    assert c.get(3) == "c"

    # 4. get counts as a use and protects a key from eviction.
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    assert c.get(1) == "a"  # now 1 is most-recently-used, 2 is LRU
    c.put(3, "c")  # evicts key 2
    assert c.get(2) is None
    assert c.get(1) == "a"
    assert c.get(3) == "c"

    # 5. Updating an existing key refreshes value AND recency (no eviction).
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(1, "A")  # update value of 1; 1 becomes most recent, 2 is LRU
    assert c.get(1) == "A"
    assert len(c) == 2  # no growth from an update
    c.put(3, "c")  # evicts key 2 (LRU), not key 1
    assert c.get(2) is None
    assert c.get(1) == "A"
    assert c.get(3) == "c"

    # 6. Capacity limit is never exceeded.
    c = LRUCache(3)
    for i in range(10):
        c.put(i, i * 10)
        assert len(c) <= 3
    # Only the last 3 inserted keys survive.
    assert c.keys_most_to_least_recent() == [9, 8, 7]
    assert c.get(9) == 90 and c.get(8) == 80 and c.get(7) == 70
    for gone in range(7):
        assert c.get(gone) is None

    # 7. Recency ordering reflects the most recent operation.
    c = LRUCache(3)
    c.put("x", 1)
    c.put("y", 2)
    c.put("z", 3)
    assert c.keys_most_to_least_recent() == ["z", "y", "x"]
    c.get("x")  # touch x -> moves to front
    assert c.keys_most_to_least_recent() == ["x", "z", "y"]
    c.put("y", 22)  # update y -> moves to front
    assert c.keys_most_to_least_recent() == ["y", "x", "z"]

    # 8. Capacity-1 cache: every new key evicts the previous one.
    c = LRUCache(1)
    c.put(1, "a")
    assert c.get(1) == "a"
    c.put(2, "b")
    assert c.get(1) is None
    assert c.get(2) == "b"

    # 9. Falsy values (0, "", None, []) are stored and retrievable.
    c = LRUCache(4)
    c.put("zero", 0)
    c.put("empty_str", "")
    c.put("none_val", None)
    c.put("empty_list", [])
    assert c.get("zero") == 0
    assert c.get("empty_str") == ""
    assert "none_val" in c  # key exists even though value is None
    assert c.get("none_val") is None
    assert c.get("empty_list") == []

    # 10. Invalid capacities are rejected.
    for bad in (0, -1, -5):
        try:
            LRUCache(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"capacity {bad} should raise ValueError")

    print("All LRUCache self-checks passed.")
