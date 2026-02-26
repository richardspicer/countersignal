"""SQLite-backed evidence store for campaigns and test results."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from countersignal.cxp.models import Campaign, TestResult

_DEFAULT_DB_PATH = Path("cxp-canary.db")

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS test_results (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id),
    technique_id TEXT NOT NULL,
    assistant TEXT NOT NULL,
    model TEXT,
    timestamp TEXT NOT NULL,
    trigger_prompt TEXT NOT NULL,
    capture_mode TEXT NOT NULL,
    captured_files TEXT,
    raw_output TEXT NOT NULL,
    validation_result TEXT NOT NULL DEFAULT 'pending',
    validation_details TEXT,
    notes TEXT
);
"""


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Open or create the evidence database.

    Args:
        db_path: Path to the database file. Defaults to ./cxp-canary.db.

    Returns:
        An open SQLite connection with tables initialized.
    """
    path = db_path or _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist.

    Args:
        conn: An open SQLite connection.
    """
    conn.executescript(_SCHEMA)


def _row_to_campaign(row: tuple) -> Campaign:  # type: ignore[type-arg]
    """Convert a database row to a Campaign dataclass."""
    return Campaign(
        id=row[0],
        name=row[1],
        created=datetime.fromisoformat(row[2]),
        description=row[3] or "",
    )


def _row_to_result(row: tuple) -> TestResult:  # type: ignore[type-arg]
    """Convert a database row to a TestResult dataclass."""
    return TestResult(
        id=row[0],
        campaign_id=row[1],
        technique_id=row[2],
        assistant=row[3],
        model=row[4] or "",
        timestamp=datetime.fromisoformat(row[5]),
        trigger_prompt=row[6],
        capture_mode=row[7],
        captured_files=json.loads(row[8]) if row[8] else [],
        raw_output=row[9],
        validation_result=row[10],
        validation_details=row[11] or "",
        notes=row[12] or "",
    )


def create_campaign(conn: sqlite3.Connection, name: str, description: str = "") -> Campaign:
    """Create a new campaign.

    Args:
        conn: An open SQLite connection.
        name: Campaign name.
        description: Optional description.

    Returns:
        The created Campaign.
    """
    campaign_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO campaigns (id, name, created, description) VALUES (?, ?, ?, ?)",
        (campaign_id, name, now, description),
    )
    conn.commit()
    return Campaign(
        id=campaign_id,
        name=name,
        created=datetime.fromisoformat(now),
        description=description,
    )


def list_campaigns(conn: sqlite3.Connection) -> list[Campaign]:
    """Return all campaigns, newest first.

    Args:
        conn: An open SQLite connection.

    Returns:
        List of campaigns ordered by creation time descending.
    """
    cursor = conn.execute("SELECT * FROM campaigns ORDER BY created DESC, rowid DESC")
    return [_row_to_campaign(row) for row in cursor.fetchall()]


def get_campaign(conn: sqlite3.Connection, campaign_id: str) -> Campaign | None:
    """Get a single campaign by ID.

    Args:
        conn: An open SQLite connection.
        campaign_id: The campaign UUID.

    Returns:
        The Campaign, or None if not found.
    """
    cursor = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    return _row_to_campaign(row) if row else None


def record_result(
    conn: sqlite3.Connection,
    campaign_id: str,
    technique_id: str,
    assistant: str,
    trigger_prompt: str,
    raw_output: str,
    capture_mode: str,
    model: str = "",
    captured_files: list[str] | None = None,
    validation_result: str = "pending",
    validation_details: str = "",
    notes: str = "",
) -> TestResult:
    """Record a test result.

    Args:
        conn: An open SQLite connection.
        campaign_id: The campaign this result belongs to.
        technique_id: Which technique was tested.
        assistant: Which assistant was tested.
        trigger_prompt: The prompt used to trigger the assistant.
        raw_output: Captured output text.
        capture_mode: "file" or "output".
        model: Underlying model name if known.
        captured_files: Paths to captured files (file mode).
        validation_result: Validation status (default "pending").
        validation_details: What the validator found.
        notes: Researcher observations.

    Returns:
        The created TestResult.
    """
    result_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    files = captured_files or []
    conn.execute(
        """INSERT INTO test_results
           (id, campaign_id, technique_id, assistant, model, timestamp,
            trigger_prompt, capture_mode, captured_files, raw_output,
            validation_result, validation_details, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result_id,
            campaign_id,
            technique_id,
            assistant,
            model,
            now,
            trigger_prompt,
            capture_mode,
            json.dumps(files),
            raw_output,
            validation_result,
            validation_details,
            notes,
        ),
    )
    conn.commit()
    return TestResult(
        id=result_id,
        campaign_id=campaign_id,
        technique_id=technique_id,
        assistant=assistant,
        model=model,
        timestamp=datetime.fromisoformat(now),
        trigger_prompt=trigger_prompt,
        capture_mode=capture_mode,
        captured_files=files,
        raw_output=raw_output,
        validation_result=validation_result,
        validation_details=validation_details,
        notes=notes,
    )


def list_results(conn: sqlite3.Connection, campaign_id: str | None = None) -> list[TestResult]:
    """List results, optionally filtered by campaign.

    Args:
        conn: An open SQLite connection.
        campaign_id: Optional campaign ID to filter by.

    Returns:
        List of test results.
    """
    if campaign_id:
        cursor = conn.execute(
            "SELECT * FROM test_results WHERE campaign_id = ? ORDER BY timestamp DESC",
            (campaign_id,),
        )
    else:
        cursor = conn.execute("SELECT * FROM test_results ORDER BY timestamp DESC")
    return [_row_to_result(row) for row in cursor.fetchall()]


def get_result(conn: sqlite3.Connection, result_id: str) -> TestResult | None:
    """Get a single result by ID.

    Args:
        conn: An open SQLite connection.
        result_id: The result UUID.

    Returns:
        The TestResult, or None if not found.
    """
    cursor = conn.execute("SELECT * FROM test_results WHERE id = ?", (result_id,))
    row = cursor.fetchone()
    return _row_to_result(row) if row else None


def update_validation(
    conn: sqlite3.Connection,
    result_id: str,
    validation_result: str,
    validation_details: str,
) -> None:
    """Update the validation fields of a stored test result.

    Args:
        conn: An open SQLite connection.
        result_id: The result UUID to update.
        validation_result: New validation result ("hit", "miss", "partial").
        validation_details: What the validator found.
    """
    conn.execute(
        "UPDATE test_results SET validation_result = ?, validation_details = ? WHERE id = ?",
        (validation_result, validation_details, result_id),
    )
    conn.commit()
