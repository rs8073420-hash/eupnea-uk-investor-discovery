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
        self.db_path = db_path
        self.reload_data()

    def reload_data(self):
        """Reloads the verified database from disk."""
        with open(self.db_path, "r", encoding="utf-8") as f:
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

            # --- 1. CATEGORY FIT (+20 Points) ---
            if entry_cat in self.VALID_CATEGORIES:
                breakdown["category_points"] = 20
                score += 20
                reasons.append(f"+20 pts: Verified {entry_cat} category fit")
            else:
                breakdown["category_points"] = 5
                score += 5
                reasons.append(f"+5 pts: Secondary category ({entry_cat})")

            # --- 2. SECTOR & THESIS ALIGNMENT (Max 35 Points, Meaningful Penalty for Mismatch) ---
            sector_lower = sector.lower().strip()
            entry_sectors = [s.lower().strip() for s in entry.get("sectors", [])]
            is_generalist = any(g in entry_sectors for g in ["all sectors", "all tech sectors", "general tech"])
            is_direct_sector = any(sector_lower in s or s in sector_lower for s in entry_sectors)
            is_related_sector = any(any(w in s for w in sector_lower.split()) for s in entry_sectors)

            if is_direct_sector:
                breakdown["sector_points"] = 35
                score += 35
                reasons.append(f"+35 pts: Direct Sector Match ({sector})")
            elif is_related_sector:
                breakdown["sector_points"] = 24
                score += 24
                reasons.append(f"+24 pts: Related Sector Overlap")
            elif is_generalist:
                breakdown["sector_points"] = 18
                score += 18
                reasons.append("+18 pts: Broad Generalist Technology Thesis")
            else:
                breakdown["sector_points"] = -15
                score -= 15
                reasons.append(f"-15 pts: Sector Mismatch (Target: {sector}, Focus: {', '.join(entry.get('sectors', [])[:2])})")

            # --- 3. STAGE FIT (Max 15 Points) ---
            stage_lower = stage.lower().strip()
            entry_stages = [s.lower().strip() for s in entry.get("stages", [])]
            if stage_lower in entry_stages:
                score += 15
                reasons.append(f"+15 pts: Target Stage Match ({stage})")
            elif any(s in stage_lower for s in ["pre-seed", "seed"]) and any(s in "".join(entry_stages) for s in ["pre-seed", "seed"]):
                score += 10
                reasons.append("+10 pts: Adjacent Seed/Pre-Seed Bridge Fit")
            else:
                score += 4
                reasons.append("+4 pts: Multi-stage syndicate participation")

            # --- 4. CHEQUE RANGE FIT (Max 15 Points) ---
            if min_chk <= target_raise <= max_chk:
                breakdown["cheque_points"] = 15
                score += 15
                reasons.append(f"+15 pts: Cheque Range (£{min_chk:,} - £{max_chk:,}) fits £{target_raise:,}")
            elif (target_raise > max_chk and target_raise <= max_chk * 2.0) or (target_raise < min_chk and target_raise >= min_chk * 0.5):
                breakdown["cheque_points"] = 8
                score += 8
                reasons.append(f"+8 pts: Partial syndicate ticket fit for £{target_raise:,}")
            else:
                breakdown["cheque_points"] = -10
                score -= 10
                reasons.append(f"-10 pts: Cheque size mismatch for £{target_raise:,}")

            # --- 5. UK / REGIONAL ACTIVITY (+10 Points) ---
            is_uk = factors.get("uk_market_active", True)
            loc = entry.get("location", "").lower()
            if is_uk and any(uk_term in loc for uk_term in ["uk", "london", "cambridge", "oxford", "manchester", "edinburgh", "bristol", "bournemouth"]):
                breakdown["market_points"] = 10
                score += 10
                reasons.append(f"+10 pts: Verified UK Early-Stage Nexus ({entry.get('location')})")
            else:
                breakdown["market_points"] = 5
                score += 5
                reasons.append("+5 pts: European cross-border presence")

            # --- 6. DIRECT PITCH / ACCESS ROUTE (+5 Points) ---
            has_direct = factors.get("has_direct_route", True)
            contact_email = entry.get("contact_email", "")
            if has_direct and contact_email:
                breakdown["access_points"] = 5
                score += 5
                reasons.append(f"+5 pts: Verified Direct Outreach Route ({entry.get('access_route')})")
            else:
                breakdown["access_points"] = 2
                score += 2
                reasons.append("+2 pts: Syndicate / network submission pathway")

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
