# Eupnea Early-Stage UK Investor Discovery Engine (£50k – £500k)

Autonomous AI-Powered Fundraising Cockpit built specifically for early-stage cohort startups participating in the **Eupnea Accelerator Program**.

### Scope & Architecture:
- **Excludes all institutional VCs and big funds.**
- **Focuses strictly on:**
  1. **UK Private & Angel Investors** (£5k to £500k+, SEIS/EIS eligible).
  2. **UK Family Offices** (direct early-stage allocations up to £1M).
  3. **Investor Networks & Syndicates** (UKBAA, Angel Investment Network, F6S, Cambridge Angels, Minerva, Envestors).
  4. **Smart Match Platforms** (Seedrs/Republic, Crowdcube, AngelList UK, SeedLegals, Beauhurst).
- **Suitability Scoring Engine (0–100%)**:
  - Cheque Size Fit (35%)
  - Sector Alignment (30%)
  - SEIS/EIS Eligibility (20%)
  - Active Deal Deployment (15%)
- **Built-in Outreach Generator & CSV Exporter.**

### Execution:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
