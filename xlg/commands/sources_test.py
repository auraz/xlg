"""Source command tests."""
import tempfile
from pathlib import Path
from xlg.commands.sources import cmd_read


def test_read_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("line1\nline2")
        path = f.name
    result = list(cmd_read(path))
    assert result == ["line1\nline2"]
    Path(path).unlink()
