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
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from matcher import VCMatcher, EupneaAngelMatcher
from outreach_engine import OutreachEngine
from ai_fundraising_swarm import fleet
from notion_sync import notion_bridge
from pitch_loop_engine import pitch_loop
from data_room_builder import vdr_builder

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
async def get_angels(category: Optional[str] = None):
    """Lists verified UK early stage investors/networks/platforms."""
    results = angel_matcher.match(category=category, min_suitability_score=0)
    return {
        "status": "success",
        "total": len(results),
        "data": results
    }

@app.post("/api/angels-match")
async def match_angels(payload: AngelMatchRequest):
    """
    Matches startups against UK Angels, Family Offices, Investor Networks & Smart Match Platforms.
    Applies Eupnea's Early-Stage Investor Suitability Scoring Standard (0 - 100%).
    """
    start = time.time()
    
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
        enriched.append({**m, "outreach": pitch})

    elapsed = round(time.time() - start, 3)

    return {
        "status": "success",
        "real_time_elapsed": f"{elapsed}s",
        "total_matches": len(enriched),
        "qualified_count": qualified_count,
        "borderline_count": borderline_count,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8095, reload=True)
