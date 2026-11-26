"""
CRM Persistence Store for Eupnea UK Investor Discovery (Project 2)
Tracks per-investor CRM stages (Viewed, Contacted, Partnered, Invested),
owner assignment (Investor Managed by: Panagiotis Dimitrelis & Team),
dedicated investor portal/profile links, last-checked timestamps,
inbound activity flags, action-needed reminders, and notes.
"""

import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRM_DB_PATH = os.path.join(BASE_DIR, "investor_crm.db")

INVESTOR_PROFILE_STAGES = ("Viewed", "Contacted", "Partnered", "Invested")

CRM_TEAM_MEMBERS = [
    "Panagiotis Dimitrelis",
    "Aadarsh Singh Raghav",
    "Shruti Sharma",
    "Sreelakshmi Ajith K",
    "Sarah Chen",
    "Marcus Vance",
    "Client Services Lead",
]


def normalize_investor_key(raw_id_or_name: str) -> str:
    val = (raw_id_or_name or "").strip().lower()
    val = re.sub(r"[^a-z0-9]+", "_", val).strip("_")
    return val or "unknown_investor"


def init_investor_crm_db(db_path: str = CRM_DB_PATH) -> None:
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investor_crm (
            investor_key TEXT PRIMARY KEY,
            investor_id TEXT DEFAULT '',
            investor_name TEXT NOT NULL,
            category TEXT DEFAULT '',
            profile_stage TEXT DEFAULT '',
            managed_by TEXT DEFAULT '',
            profile_url TEXT DEFAULT '',
            last_checked TEXT DEFAULT '',
            new_activity INTEGER DEFAULT 0,
            action_needed INTEGER DEFAULT 0,
            next_action TEXT DEFAULT '',
            crm_notes TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
        """
    )
    conn.commit()
    conn.close()


def get_all_crm_map(db_path: str = CRM_DB_PATH) -> Dict[str, Dict[str, Any]]:
    init_investor_crm_db(db_path)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM investor_crm ORDER BY updated_at DESC").fetchall()
    conn.close()
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        item = dict(r)
        item["new_activity"] = bool(item.get("new_activity"))
        item["action_needed"] = bool(item.get("action_needed"))
        out[item["investor_key"]] = item
        if item.get("investor_id"):
            out[normalize_investor_key(item["investor_id"])] = item
        if item.get("investor_name"):
            out[normalize_investor_key(item["investor_name"])] = item
    return out


def list_crm_records(
    stage: Optional[str] = None,
    managed_by: Optional[str] = None,
    action_needed_only: bool = False,
    db_path: str = CRM_DB_PATH,
) -> Dict[str, Any]:
    init_investor_crm_db(db_path)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    all_rows = [dict(r) for r in conn.execute("SELECT * FROM investor_crm ORDER BY COALESCE(updated_at, '') DESC").fetchall()]
    conn.close()

    summary = {
        "total_tracked": len(all_rows),
        "viewed_count": sum(1 for r in all_rows if r.get("profile_stage") == "Viewed"),
        "contacted_count": sum(1 for r in all_rows if r.get("profile_stage") == "Contacted"),
        "partnered_count": sum(1 for r in all_rows if r.get("profile_stage") == "Partnered"),
        "invested_count": sum(1 for r in all_rows if r.get("profile_stage") == "Invested"),
        "action_needed_count": sum(1 for r in all_rows if r.get("action_needed")),
        "new_activity_count": sum(1 for r in all_rows if r.get("new_activity")),
        "managed_by_panagiotis": sum(1 for r in all_rows if "panagiotis" in (r.get("managed_by") or "").lower()),
    }

    filtered = []
    for r in all_rows:
        if stage and stage != "all":
            if (r.get("profile_stage") or "") != stage:
                continue
        if managed_by and managed_by != "all":
            if (r.get("managed_by") or "") != managed_by:
                continue
        if action_needed_only and not r.get("action_needed"):
            continue
        r["new_activity"] = bool(r.get("new_activity"))
        r["action_needed"] = bool(r.get("action_needed"))
        filtered.append(r)

    return {"summary": summary, "records": filtered, "team_members": CRM_TEAM_MEMBERS}


def upsert_investor_crm(
    investor_key_or_id: str,
    investor_name: str,
    category: str = "",
    profile_stage: Optional[str] = None,
    managed_by: Optional[str] = None,
    profile_url: Optional[str] = None,
    new_activity: Optional[bool] = None,
    action_needed: Optional[bool] = None,
    next_action: Optional[str] = None,
    crm_notes: Optional[str] = None,
    mark_checked: bool = True,
    db_path: str = CRM_DB_PATH,
) -> Dict[str, Any]:
    init_investor_crm_db(db_path)
    key = normalize_investor_key(investor_key_or_id or investor_name)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if profile_stage is not None and profile_stage != "" and profile_stage not in INVESTOR_PROFILE_STAGES:
        raise ValueError(f"Invalid investor profile stage '{profile_stage}'. Must be one of {INVESTOR_PROFILE_STAGES} or empty.")

    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    existing_row = conn.execute("SELECT * FROM investor_crm WHERE investor_key = ?", (key,)).fetchone()
    if not existing_row and investor_name:
        name_key = normalize_investor_key(investor_name)
        existing_row = conn.execute("SELECT * FROM investor_crm WHERE investor_key = ?", (name_key,)).fetchone()
        if existing_row:
            key = name_key

    curr = dict(existing_row) if existing_row else {
        "investor_key": key,
        "investor_id": str(investor_key_or_id or key),
        "investor_name": investor_name or str(investor_key_or_id or key),
        "category": category or "",
        "profile_stage": "",
        "managed_by": "",
        "profile_url": "",
        "last_checked": "",
        "new_activity": 0,
        "action_needed": 0,
        "next_action": "",
        "crm_notes": "",
        "updated_at": now_str,
    }

    if investor_name:
        curr["investor_name"] = investor_name
    if category:
        curr["category"] = category
    if profile_stage is not None:
        curr["profile_stage"] = profile_stage
    if managed_by is not None:
        curr["managed_by"] = managed_by.strip()
    if profile_url is not None:
        curr["profile_url"] = profile_url.strip()
    if new_activity is not None:
        curr["new_activity"] = 1 if new_activity else 0
    if action_needed is not None:
        curr["action_needed"] = 1 if action_needed else 0
    if next_action is not None:
        curr["next_action"] = next_action.strip()
    if crm_notes is not None:
        curr["crm_notes"] = crm_notes.strip()
    if mark_checked or not curr.get("last_checked"):
        curr["last_checked"] = now_str
    curr["updated_at"] = now_str

    conn.execute(
        """
        INSERT INTO investor_crm (
            investor_key, investor_id, investor_name, category, profile_stage,
            managed_by, profile_url, last_checked, new_activity, action_needed,
            next_action, crm_notes, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(investor_key) DO UPDATE SET
            investor_id = excluded.investor_id,
            investor_name = excluded.investor_name,
            category = excluded.category,
            profile_stage = excluded.profile_stage,
            managed_by = excluded.managed_by,
            profile_url = excluded.profile_url,
            last_checked = excluded.last_checked,
            new_activity = excluded.new_activity,
            action_needed = excluded.action_needed,
            next_action = excluded.next_action,
            crm_notes = excluded.crm_notes,
            updated_at = excluded.updated_at
        """,
        (
            curr["investor_key"],
            curr["investor_id"],
            curr["investor_name"],
            curr["category"],
            curr["profile_stage"],
            curr["managed_by"],
            curr["profile_url"],
            curr["last_checked"],
            int(curr["new_activity"]),
            int(curr["action_needed"]),
            curr["next_action"],
            curr["crm_notes"],
            curr["updated_at"],
        ),
    )
    conn.commit()
    conn.close()

    curr["new_activity"] = bool(curr["new_activity"])
    curr["action_needed"] = bool(curr["action_needed"])
    return curr


def attach_crm_to_item(item: Dict[str, Any], crm_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    raw_id = str(item.get("id") or "")
    name = str(item.get("name") or item.get("fund_or_network_name") or "")
    key_id = normalize_investor_key(raw_id) if raw_id else ""
    key_name = normalize_investor_key(name) if name else ""
    rec = (key_id and crm_map.get(key_id)) or (key_name and crm_map.get(key_name)) or None
    crm_data = {
        "investor_key": (rec["investor_key"] if rec else (key_id or key_name)),
        "profile_stage": (rec.get("profile_stage", "") if rec else ""),
        "managed_by": (rec.get("managed_by", "") if rec else ""),
        "profile_url": (rec.get("profile_url", "") if rec else ""),
        "last_checked": (rec.get("last_checked", "") if rec else ""),
        "new_activity": bool(rec.get("new_activity")) if rec else False,
        "action_needed": bool(rec.get("action_needed")) if rec else False,
        "next_action": (rec.get("next_action", "") if rec else ""),
        "crm_notes": (rec.get("crm_notes", "") if rec else ""),
    }
    return {**item, "crm": crm_data, **crm_data}
