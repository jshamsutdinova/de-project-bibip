from pathlib import Path
from sortedcontainers import SortedList


class IndexUtils:
    """This class operates with index file."""
    def __init__(self, path: Path):
        self.path = path

    def get(self, key: str) -> int | None:
        """Return line number found by key in the index."""
        key = str(key)
        with open(self.path, 'r') as f:
            for row in f:
                idx, line_number = row.strip().split(';')
                if idx == key:
                    return int(line_number)
        return None

    def add(self, line_number: int, new_idx: str) -> None:
        """Add new index to the table. Sort by indexes."""
        indexes = []
        with open(self.path, 'r+') as f:
            for row in f:
                vin, ln = row.strip().split(';')
                indexes.append((vin, int(ln)))
            indexes.append((new_idx, line_number))
            indexes = SortedList(indexes, key=lambda x: x[0])

            f.seek(0)  # delete old lines.
            f.truncate()

            for id, ln in indexes:
                f.write(f"{id};{ln}\n")

    def update(self, old_idx: str, new_idx: str) -> None:
        """Update index in the file."""
        indexes = []

        with open(self.path, 'r') as f:
            for row in f:
                idx, ln = row.strip().split(';')

                if idx == str(old_idx):
                    idx = str(new_idx)

                indexes.append((idx, int(ln)))

        indexes.sort(key=lambda x: x[0])

        with open(self.path, 'w') as f:
            for idx, ln in indexes:
                f.write(f"{idx};{ln}\n")
