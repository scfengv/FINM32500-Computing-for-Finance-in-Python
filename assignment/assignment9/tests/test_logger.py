import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import json
from logger import Logger

def test_logger_singleton_and_save(tmp_path):
    path = tmp_path / "events.json"
    log1 = Logger(str(path))
    log2 = Logger("ignored")

    assert log1 is log2

    log1.log("e1", {"a": 1})
    log2.log("e2", {"b": 2})
    log1.save()

    with open(path) as f:
        events = json.load(f)

    assert len(events) == 2