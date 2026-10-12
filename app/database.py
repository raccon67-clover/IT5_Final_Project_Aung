import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATABASE_FILE = Path(os.getenv("LOST_FOUND_DB", Path(__file__).resolve().parent.parent / "lost_found.db"))


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL CHECK (length(trim(full_name)) > 0),
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                contact_number TEXT,
                role TEXT NOT NULL CHECK (role IN ('student', 'staff', 'admin')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS item_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL CHECK (report_type IN ('lost', 'found')),
                item_name TEXT NOT NULL CHECK (length(trim(item_name)) > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                color TEXT,
                location TEXT NOT NULL,
                event_date TEXT NOT NULL,
                reporter_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'under_review', 'matched', 'claimed', 'closed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES people(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                claimant_id INTEGER NOT NULL,
                claim_details TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                reviewed_by INTEGER,
                review_note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                FOREIGN KEY (item_id) REFERENCES item_reports(id) ON DELETE CASCADE,
                FOREIGN KEY (claimant_id) REFERENCES people(id) ON DELETE RESTRICT,
                FOREIGN KEY (reviewed_by) REFERENCES people(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS item_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                changed_by INTEGER NOT NULL,
                note TEXT,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES item_reports(id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES people(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_items_status ON item_reports(status);
            CREATE INDEX IF NOT EXISTS idx_items_type ON item_reports(report_type);
            CREATE INDEX IF NOT EXISTS idx_items_category ON item_reports(category);
            CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
            CREATE INDEX IF NOT EXISTS idx_history_item ON item_status_history(item_id, changed_at);
            """
        )
