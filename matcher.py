"""
Core Multi-Vector Matching Engine for Venture Capital & Angel Discovery
Includes:
1. VCMatcher: Legacy Tier-1 Institutional Fund matcher
2. EupneaAngelMatcher: Dedicated UK Angel, Family Office, Investor Network & Smart Match Platform
   engine implementing Eupnea's Investor Suitability Scoring Standard (0 - 100%).
Zero Cost, Open Source, and Self-Contained.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class VCMatcher:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "vc_database.json"
        with open(db_path, "r", encoding="utf-8") as f:
            self.vc_data = json.load(f)

    def match(
        self,
        sector: str = "B2B SaaS",
        stage: str = "Seed",
        target_raise_gbp: int = 1000000,
        geo: str = "UK",
        company_summary: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Calculates match score (0 - 100) based on:
        1. Sector Relevance (35%)
        2. Stage Match (25%)
        3. Check Size Compatibility (20%)
        4. Geography Match (15%)
        5. Thesis Keyword Density (5%)
        """
        results = []

        for vc in self.vc_data:
            score = 0
            match_reasons = []

            # 1. Sector Matching
            sector_lower = sector.lower()
            matched_sectors = [s for s in vc.get("sectors", []) if s.lower() in sector_lower or sector_lower in s.lower()]
            if matched_sectors:
                score += 35
                match_reasons.append(f"Direct Sector Alignment ({', '.join(matched_sectors)})")
            elif any(word in [s.lower() for s in vc.get("sectors", [])] for word in sector_lower.split()):
                score += 25
                match_reasons.append("Related Industry Category")

            # 2. Stage Matching
            stage_lower = stage.lower()
            vc_stages_lower = [s.lower() for s in vc.get("stages", [])]
            if stage_lower in vc_stages_lower:
                score += 25
                match_reasons.append(f"Invests actively in {stage} rounds")
            elif "pre-seed" in stage_lower and "seed" in vc_stages_lower:
                score += 18
                match_reasons.append("Adjacent Stage Fit (Pre-Seed to Seed bridge)")

            # 3. Check Size Fit (£ target)
            min_chk = vc.get("check_size_min_gbp", 0)
            max_chk = vc.get("check_size_max_gbp", 10000000)
            if min_chk <= target_raise_gbp <= max_chk:
                score += 20
                match_reasons.append(f"Ticket capacity (£{min_chk:,} - £{max_chk:,}) fits £{target_raise_gbp:,} raise perfectly")
            elif target_raise_gbp < min_chk and target_raise_gbp >= min_chk * 0.5:
                score += 12
                match_reasons.append("Co-investor syndicate candidate")
            elif target_raise_gbp > max_chk:
                score += 10
                match_reasons.append("Potential partial ticket / follow-on check")

            # 4. Geography Match
            geo_lower = geo.lower()
            vc_loc = vc.get("location", "").lower()
            if geo_lower in vc_loc or ("uk" in geo_lower and "london" in vc_loc) or ("europe" in geo_lower and ("uk" in vc_loc or "germany" in vc_loc or "vienna" in vc_loc)):
                score += 15
                match_reasons.append(f"Regional Hub Match ({vc.get('location')})")
            else:
                score += 7
                match_reasons.append("Cross-border European investment coverage")

            # 5. Thesis / Summary Bonus
            thesis_text = (vc.get("thesis", "") + " " + " ".join(vc.get("portfolio", []))).lower()
            if company_summary:
                tokens = [t.lower() for t in company_summary.split() if len(t) > 4]
                matching_tokens = [t for t in tokens if t in thesis_text]
                if matching_tokens:
                    bonus = min(5, len(matching_tokens) * 2)
                    score += bonus
                    match_reasons.append(f"Portfolio synergies detected ({', '.join(set(matching_tokens[:3]))})")

            # Cap at 100
            score = min(100, score)

            results.append({
                **vc,
                "match_score": score,
                "match_reasons": match_reasons
            })

        # Sort descending by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results


class EupneaAngelMatcher:
    """
    Dedicated Discovery & Suitability Scoring Engine for Eupnea Accelerator.
    
    Excludes institutional VCs, mega-funds, and PE firms.
    Focuses 100% on:
      1. UK Angel / Private Investors (cheques £5k - £1m)
      2. UK Family Offices (cheques up to £1m)
      3. Investor Networks (UKBAA, AIN, F6S, Cambridge Angels, 24Haymarket, etc.)
      4. Smart Match Platforms (Connectd, Seedrs, Crowdcube, Floww, SyndicateRoom, Vestbee, etc.)
      
    Suitability Scoring Standard (0 - 100%):
      Derived from Eupnea's suitability scoring methodology:
      - Category Fit (+30 pts)
      - Cheque Range Alignment (£50k to £500k) (+20 pts)
      - Direct Access / Application Route (+20 pts)
      - UK / Regional Activity (+15 pts)
      - Sector Thesis Match (+15 pts)
      - Disqualifiers / Deductions:
          * Institutional VC / Mega-fund: -50 pts
          * Cheque Minimum > £1M: -40 pts
          * Non-UK / Inaccessible Geo: -30 pts
          * Closed Network / No Apply Route: -25 pts
      - Tiers:
          * Qualified: 70 - 100 pts
          * Borderline: 50 - 69 pts
          * Weak: < 50 pts
    """

    VALID_CATEGORIES = [
        "UK Angel / Private Investor",
        "UK Family Office",
        "Investor Network",
        "Smart Match Platform"
    ]

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "uk_angels_and_networks.json"
        with open(db_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_categories(self) -> Dict[str, int]:
        """Returns the 4 categories and the count of entries in each."""
        counts = {cat: 0 for cat in self.VALID_CATEGORIES}
        for item in self.data:
            cat = item.get("category", "")
            if cat in counts:
                counts[cat] += 1
            else:
                counts[cat] = counts.get(cat, 0) + 1
        return counts

    def match(
        self,
        category: Optional[str] = None,
        sector: str = "B2B SaaS",
        stage: str = "Pre-Seed",
        target_raise_gbp: int = 150000,
        min_suitability_score: int = 0,
        company_summary: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Calculates the Suitability Score (0 - 100) and filters by category and threshold.
        """
        results = []
        target_raise = max(25000, min(1000000, target_raise_gbp))

        for entry in self.data:
            # Category Filtering
            entry_cat = entry.get("category", "")
            if category and category.lower() not in ["all", "all early-stage", "any", ""]:
                if category.lower() not in entry_cat.lower():
                    continue

            score = 0
            breakdown = {
                "category_points": 0,
                "cheque_points": 0,
                "access_points": 0,
                "market_points": 0,
                "sector_points": 0,
                "deductions": 0
            }
            reasons = []

            factors = entry.get("suitability_factors", {})

            # --- HARD DISQUALIFIERS / DEDUCTIONS ---
            is_vc = factors.get("is_institutional_vc", False)
            if is_vc:
                breakdown["deductions"] -= 50
                score -= 50
                reasons.append("DEDUCTION (-50): Institutional VC or Mega-fund disqualified per early-stage directive")

            min_chk = entry.get("cheque_min_gbp", 0)
            max_chk = entry.get("cheque_max_gbp", 1000000)
            if min_chk > 1000000:
                breakdown["deductions"] -= 40
                score -= 40
                reasons.append("DEDUCTION (-40): Minimum cheque exceeds £1,000,000 threshold")

            loc = entry.get("location", "").lower()
            if "uk" not in loc and "london" not in loc and "oxford" not in loc and "cambridge" not in loc and "bristol" not in loc and "manchester" not in loc and "edinburgh" not in loc and "european hubs" not in loc:
                breakdown["deductions"] -= 30
                score -= 30
                reasons.append("DEDUCTION (-30): Non-UK geography without UK investment nexus")

            access = entry.get("access_route", "")
            if not access or "none" in access.lower():
                breakdown["deductions"] -= 25
                score -= 25
                reasons.append("DEDUCTION (-25): Closed channel with no application or direct pitch route")

            # --- 1. CATEGORY FIT (+30 Points) ---
            if entry_cat in self.VALID_CATEGORIES:
                breakdown["category_points"] = 30
                score += 30
                reasons.append(f"+30 pts: Verified {entry_cat} category fit")
            else:
                breakdown["category_points"] = 10
                score += 10
                reasons.append(f"+10 pts: Secondary category ({entry_cat})")

            # --- 2. CHEQUE RANGE FIT (+20 Points) ---
            # Pre-seed and Seed normal scope: £50K - £500K. Cheque sizes: £5K - £1M
            if min_chk <= target_raise <= max_chk:
                breakdown["cheque_points"] = 20
                score += 20
                reasons.append(f"+20 pts: Cheque range (£{min_chk:,} - £{max_chk:,}) fits target raise of £{target_raise:,}")
            elif (target_raise > max_chk and target_raise <= max_chk * 2.5) or (target_raise < min_chk and target_raise >= min_chk * 0.5):
                breakdown["cheque_points"] = 14
                score += 14
                reasons.append(f"+14 pts: Partial / Syndicate ticket fit for £{target_raise:,} raise")
            else:
                breakdown["cheque_points"] = 8
                score += 8
                reasons.append(f"+8 pts: Co-syndication candidate across broader syndicate round")

            # --- 3. DIRECT PITCH / ACCESS ROUTE (+20 Points) ---
            has_direct = factors.get("has_direct_route", True)
            contact_email = entry.get("contact_email", "")
            if has_direct and contact_email:
                breakdown["access_points"] = 20
                score += 20
                reasons.append(f"+20 pts: Direct accessible outreach route ({entry.get('access_route')})")
            elif has_direct:
                breakdown["access_points"] = 15
                score += 15
                reasons.append(f"+15 pts: Structured submission portal / platform route")
            else:
                breakdown["access_points"] = 5
                score += 5
                reasons.append("+5 pts: Indirect or referral-dependent pathway")

            # --- 4. UK / REGIONAL ACTIVITY (+15 Points) ---
            is_uk = factors.get("uk_market_active", True)
            if is_uk:
                breakdown["market_points"] = 15
                score += 15
                reasons.append(f"+15 pts: Active in UK early-stage ecosystem ({entry.get('location')})")
            else:
                breakdown["market_points"] = 8
                score += 8
                reasons.append("+8 pts: European cross-border presence")

            # --- 5. SECTOR & STAGE THESIS FIT (+15 Points) ---
            sector_lower = sector.lower()
            entry_sectors = [s.lower() for s in entry.get("sectors", [])]
            entry_stages = [s.lower() for s in entry.get("stages", [])]

            stage_match = stage.lower() in entry_stages or any(s in stage.lower() for s in ["pre-seed", "seed"])

            direct_sector = any(s in sector_lower or sector_lower in s for s in entry_sectors) or "all sectors" in entry_sectors or "all tech sectors" in entry_sectors
            broad_sector = any(w in " ".join(entry_sectors) for w in sector_lower.split())

            if direct_sector and stage_match:
                breakdown["sector_points"] = 15
                score += 15
                reasons.append(f"+15 pts: Direct sector ({sector}) & stage ({stage}) alignment")
            elif direct_sector or stage_match:
                breakdown["sector_points"] = 11
                score += 11
                reasons.append(f"+11 pts: Primary sector overlap in target asset class")
            elif broad_sector:
                breakdown["sector_points"] = 7
                score += 7
                reasons.append(f"+7 pts: Generalist technology investment thesis")
            else:
                breakdown["sector_points"] = 4
                score += 4
                reasons.append("+4 pts: Cross-domain exploratory profile")

            # Bonus for Summary Keyword Synergies (up to 5 bonus points, capped inside 100)
            if company_summary:
                thesis_corpus = (entry.get("thesis", "") + " " + " ".join(entry.get("portfolio", []))).lower()
                tokens = [t.lower() for t in company_summary.split() if len(t) > 4]
                matching = [t for t in tokens if t in thesis_corpus]
                if matching:
                    bonus = min(5, len(matching) * 2)
                    score += bonus
                    reasons.append(f"+{bonus} pts: Portfolio / thesis synergy detected ({', '.join(set(matching[:2]))})")

            # Clamp score 0 to 100
            final_score = max(0, min(100, score))

            # Classification Tier per Eupnea Web Presence Guidelines
            if final_score >= 70:
                tier = "Qualified"
                tier_badge = "emerald"
            elif final_score >= 50:
                tier = "Borderline"
                tier_badge = "amber"
            else:
                tier = "Weak"
                tier_badge = "rose"

            # Filter by threshold
            if final_score < min_suitability_score:
                continue

            results.append({
                **entry,
                "suitability_score": final_score,
                "suitability_tier": tier,
                "tier_badge": tier_badge,
                "points_breakdown": breakdown,
                "suitability_reasons": reasons
            })

        # Sort descending by suitability score
        results.sort(key=lambda x: x["suitability_score"], reverse=True)
        return results


if __name__ == "__main__":
    angel_matcher = EupneaAngelMatcher()
    print("Categories available:", angel_matcher.get_categories())
    
    matches = angel_matcher.match(
        category="All",
        sector="B2B SaaS",
        stage="Seed",
        target_raise_gbp=150000,
        min_suitability_score=50
    )
    print(f"\nTotal early-stage matches >= 50%: {len(matches)}")
    for m in matches[:5]:
        print(f"[{m['suitability_tier']} - {m['suitability_score']}%] {m['name']} ({m['category']}) | Ticket: £{m['cheque_min_gbp']:,}-£{m['cheque_max_gbp']:,} | Route: {m['access_route']}")
