"""
repo_store.py
CSV-backed store for the repository data the admin console works with:
papers, approval decisions, the audit trail and notifications.
Mirrors auth_utils.py (which owns users.csv) - swap for a real DB in production.
"""

import os
from datetime import datetime
from typing import Any

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
PAPERS_CSV = os.path.join(DATA_DIR, "papers.csv")
APPROVALS_CSV = os.path.join(DATA_DIR, "approvals.csv")
AUDIT_CSV = os.path.join(DATA_DIR, "audit_log.csv")
NOTIFICATIONS_CSV = os.path.join(DATA_DIR, "notifications.csv")

PAPER_FIELDS = [
    "paper_id", "title", "authors", "department", "publication_type", "journal",
    "year", "doi", "indexing", "keywords", "abstract", "file_name", "status",
    "citations", "submitted_by", "submitted_on", "updated_on", "is_deleted",
]
APPROVAL_FIELDS = ["approval_id", "paper_id", "reviewer", "decision", "remark", "decided_on"]
AUDIT_FIELDS = ["log_id", "timestamp", "actor", "action", "target", "details"]
NOTIFICATION_FIELDS = [
    "notification_id", "created_on", "audience", "target", "title", "message", "sent_by",
]

NUMERIC_FIELDS = ["year", "citations", "is_deleted"]

STATUSES = ["Pending", "Approved", "Rejected"]
PUBLICATION_TYPES = ["Journal", "Conference", "Book Chapter", "Patent", "Workshop"]
INDEXING_TYPES = ["SCI", "Scopus", "Web of Science", "UGC-CARE", "Other"]
AUDIENCES = ["All users", "Department", "Single user"]


def now():
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# GENERIC CSV HELPERS
# --------------------------------------------------------------------------
def _read(path, fields) -> pd.DataFrame:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        pd.DataFrame(columns=fields).to_csv(path, index=False)
    frame = pd.DataFrame(pd.read_csv(path, dtype=str)).fillna("")
    for field in fields:
        if field not in frame.columns:
            frame[field] = ""
    return pd.DataFrame(frame[fields])


def _write(frame, path, fields):
    os.makedirs(DATA_DIR, exist_ok=True)
    frame[fields].to_csv(path, index=False)


def _append(row, path, fields):
    frame = _read(path, fields)
    complete = {field: str(row.get(field, "")) for field in fields}
    _write(pd.concat([frame, pd.DataFrame([complete])], ignore_index=True), path, fields)


def _next_id(existing, prefix):
    numbers = [int(value.rsplit("-", 1)[-1]) for value in existing if value.rsplit("-", 1)[-1].isdigit()]
    return f"{prefix}-{max(numbers, default=0) + 1:04d}"


# --------------------------------------------------------------------------
# PAPERS
# --------------------------------------------------------------------------
def load_papers(include_deleted=False) -> pd.DataFrame:
    frame = _read(PAPERS_CSV, PAPER_FIELDS)
    for field in NUMERIC_FIELDS:
        frame[field] = pd.Series(pd.to_numeric(frame[field], errors="coerce")).fillna(0).astype(int)
    if include_deleted:
        return frame
    return frame.loc[frame["is_deleted"] == 0].reset_index(drop=True)


def get_paper(paper_id):
    frame = load_papers(include_deleted=True)
    match = frame.loc[frame["paper_id"] == paper_id]
    return match.iloc[0].to_dict() if len(match) else None


def add_paper(values, actor):
    frame = load_papers(include_deleted=True)
    row: dict[str, Any] = {field: "" for field in PAPER_FIELDS}
    row.update(values)
    row["paper_id"] = _next_id(frame["paper_id"].tolist(), "RP")
    row["submitted_on"] = row["updated_on"] = now()
    row["is_deleted"] = 0
    _write(pd.concat([frame, pd.DataFrame([row])], ignore_index=True), PAPERS_CSV, PAPER_FIELDS)
    log_action(actor, "Added paper", row["paper_id"], row["title"])
    return row["paper_id"]


def update_paper(paper_id, values, actor, action="Updated paper"):
    frame = load_papers(include_deleted=True)
    mask = frame["paper_id"] == paper_id
    if not mask.any():
        return False
    for field, value in values.items():
        frame.loc[mask, field] = value
    frame.loc[mask, "updated_on"] = now()
    _write(frame, PAPERS_CSV, PAPER_FIELDS)
    log_action(actor, action, paper_id, values.get("title", ""))
    return True


def set_paper_deleted(paper_id, deleted, actor):
    action = "Moved paper to recycle bin" if deleted else "Restored paper"
    return update_paper(paper_id, {"is_deleted": int(deleted)}, actor, action)


def purge_paper(paper_id, actor):
    frame = load_papers(include_deleted=True)
    _write(frame.loc[frame["paper_id"] != paper_id], PAPERS_CSV, PAPER_FIELDS)
    log_action(actor, "Permanently deleted paper", paper_id)


def decide_paper(paper_id, decision, remark, reviewer):
    update_paper(paper_id, {"status": decision}, reviewer, f"{decision} paper")
    frame = _read(APPROVALS_CSV, APPROVAL_FIELDS)
    _append(
        {
            "approval_id": _next_id(frame["approval_id"].tolist(), "AP"),
            "paper_id": paper_id,
            "reviewer": reviewer,
            "decision": decision,
            "remark": remark,
            "decided_on": now(),
        },
        APPROVALS_CSV,
        APPROVAL_FIELDS,
    )


def load_approvals() -> pd.DataFrame:
    frame = _read(APPROVALS_CSV, APPROVAL_FIELDS)
    return frame.sort_values(by="decided_on", ascending=False).reset_index(drop=True)


def save_upload(uploaded_file):
    """Store an uploaded PDF next to the CSVs and return the stored file name."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
    with open(os.path.join(UPLOADS_DIR, name), "wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return name


# --------------------------------------------------------------------------
# AUDIT TRAIL + NOTIFICATIONS
# --------------------------------------------------------------------------
def log_action(actor, action, target="", details=""):
    frame = _read(AUDIT_CSV, AUDIT_FIELDS)
    _append(
        {
            "log_id": _next_id(frame["log_id"].tolist(), "LOG"),
            "timestamp": now(),
            "actor": actor,
            "action": action,
            "target": target,
            "details": details,
        },
        AUDIT_CSV,
        AUDIT_FIELDS,
    )


def load_audit_log() -> pd.DataFrame:
    frame = _read(AUDIT_CSV, AUDIT_FIELDS)
    return frame.sort_values(by="timestamp", ascending=False).reset_index(drop=True)


def add_notification(audience, target, title, message, sent_by):
    frame = _read(NOTIFICATIONS_CSV, NOTIFICATION_FIELDS)
    _append(
        {
            "notification_id": _next_id(frame["notification_id"].tolist(), "NT"),
            "created_on": now(),
            "audience": audience,
            "target": target,
            "title": title,
            "message": message,
            "sent_by": sent_by,
        },
        NOTIFICATIONS_CSV,
        NOTIFICATION_FIELDS,
    )
    log_action(sent_by, "Sent notification", target or audience, title)


def load_notifications() -> pd.DataFrame:
    frame = _read(NOTIFICATIONS_CSV, NOTIFICATION_FIELDS)
    return frame.sort_values(by="created_on", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# DEMO DATA
# --------------------------------------------------------------------------
DEMO_PAPERS = [
    ("Deep Learning for Medical Image Segmentation", "R. Kumar; S. Nair", "CSE", "Journal",
     "IEEE Transactions on Medical Imaging", 2025, "Scopus", "Approved", 34),
    ("Federated Learning on Edge Devices", "A. Sharma; P. Rao", "CSE", "Conference",
     "ACM MobiCom", 2024, "SCI", "Approved", 18),
    ("Low Power VLSI Design for IoT Nodes", "M. Iyer", "ECE", "Journal",
     "Elsevier Microelectronics Journal", 2024, "SCI", "Approved", 21),
    ("5G Beamforming Using Smart Antennas", "K. Bose; V. Menon", "ECE", "Conference",
     "IEEE VTC", 2025, "Scopus", "Pending", 0),
    ("Additive Manufacturing of Titanium Alloys", "S. Patil", "ME", "Journal",
     "Journal of Materials Processing Technology", 2023, "Web of Science", "Approved", 42),
    ("Vibration Analysis of Composite Beams", "D. Joshi; R. Kulkarni", "ME", "Journal",
     "Springer Mechanica", 2025, "Scopus", "Pending", 0),
    ("Self-Healing Concrete for Coastal Structures", "N. Reddy", "CE", "Journal",
     "Construction and Building Materials", 2024, "SCI", "Approved", 27),
    ("Seismic Retrofitting of RC Frames", "G. Prasad", "CE", "Conference",
     "World Conference on Earthquake Engineering", 2023, "Other", "Rejected", 3),
    ("Grid Integration of Rooftop Solar Systems", "T. Verma; L. Das", "EE", "Journal",
     "IEEE Transactions on Power Systems", 2025, "SCI", "Approved", 15),
    ("Fault Detection in Induction Motors", "H. Gupta", "EE", "Workshop",
     "National Workshop on Electric Drives", 2024, "UGC-CARE", "Pending", 0),
    ("Blockchain Framework for Academic Records", "P. Singh; A. Khan", "IT", "Journal",
     "Journal of Information Security", 2025, "Scopus", "Approved", 30),
    ("Explainable AI for Credit Risk Scoring", "S. Mehta", "IT", "Book Chapter",
     "Springer Studies in Computational Intelligence", 2023, "UGC-CARE", "Approved", 11),
]


def seed_demo_data():
    """Give a brand new repository some sample papers so the dashboard has data to show."""
    if len(load_papers(include_deleted=True)):
        return
    rows = []
    for index, item in enumerate(DEMO_PAPERS, start=1):
        title, authors, department, kind, journal, year, indexing, status, citations = item
        rows.append({
            "paper_id": f"RP-{index:04d}",
            "title": title,
            "authors": authors,
            "department": department,
            "publication_type": kind,
            "journal": journal,
            "year": year,
            "doi": f"10.1234/rprms.{year}.{index:03d}",
            "indexing": indexing,
            "keywords": "",
            "abstract": "",
            "file_name": "",
            "status": status,
            "citations": citations,
            "submitted_by": "seed@rprms.local",
            "submitted_on": now(),
            "updated_on": now(),
            "is_deleted": 0,
        })
    _write(pd.DataFrame(rows), PAPERS_CSV, PAPER_FIELDS)
    log_action("system", "Seeded demo repository", "papers", f"{len(rows)} sample papers")


def reset_repository(actor):
    """Clear papers and approval history, then reload the sample data."""
    _write(pd.DataFrame(columns=PAPER_FIELDS), PAPERS_CSV, PAPER_FIELDS)
    _write(pd.DataFrame(columns=APPROVAL_FIELDS), APPROVALS_CSV, APPROVAL_FIELDS)
    log_action(actor, "Reset repository data", "papers")
    seed_demo_data()
