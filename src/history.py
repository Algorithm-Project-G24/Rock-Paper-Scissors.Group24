"""Round History."""
import json
from collections import deque


class RoundHistory:
    def __init__(self, size: int = 8):
        self._items = deque(maxlen=size)

    def add(self, player: str, computer: str, result: str):
        self._items.append({"player": player, "computer": computer, "result": result})

    def recent(self):
        """Newest first."""
        return list(reversed(self._items))

    def clear(self):
        self._items.clear()

    def __len__(self):
        return len(self._items)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(self._items), f, indent=2)
