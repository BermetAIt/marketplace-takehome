"""
Drops all tables and recreates schema (development only).
Usage: set ALLOW_RESET_DEV_DB=1 then: python scripts/reset_dev_db.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

import app.models  # noqa: F401 — register all models on Base.metadata
from app.db.database import Base, engine


def main():
    if os.environ.get("ALLOW_RESET_DEV_DB") != "1":
        print("Refusing: set ALLOW_RESET_DEV_DB=1 to confirm destructive reset.")
        sys.exit(1)
    print("Dropping ALL tables in database (including legacy) ...")
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        rows = conn.execute(text("SHOW TABLES")).fetchall()
        for (table_name,) in rows:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    print("Creating schema from models...")
    Base.metadata.create_all(bind=engine)
    print("Done. Run: python scripts/seed_demo.py")


if __name__ == "__main__":
    main()
