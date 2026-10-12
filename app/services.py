import sqlite3
from datetime import date
from typing import Any

from fastapi import HTTPException

from app.database import database_connection


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def require_row(row: sqlite3.Row | None, message: str) -> dict[str, Any]:
    result = row_dict(row)
    if result is None:
        raise HTTPException(status_code=404, detail=message)
    return result


def require_person(connection: sqlite3.Connection, person_id: int) -> None:
    if connection.execute("SELECT id FROM people WHERE id = ?", (person_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Person not found")


def list_people(role: str | None = None) -> list[dict[str, Any]]:
    with database_connection() as connection:
        if role:
            rows = connection.execute("SELECT * FROM people WHERE role = ? ORDER BY id", (role,)).fetchall()
        else:
            rows = connection.execute("SELECT * FROM people ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def get_person(person_id: int) -> dict[str, Any]:
    with database_connection() as connection:
        return require_row(connection.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone(), "Person not found")


def create_person(data: dict[str, Any]) -> dict[str, Any]:
    with database_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO people (full_name, email, contact_number, role) VALUES (?, ?, ?, ?)",
                (data["full_name"], data["email"], data.get("contact_number"), data["role"]),
            )
        except sqlite3.IntegrityError as exc:
            if "people.email" in str(exc) or "UNIQUE constraint failed" in str(exc):
                raise HTTPException(status_code=409, detail="A person with this email already exists") from exc
            raise HTTPException(status_code=409, detail="The person record violates a database rule") from exc
        row = connection.execute("SELECT * FROM people WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def update_person(person_id: int, data: dict[str, Any]) -> dict[str, Any]:
    with database_connection() as connection:
        if connection.execute("SELECT id FROM people WHERE id = ?", (person_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Person not found")
        try:
            connection.execute(
                "UPDATE people SET full_name = ?, email = ?, contact_number = ?, role = ? WHERE id = ?",
                (data["full_name"], data["email"], data.get("contact_number"), data["role"], person_id),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email already exists or the update violates a database rule") from exc
        row = connection.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    return dict(row)


def delete_person(person_id: int) -> None:
    with database_connection() as connection:
        if connection.execute("SELECT id FROM people WHERE id = ?", (person_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Person not found")
        try:
            connection.execute("DELETE FROM people WHERE id = ?", (person_id,))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="This person is linked to reports or claims and cannot be deleted") from exc


def list_items(report_type: str | None = None, status: str | None = None, category: str | None = None, location: str | None = None, search: str | None = None, reporter_id: int | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    for column, value in (("report_type", report_type), ("status", status), ("category", category), ("location", location), ("reporter_id", reporter_id)):
        if value is not None:
            clauses.append(f"{column} = ?")
            values.append(value)
    if search:
        clauses.append("(item_name LIKE ? OR description LIKE ? OR color LIKE ?)")
        term = f"%{search.strip()}%"
        values.extend([term, term, term])
    sql = "SELECT * FROM item_reports"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC, id DESC"
    with database_connection() as connection:
        rows = connection.execute(sql, values).fetchall()
    return [dict(row) for row in rows]


def get_item(item_id: int) -> dict[str, Any]:
    with database_connection() as connection:
        return require_row(connection.execute("SELECT * FROM item_reports WHERE id = ?", (item_id,)).fetchone(), "Item report not found")


def create_item(data: dict[str, Any]) -> dict[str, Any]:
    with database_connection() as connection:
        require_person(connection, data["reporter_id"])
        cursor = connection.execute(
            "INSERT INTO item_reports (report_type, item_name, category, description, color, location, event_date, reporter_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data["report_type"], data["item_name"], data["category"], data["description"], data.get("color"), str(data["location"]), str(data["event_date"]), data["reporter_id"]),
        )
        item_id = cursor.lastrowid
        connection.execute(
            "INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, NULL, 'open', ?, ?)",
            (item_id, data["reporter_id"], "Initial report created"),
        )
        row = connection.execute("SELECT * FROM item_reports WHERE id = ?", (item_id,)).fetchone()
    return dict(row)


def update_item(item_id: int, data: dict[str, Any]) -> dict[str, Any]:
    with database_connection() as connection:
        if connection.execute("SELECT id FROM item_reports WHERE id = ?", (item_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Item report not found")
        connection.execute(
            "UPDATE item_reports SET item_name = ?, category = ?, description = ?, color = ?, location = ?, event_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data["item_name"], data["category"], data["description"], data.get("color"), data["location"], str(data["event_date"]), item_id),
        )
        row = connection.execute("SELECT * FROM item_reports WHERE id = ?", (item_id,)).fetchone()
    return dict(row)


def delete_item(item_id: int) -> None:
    with database_connection() as connection:
        if connection.execute("SELECT id FROM item_reports WHERE id = ?", (item_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Item report not found")
        connection.execute("DELETE FROM item_reports WHERE id = ?", (item_id,))


def close_item(item_id: int, changed_by: int, note: str | None) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute("SELECT * FROM item_reports WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Item report not found")
        if row["status"] in ("claimed", "closed"):
            raise HTTPException(status_code=409, detail=f"An item with status '{row['status']}' cannot be closed again")
        require_person(connection, changed_by)
        connection.execute("UPDATE item_reports SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
        connection.execute(
            "INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, ?, 'closed', ?, ?)",
            (item_id, row["status"], changed_by, note or "Item report closed"),
        )
        updated = connection.execute("SELECT * FROM item_reports WHERE id = ?", (item_id,)).fetchone()
    return dict(updated)


def list_history(item_id: int) -> list[dict[str, Any]]:
    with database_connection() as connection:
        if connection.execute("SELECT id FROM item_reports WHERE id = ?", (item_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Item report not found")
        rows = connection.execute("SELECT * FROM item_status_history WHERE item_id = ? ORDER BY changed_at, id", (item_id,)).fetchall()
    return [dict(row) for row in rows]


def list_claims(status: str | None = None, item_id: int | None = None, claimant_id: int | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    for column, value in (("status", status), ("item_id", item_id), ("claimant_id", claimant_id)):
        if value is not None:
            clauses.append(f"{column} = ?")
            values.append(value)
    sql = "SELECT * FROM claims"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC, id DESC"
    with database_connection() as connection:
        rows = connection.execute(sql, values).fetchall()
    return [dict(row) for row in rows]


def get_claim(claim_id: int) -> dict[str, Any]:
    with database_connection() as connection:
        return require_row(connection.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone(), "Claim not found")


def create_claim(data: dict[str, Any]) -> dict[str, Any]:
    with database_connection() as connection:
        item = connection.execute("SELECT * FROM item_reports WHERE id = ?", (data["item_id"],)).fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Item report not found")
        if item["report_type"] != "found":
            raise HTTPException(status_code=409, detail="Claims can only be submitted for found-item reports")
        if item["status"] in ("claimed", "closed"):
            raise HTTPException(status_code=409, detail="This item is no longer accepting claims")
        require_person(connection, data["claimant_id"])
        existing = connection.execute("SELECT id FROM claims WHERE item_id = ? AND claimant_id = ? AND status = 'pending'", (data["item_id"], data["claimant_id"])).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="This person already has a pending claim for this item")
        cursor = connection.execute(
            "INSERT INTO claims (item_id, claimant_id, claim_details) VALUES (?, ?, ?)",
            (data["item_id"], data["claimant_id"], data["claim_details"]),
        )
        if item["status"] == "open":
            connection.execute("UPDATE item_reports SET status = 'under_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (data["item_id"],))
            connection.execute(
                "INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, 'open', 'under_review', ?, ?)",
                (data["item_id"], data["claimant_id"], "A claim was submitted"),
            )
        row = connection.execute("SELECT * FROM claims WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def review_claim(claim_id: int, decision: str, reviewed_by: int, review_note: str | None) -> dict[str, Any]:
    with database_connection() as connection:
        claim = connection.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if claim is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        if claim["status"] != "pending":
            raise HTTPException(status_code=409, detail="Only pending claims can be reviewed")
        require_person(connection, reviewed_by)
        item = connection.execute("SELECT * FROM item_reports WHERE id = ?", (claim["item_id"],)).fetchone()
        if decision == "approved":
            if item["status"] in ("claimed", "closed"):
                raise HTTPException(status_code=409, detail="This item has already been claimed or closed")
            connection.execute("UPDATE claims SET status = 'rejected', reviewed_by = ?, review_note = ?, reviewed_at = CURRENT_TIMESTAMP WHERE item_id = ? AND id != ? AND status = 'pending'", (reviewed_by, "Another claim was approved", claim["item_id"], claim_id))
            connection.execute("UPDATE claims SET status = 'approved', reviewed_by = ?, review_note = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?", (reviewed_by, review_note, claim_id))
            connection.execute("UPDATE item_reports SET status = 'claimed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (claim["item_id"],))
            connection.execute("INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, ?, 'claimed', ?, ?)", (claim["item_id"], item["status"], reviewed_by, review_note or "Claim approved"))
        else:
            connection.execute("UPDATE claims SET status = 'rejected', reviewed_by = ?, review_note = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?", (reviewed_by, review_note, claim_id))
            remaining = connection.execute("SELECT id FROM claims WHERE item_id = ? AND status = 'pending' AND id != ?", (claim["item_id"], claim_id)).fetchone()
            if not remaining and item["status"] == "under_review":
                connection.execute("UPDATE item_reports SET status = 'open', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (claim["item_id"],))
                connection.execute("INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, 'under_review', 'open', ?, ?)", (claim["item_id"], reviewed_by, "No pending claims remain"))
        row = connection.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    return dict(row)


def delete_claim(claim_id: int) -> None:
    with database_connection() as connection:
        claim = connection.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if claim is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        if claim["status"] != "pending":
            raise HTTPException(status_code=409, detail="Only pending claims can be deleted")
        connection.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
        remaining = connection.execute("SELECT id FROM claims WHERE item_id = ? AND status = 'pending'", (claim["item_id"],)).fetchone()
        item = connection.execute("SELECT status FROM item_reports WHERE id = ?", (claim["item_id"],)).fetchone()
        if not remaining and item and item["status"] == "under_review":
            connection.execute("UPDATE item_reports SET status = 'open', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (claim["item_id"],))
            connection.execute("INSERT INTO item_status_history (item_id, previous_status, new_status, changed_by, note) VALUES (?, 'under_review', 'open', ?, ?)", (claim["item_id"], claim["claimant_id"], "Pending claim removed"))
