from __future__ import annotations

import os
from pathlib import Path

from axiom.persistence import db


def test_tests_do_not_use_operational_database():
    operational_db = Path(r"C:\axiom\axiom.db").resolve()
    active_db = Path(os.environ["AXIOM_DB_PATH"]).resolve()

    assert active_db != operational_db
    assert db.DB_PATH.resolve() != operational_db