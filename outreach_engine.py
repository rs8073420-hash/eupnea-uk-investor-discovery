"""
AI Personalized Pitch & Multi-Channel Outreach Engine
Generates 1-to-1 tailored emails, LinkedIn connection notes, and follow-ups.
Tailored for:
1. Institutional VCs (legacy)
2. UK Angels & Private Investors (SEIS/EIS, fast decisions, founder empathy)
3. UK Family Offices (wealth preservation, commercial traction, structured terms)
4. Investor Networks (UKBAA, AIN, F6S - committee & showcase applications)
5. Smart Match Platforms (algorithmic bio & syndicate blurbs)
Zero Cost, fully automated.
"""

from typing import Dict, Any

class OutreachEngine:
    def generate_pitch_package(
        self,
        company_name: str,
        sector: str,
        stage: str,
        target_raise: str,
        traction_highlights: str,
        founder_name: str,
        founder_title: str,
        vc_match: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Creates a custom 1-to-1 tailored outreach package for a specific VC partner.
        """
        partner_name = vc_match.get("lead_partner", "Partner")
        partner_first = partner_name.split()[0]
        fund_name = vc_match.get("fund_name", "the fund")
        portfolio = vc_match.get("portfolio", [])
        sample_port = portfolio[0] if portfolio else "category leaders"

        email_subject = f"{company_name} (£{target_raise} {stage}) - {fund_name}'s thesis in {sector}"
        
        email_body = f"""Hi {partner_first},

I've been following {fund_name}'s investments in scalable software, particularly your backing of {sample_port}. Given your focus on {vc_match.get('thesis', 'high-growth early stage tech')[:120]}..., I wanted to briefly share what we are building at {company_name}.

We are an early-stage {sector} startup in the Eupnea Accelerator cohort. 

Quick Highlights:
• Traction: {traction_highlights}
• Market Opportunity: Addressing high-demand workflow automation for enterprise and scale-up teams.
• Current Round: We are raising £{target_raise} {stage} capital to scale product distribution and expand market presence.

Would you be open to a 15-minute introductory conversation next Tuesday or Thursday? I'd love to share our deck and walk through our metrics.

Best regards,

{founder_name}
{founder_title}, {company_name}
Eupnea Accelerator Member
LinkedIn: https://linkedin.com/in/{founder_name.lower().replace(' ', '')}"""

        linkedin_note = (
            f"Hi {partner_first}, loved {fund_name}'s thesis backing {sample_port}. "
            f"We're building {company_name} ({sector}, Eupnea cohort) raising £{target_raise} {stage}. "
            f"Would love to connect and keep you posted on milestones!"
        )

        follow_up = f"""Hi {partner_first},

Following up on my note last week regarding {company_name}'s £{target_raise} {stage} round. 

We just closed new commercial momentum: {traction_highlights.split('.')[0] if '.' in traction_highlights else traction_highlights}. 

Given {fund_name}'s track record with {sample_port}, I'd value 10 minutes to share our deck and discuss if our thesis aligns.

Let me know if next week works for a brief intro call.

Warm regards,
{founder_name}"""

        return {
            "email_subject": email_subject,
            "email_body": email_body,
            "linkedin_note": linkedin_note,
            "follow_up_email": follow_up
        }

    def generate_angel_pitch_package(
        self,
        company_name: str,
        sector: str,
        stage: str,
        target_raise: str,
        traction_highlights: str,
        founder_name: str,
        founder_title: str,
        investor_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Creates bespoke pitch copy customized to the specific category:
        - UK Angel / Private Investor
        - UK Family Office
        - Investor Network
        - Smart Match Platform
        """
        cat = investor_data.get("category", "UK Angel / Private Investor")
        contact_name = investor_data.get("lead_contact", investor_data.get("name", "Investor"))
        first_name = contact_name.split()[0] if " " in contact_name else contact_name
        org_name = investor_data.get("name", "your syndicate")
        portfolio = investor_data.get("portfolio", [])
        sample_port = portfolio[0] if portfolio else "high-growth ventures"
        access_route = investor_data.get("access_route", "Direct Pitch")
        suitability_score = investor_data.get("suitability_score", 85)

        if "Angel" in cat:
            subject = f"{company_name} (SEIS/EIS | £{target_raise} {stage}) - Angel intro for {first_name}"
            email_body = f"""Hi {first_name},

I saw your impressive angel portfolio (particularly your backing of {sample_port}) and your focus on {sector} founders. Knowing your background as a hands-on operator, I wanted to reach out directly.

I'm the {founder_title} of {company_name}, currently in the Eupnea Accelerator cohort. We are raising £{target_raise} {stage} with full SEIS/EIS tax relief eligibility in place.

Why We Are Reaching Out:
• Product & Traction: {traction_highlights}
• Round Structure: Raising £{target_raise} with cheques from £15k - £100k+ welcomed to close out the round.
• Founder Fit: We value operator angels who have navigated zero-to-one scale.

Would you be open to reviewing our 10-slide deck or having a brief 10-minute coffee chat / call next week?

Warm regards,

{founder_name}
{founder_title}, {company_name}
Eupnea Accelerator Member
Email: {founder_name.lower().replace(' ', '.')}@{company_name.lower().replace(' ', '')}.com"""

            linkedin_note = (
                f"Hi {first_name}, admire your angel angel investments (e.g. {sample_port}). "
                f"Building {company_name} ({sector}, Eupnea cohort) raising £{target_raise} SEIS/EIS. "
                f"Would love to connect and share our brief deck if open!"
            )

            application_summary = f"""COMPANY: {company_name}
STAGE: {stage} (Eupnea Accelerator)
SECTOR: {sector}
ROUND: £{target_raise} (SEIS/EIS Advance Assurance Ready)
KEY TRACTION: {traction_highlights}
CONTACT: {founder_name} ({founder_title})"""

        elif "Family Office" in cat:
            subject = f"Direct Investment Brief: {company_name} (£{target_raise} {stage} Round) - {org_name}"
            email_body = f"""Dear {first_name} and Investment Committee,

I am writing on behalf of {company_name}, an early-stage {sector} startup in the Eupnea Accelerator cohort, to introduce our current £{target_raise} {stage} funding round.

We have followed {org_name}'s venture allocations, specifically your emphasis on disciplined early-stage technology companies with capital-efficient unit economics (including {sample_port}).

Executive Overview:
• Problem & Solution: Proprietary software solving high-value workflow inefficiencies for UK and international customers.
• Verified Traction: {traction_highlights}
• Allocation: Co-investing alongside reputable UK business angels and syndicates (£50k to £250k ticket capacity).
• Governance: Clean cap table, UK corporate structure, full SEIS/EIS eligibility.

We have established our Virtual Data Room (VDR) and executive summary. We would welcome the opportunity to submit our investment memorandum to your direct investments team.

Yours sincerely,

{founder_name}
{founder_title}, {company_name}
Eupnea Accelerator Cohort"""

            linkedin_note = (
                f"Dear {first_name}, reaching out regarding {company_name}'s £{target_raise} {stage} round. "
                f"We are an early-stage {sector} company (Eupnea cohort) with strong metrics: {traction_highlights[:70]}... "
                f"Would welcome connecting with {org_name}'s venture team."
            )

            application_summary = f"""FAMILY OFFICE DIRECT SUBMISSION:
Target Entity: {org_name}
Company: {company_name}
Sector: {sector} | Stage: {stage}
Target Raise: £{target_raise}
Key Metric: {traction_highlights}
Suitability Score: {suitability_score}% (Qualified)"""

        elif "Network" in cat:
            subject = f"Pitch Application: {company_name} (£{target_raise} {stage}) - {org_name}"
            email_body = f"""Dear {org_name} Screening Committee,

We are submitting {company_name} for presentation to the {org_name} investor membership for our current £{target_raise} {stage} syndicate round.

We are actively participating in the Eupnea Accelerator program and have structured our round to accommodate angel syndicates with £15k - £100k individual tickets.

Key Submission Details:
• Sector: {sector}
• Core Traction: {traction_highlights}
• Tax Relief: SEIS / EIS Advance Assurance obtained / pending.
• Next Milestone: Scaling commercial deployment and growing enterprise customer accounts.

We have completed our pitch deck and investor one-pager ready for the upcoming screening sift.

Best regards,

{founder_name}
{founder_title}, {company_name}
Phone / WhatsApp: +44 7700 900123
Route: {access_route}"""

            linkedin_note = (
                f"Hello {first_name}, submitting {company_name} for {org_name}'s investor showcase. "
                f"We are raising £{target_raise} {stage} in {sector} with strong early traction: {traction_highlights[:60]}... "
                f"Looking forward to engaging with the syndicate!"
            )

            application_summary = f"""PITCH SHOWCASE SIFT SUBMISSION:
Network: {org_name}
Channel: {access_route}
Company: {company_name}
Raise: £{target_raise} ({stage})
Elevator Pitch: {company_name} operates in {sector}, delivering: {traction_highlights}.
Presenter: {founder_name} ({founder_title})"""

        else: # Smart Match Platform
            subject = f"{company_name} Smart Match Profile - £{target_raise} {stage}"
            email_body = f"""Hi {org_name} Team,

We are updating our deal room on {org_name} for our upcoming £{target_raise} {stage} matching round.

Startup Profile:
• Name: {company_name} (Eupnea Accelerator)
• Sector: {sector}
• Stage: {stage}
• Raising: £{target_raise} (SEIS/EIS eligible)
• Traction: {traction_highlights}

We look forward to smart matching with aligned UK angels and micro-syndicates searching for high-growth {sector} opportunities.

Best regards,
{founder_name}"""

            linkedin_note = (
                f"Hi {first_name}, connecting regarding our active match listing on {org_name} for {company_name} (£{target_raise} {stage}). Excited to partner with your ecosystem!"
            )

            application_summary = f"""SMART MATCH ALGORITHM BIO:
Entity: {company_name}
Match Tag: {sector} | {stage} | UK Angel Syndicate
Raise: £{target_raise}
Traction Snippet: {traction_highlights}
Platform Target: {org_name} ({access_route})"""

        return {
            "email_subject": subject,
            "email_body": email_body,
            "linkedin_note": linkedin_note,
            "application_summary": application_summary,
            "access_route": access_route
        }
