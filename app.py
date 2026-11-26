"""
High-Velocity In-House Fundraising & Investor Discovery Engine
Powered by Autonomous Multi-Agent Swarm and Direct Pitch Generation
Integrated with Notion AI OS, Pitch Loop Engine, Virtual Data Room (VDR),
and Eupnea UK Early-Stage Angel, Family Office & Investor Network Matcher (£50K - £500K)

Zero Cost • Unlimited Matches • Full Privacy • High Quantity • Sub-Second Latency
"""

import os
import json
import csv
import io
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from matcher import VCMatcher, EupneaAngelMatcher
from outreach_engine import OutreachEngine
from ai_fundraising_swarm import fleet
from notion_sync import notion_bridge
from pitch_loop_engine import pitch_loop
from data_room_builder import vdr_builder
from crm_store import (
    init_investor_crm_db,
    get_all_crm_map,
    list_crm_records,
    upsert_investor_crm,
    attach_crm_to_item,
    CRM_TEAM_MEMBERS,
    INVESTOR_PROFILE_STAGES,
)

init_investor_crm_db()

try:
    from investor_search_refinement_engine import search_refinement_engine, RefinedPlatformFilter
except (ImportError, Exception) as _eng_err:
    print(f"[REFINEMENT ENGINE NOTICE] {type(_eng_err).__name__}: {_eng_err}")
    search_refinement_engine = None
    RefinedPlatformFilter = None

app = FastAPI(title="Eupnea Early-Stage UK Investor Discovery Engine (£50K - £500K)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

matcher = VCMatcher()
angel_matcher = EupneaAngelMatcher()
outreach = OutreachEngine()

class MatchRequest(BaseModel):
    company_name: str = "Company X"
    sector: str = "B2B SaaS"
    stage: str = "Seed"
    target_raise_gbp: int = 1000000
    geo: str = "UK & Europe"
    company_summary: str = "Early-stage B2B SaaS platform building workflow optimization and data orchestration for mid-market scale-ups."
    traction: str = "£28k MRR, 18% MoM growth, 6 active enterprise pilots"
    founder_name: str = "Alex Morgan"
    founder_title: str = "Co-Founder & CEO"
    batch_size: Optional[int] = 50

class AngelMatchRequest(BaseModel):
    company_name: str = "Company X"
    sector: str = "B2B SaaS"
    stage: str = "Pre-Seed"
    target_raise_gbp: int = 150000
    category: Optional[str] = "All"
    min_suitability_score: Optional[int] = 0
    company_summary: Optional[str] = "Early-stage enterprise AI workflow platform designed for high-velocity operations."
    traction: Optional[str] = "£18k MRR, 25% MoM growth, 4 signed pilots"
    founder_name: Optional[str] = "Alex Morgan"
    founder_title: Optional[str] = "Co-Founder & CEO"

class MeetingNotesRequest(BaseModel):
    partner_name: str = "Robin Klein"
    fund_name: str = "LocalGlobe"
    raw_notes: str

class VDRRequest(BaseModel):
    company_name: str = "Company X"
    raise_amount_gbp: int = 150000

class InvestorCRMUpdateRequest(BaseModel):
    investor_key: Optional[str] = None
    investor_id: Optional[str] = None
    investor_name: str
    category: Optional[str] = ""
    profile_stage: Optional[str] = None
    managed_by: Optional[str] = None
    profile_url: Optional[str] = None
    new_activity: Optional[bool] = None
    action_needed: Optional[bool] = None
    next_action: Optional[str] = None
    crm_notes: Optional[str] = None
    mark_checked: Optional[bool] = True


@app.get("/api/crm/team")
async def get_crm_team():
    return {
        "status": "success",
        "team_members": CRM_TEAM_MEMBERS,
        "profile_stages": list(INVESTOR_PROFILE_STAGES),
    }


@app.get("/api/crm/investors")
async def get_crm_investors(
    stage: Optional[str] = None,
    managed_by: Optional[str] = None,
    action_needed_only: bool = False,
):
    data = list_crm_records(stage=stage, managed_by=managed_by, action_needed_only=action_needed_only)
    return {"status": "success", **data}


@app.post("/api/crm/investors/update")
async def update_investor_crm(payload: InvestorCRMUpdateRequest):
    try:
        record = upsert_investor_crm(
            investor_key_or_id=payload.investor_key or payload.investor_id or payload.investor_name,
            investor_name=payload.investor_name,
            category=payload.category or "",
            profile_stage=payload.profile_stage,
            managed_by=payload.managed_by,
            profile_url=payload.profile_url,
            new_activity=payload.new_activity,
            action_needed=payload.action_needed,
            next_action=payload.next_action,
            crm_notes=payload.crm_notes,
            mark_checked=True if payload.mark_checked is None else payload.mark_checked,
        )
        all_data = list_crm_records()
        return {"status": "success", "record": record, "summary": all_data["summary"]}
    except ValueError as e:
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "eupnea-uk-investor-discovery"}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# --- Eupnea Early-Stage Investor Discovery Endpoints (£50k - £500k Scope) ---

@app.get("/api/categories")
async def get_categories():
    """Returns available investor categories and their distribution."""
    return {
        "status": "success",
        "categories": angel_matcher.get_categories()
    }

@app.get("/api/angels")
async def get_angels(category: Optional[str] = None, exclude_active_crm: bool = False):
    """Lists verified UK early stage investors/networks/platforms merged with persistent CRM status."""
    crm_map = get_all_crm_map()
    raw_results = angel_matcher.match(category=category, min_suitability_score=0)
    results = [attach_crm_to_item(r, crm_map) for r in raw_results]
    if exclude_active_crm:
        results = [r for r in results if r.get("profile_stage") not in INVESTOR_PROFILE_STAGES]
    return {
        "status": "success",
        "total": len(results),
        "data": results
    }

@app.post("/api/angels-match")
async def match_angels(payload: AngelMatchRequest):
    """
    Matches startups against UK Angels, Family Offices, Investor Networks & Smart Match Platforms.
    Powered by Commander Aadarsh's 20 Autonomous AI Agents Fleet (5 Squads).
    Applies Eupnea's Early-Stage Investor Suitability Scoring Standard (0 - 100%).
    """
    start = time.time()
    crm_map = get_all_crm_map()
    
    matches = angel_matcher.match(
        category=payload.category,
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        min_suitability_score=payload.min_suitability_score or 0,
        company_summary=payload.company_summary or ""
    )

    enriched = []
    qualified_count = 0
    borderline_count = 0

    for m in matches:
        if m.get("suitability_score", 0) >= 70:
            qualified_count += 1
        elif m.get("suitability_score", 0) >= 50:
            borderline_count += 1

        pitch = outreach.generate_angel_pitch_package(
            company_name=payload.company_name,
            sector=payload.sector,
            stage=payload.stage,
            target_raise=f"{payload.target_raise_gbp:,}",
            traction_highlights=payload.traction or "Active customer pilots and verified growth",
            founder_name=payload.founder_name or "Alex Morgan",
            founder_title=payload.founder_title or "Founder & CEO",
            investor_data=m
        )
        enriched.append(attach_crm_to_item({**m, "outreach": pitch}, crm_map))

    # Run the 20-agent early-stage UK swarm
    fleet_exec = fleet.execute_uk_early_stage_swarm(
        startup_data=payload.model_dump(),
        total_candidates=len(matches)
    )

    elapsed = round(time.time() - start, 3)

    return {
        "status": "success",
        "real_time_elapsed": f"{elapsed}s",
        "total_matches": len(enriched),
        "qualified_count": qualified_count,
        "borderline_count": borderline_count,
        "fleet_telemetry": fleet_exec,
        "squad_logs": fleet_exec.get("squad_logs", []),
        "fleet_size": 20,
        "squads_active": 5,
        "matches": enriched
    }

@app.post("/api/mine-angels")
async def mine_angels(payload: AngelMatchRequest):
    """
    Autonomous Live Mining Pipeline:
    Squad B (UK Recon Swarm) & Squad C (Zero-Bounce Verifier) dynamically mine, verify,
    and ingest newly verified UK Angels, Family Offices & Syndicates matching the startup's sector.
    """
    start = time.time()
    crm_map = get_all_crm_map()
    mine_result = fleet.mine_new_uk_investors(payload.model_dump())
    
    # Reload database into matcher
    angel_matcher.reload_data()

    # Re-run matching with the updated database
    matches = angel_matcher.match(
        category=payload.category,
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        min_suitability_score=payload.min_suitability_score or 0,
        company_summary=payload.company_summary or ""
    )

    enriched = []
    qualified_count = 0
    borderline_count = 0

    for m in matches:
        if m.get("suitability_score", 0) >= 70:
            qualified_count += 1
        elif m.get("suitability_score", 0) >= 50:
            borderline_count += 1

        pitch = outreach.generate_angel_pitch_package(
            company_name=payload.company_name,
            sector=payload.sector,
            stage=payload.stage,
            target_raise=f"{payload.target_raise_gbp:,}",
            traction_highlights=payload.traction or "Active customer pilots and verified growth",
            founder_name=payload.founder_name or "Alex Morgan",
            founder_title=payload.founder_title or "Founder & CEO",
            investor_data=m
        )
        enriched.append(attach_crm_to_item({**m, "outreach": pitch}, crm_map))

    elapsed = round(time.time() - start, 3)

    return {
        "status": "success",
        "mined_count": mine_result.get("mined_count", 0),
        "newly_mined": mine_result.get("newly_mined", []),
        "real_time_elapsed": f"{elapsed}s",
        "total_matches": len(enriched),
        "qualified_count": qualified_count,
        "borderline_count": borderline_count,
        "fleet_logs": mine_result.get("logs", []),
        "matches": enriched
    }

@app.post("/api/export-angels-csv")
async def export_angels_csv(payload: AngelMatchRequest):
    """Exports early stage matches with full suitability scoring breakdown to CSV."""
    matches = angel_matcher.match(
        category=payload.category,
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        min_suitability_score=payload.min_suitability_score or 0,
        company_summary=payload.company_summary or ""
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Suitability Score (%)", "Suitability Tier", "Name", "Category", "Location", 
        "Cheque Min (£)", "Cheque Max (£)", "Typical Cheque (£)", "Lead Contact", "Role", 
        "Verified Email", "Website", "LinkedIn", "Access Route", "Sectors", "Portfolio", "Suitability Reasons"
    ])

    for m in matches:
        writer.writerow([
            m.get("suitability_score"),
            m.get("suitability_tier"),
            m.get("name"),
            m.get("category"),
            m.get("location"),
            m.get("cheque_min_gbp"),
            m.get("cheque_max_gbp"),
            m.get("typical_cheque_gbp"),
            m.get("lead_contact"),
            m.get("contact_role"),
            m.get("contact_email"),
            m.get("website"),
            m.get("linkedin"),
            m.get("access_route"),
            ", ".join(m.get("sectors", [])),
            ", ".join(m.get("portfolio", [])),
            " | ".join(m.get("suitability_reasons", []))
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={payload.company_name}_eupnea_uk_investors.csv"}
    )


# --- Legacy Tier-1 VC Swarm & VDR Endpoints ---

@app.get("/api/squads")
async def get_squads():
    return {
        "status": "success",
        "total_agents": 20,
        "squads": fleet.squads
    }

@app.get("/api/agents")
async def get_all_agents():
    return {
        "status": "success",
        "total": 20,
        "squads": fleet.squads,
        "agents": fleet.get_all_agents()
    }

@app.post("/api/fleet-execute")
async def execute_fleet(payload: MatchRequest):
    start = time.time()
    fleet_result = fleet.execute_high_velocity_swarm(
        startup_data=payload.model_dump(),
        batch_size=payload.batch_size or 50
    )
    
    matches = matcher.match(
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        geo=payload.geo,
        company_summary=payload.company_summary
    )
    
    enriched = []
    for m in matches:
        pitch = outreach.generate_pitch_package(
            company_name=payload.company_name,
            sector=payload.sector,
            stage=payload.stage,
            target_raise=f"{payload.target_raise_gbp:,}",
            traction_highlights=payload.traction,
            founder_name=payload.founder_name,
            founder_title=payload.founder_title,
            vc_match=m
        )
        enriched.append({**m, "outreach": pitch})

    elapsed = round(time.time() - start, 3)

    return {
        **fleet_result,
        "real_time_elapsed": f"{elapsed}s",
        "matches_count": len(enriched),
        "matches": enriched
    }

@app.post("/api/match")
async def api_match(payload: MatchRequest):
    matches = matcher.match(
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        geo=payload.geo,
        company_summary=payload.company_summary
    )
    
    enriched_matches = []
    for m in matches:
        pitch = outreach.generate_pitch_package(
            company_name=payload.company_name,
            sector=payload.sector,
            stage=payload.stage,
            target_raise=f"{payload.target_raise_gbp:,}",
            traction_highlights=payload.traction,
            founder_name=payload.founder_name,
            founder_title=payload.founder_title,
            vc_match=m
        )
        enriched_matches.append({**m, "outreach": pitch})
        
    return {
        "status": "success",
        "total_matches": len(enriched_matches),
        "matches": enriched_matches
    }

@app.post("/api/notion/sync")
async def sync_to_notion(payload: MatchRequest):
    matches = matcher.match(
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        geo=payload.geo,
        company_summary=payload.company_summary
    )
    res = notion_bridge.sync_batch_to_notion(matches, payload.company_name)
    return res

@app.post("/api/pitch-loop/analyze")
async def run_pitch_loop(payload: MeetingNotesRequest):
    res = pitch_loop.analyze_meeting_notes(
        partner_name=payload.partner_name,
        fund_name=payload.fund_name,
        meeting_raw_notes=payload.raw_notes
    )
    return res

@app.get("/api/vdr/assemble")
async def assemble_vdr_get(company_name: str = "Company X", raise_amount_gbp: int = 150000):
    res = vdr_builder.assemble_data_room(company_name, raise_amount_gbp)
    return {"status": "success", "vdr": res}

@app.post("/api/vdr/assemble")
async def assemble_vdr_post(payload: VDRRequest):
    res = vdr_builder.assemble_data_room(payload.company_name, payload.raise_amount_gbp)
    return {"status": "success", "vdr": res}

@app.post("/api/export-csv")
async def export_csv(payload: MatchRequest):
    matches = matcher.match(
        sector=payload.sector,
        stage=payload.stage,
        target_raise_gbp=payload.target_raise_gbp,
        geo=payload.geo,
        company_summary=payload.company_summary
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Match Score (%)", "Fund Name", "Location", "Stages", "Check Size Min (£)", "Check Size Max (£)", 
        "Lead Partner", "Partner Title", "Verified Email", "LinkedIn", "Portfolio", "Thesis", "Match Reasons"
    ])
    
    for m in matches:
        writer.writerow([
            m.get("match_score"),
            m.get("fund_name"),
            m.get("location"),
            ", ".join(m.get("stages", [])),
            m.get("check_size_min_gbp"),
            m.get("check_size_max_gbp"),
            m.get("lead_partner"),
            m.get("partner_title"),
            m.get("partner_email"),
            m.get("partner_linkedin"),
            ", ".join(m.get("portfolio", [])),
            m.get("thesis"),
            " | ".join(m.get("match_reasons", []))
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={payload.company_name}_20agent_investors.csv"}
    )

# --- High-Precision Search Refinement & Platform Crawler Endpoints ---

@app.get("/api/investors/refined-search")
@app.post("/api/investors/refined-search")
async def api_refined_search(request: Request):
    """
    Refines investor platforms according to multi-dimensional criteria:
    Stage, Ticket Size, UK Tax Relief (SEIS/EIS), Sector, Dry Powder Recency.
    Supports both GET query parameters and POST JSON payloads.
    """
    if not search_refinement_engine:
        return {"status": "error", "message": "Search refinement engine not initialized."}

    accept = request.headers.get("accept", "")
    # If viewed directly in browser by human, redirect to the visual interactive cockpit
    if request.method == "GET" and "text/html" in accept and request.query_params.get("format") != "json":
        q = str(request.url.query)
        target_url = f"/?tab=tabRefinedSearch&{q}" if q else "/?tab=tabRefinedSearch"
        return RedirectResponse(url=target_url)
    
    if request.method == "POST":
        try:
            payload = await request.json()
        except Exception:
            payload = {}
    else:
        payload = dict(request.query_params)
    
    sectors_raw = payload.get("sectors")
    if isinstance(sectors_raw, str):
        sectors = [s.strip() for s in sectors_raw.split(",") if s.strip()]
    elif isinstance(sectors_raw, list):
        sectors = sectors_raw
    else:
        sectors = ["B2B SaaS", "Enterprise AI"]

    stage = str(payload.get("stage", "Seed"))
    try:
        target_raise = int(payload.get("target_raise_gbp", 1000000))
    except (ValueError, TypeError):
        target_raise = 1000000
    
    uk_tax_only = str(payload.get("uk_tax_relief_only", "true")).lower() in ("true", "1", "yes")
    competitors_raw = payload.get("exclude_competitor_backers", [])
    if isinstance(competitors_raw, str):
        competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]
    else:
        competitors = competitors_raw

    filter_criteria = RefinedPlatformFilter(
        sectors=sectors,
        stage=stage,
        target_raise_gbp=target_raise,
        uk_tax_relief_only=uk_tax_only,
        exclude_competitor_backers=competitors,
    )
    results = search_refinement_engine.execute_refined_search(filter_criteria)
    exclude_crm = str(payload.get("exclude_active_crm", "false")).lower() in ("true", "1", "yes")
    crm_map = get_all_crm_map()
    limit = int(payload.get("limit", 250))
    enriched_investors = [attach_crm_to_item(r.dict(), crm_map) for r in results]
    excluded_crm_count = 0
    if exclude_crm:
        filtered_out = [inv for inv in enriched_investors if inv.get("profile_stage") in INVESTOR_PROFILE_STAGES]
        excluded_crm_count = len(filtered_out)
        enriched_investors = [inv for inv in enriched_investors if inv.get("profile_stage") not in INVESTOR_PROFILE_STAGES]
    return {
        "status": "success",
        "total_matched": len(enriched_investors),
        "excluded_crm_count": excluded_crm_count,
        "criteria": filter_criteria.dict(),
        "investors": enriched_investors[:limit],
        "team_members": CRM_TEAM_MEMBERS,
        "profile_stages": list(INVESTOR_PROFILE_STAGES),
    }

@app.post("/api/investors/live-crawl")
async def api_live_crawl(payload: Dict[str, str]):
    """
    Crawls an investor platform using browser-use (Compulsory Protocol) to verify intake state.
    """
    url = payload.get("url", "https://openvc.app")
    if not search_refinement_engine:
        return {"status": "error", "message": "Crawler not initialized."}
    
    crawl_result = await search_refinement_engine.crawl_platform_live(url)
    return {"status": "success", "result": crawl_result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8095, reload=True)
