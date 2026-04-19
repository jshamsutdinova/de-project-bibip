from pathlib import Path


RECORD_SIZE = 500
LINE_SIZE = RECORD_SIZE + 1


class TableUtils:
    """This class operates with txt files."""
    def __init__(self, path: Path):
        self.path = path

    def get_row(self,  line_number: int) -> str:
        """Return row by line number."""
        with open(self.path, 'r') as f:
            f.seek(line_number * LINE_SIZE)
            row = f.read(LINE_SIZE)
            return row

    def write_row(self, line_number: int, row: str) -> None:
        """Write row to the line number in the file."""
        with open(self.path, 'r+') as f:
            f.seek(line_number * LINE_SIZE)
            f.write(row)

        assert len(row) == LINE_SIZE

    def append_row(self, row: str) -> None:
        """Paste new row to the file."""
        with open(self.path, 'r+') as f:
            f.seek(0, 2)
            file_size = self.path.stat().st_size
            line_number = file_size // LINE_SIZE

            f.write(row)

            return line_number
