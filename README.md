```markdown
# GEO-Reddit-Agent | Human-in-the-Loop AI Search Optimization

Status: Private Repository | Reddit API Compliance Review  
Purpose: Generative Engine Optimization (GEO) research & human-approved content drafting  
Compliance: Fully aligned with Reddit's Responsible Builder Policy & Developer Terms  

## Overview
GEO-Reddit-Agent is a human-in-the-loop Python workflow designed to help small businesses and marketers improve visibility in AI-powered search (ChatGPT, Perplexity, Gemini, Bing Copilot) by sharing structured, data-backed, and community-aligned insights on Reddit.

The system reads public subreddit discussions, drafts GEO-optimized responses, and queues them for manual review. Zero automated posting. Every outbound action requires explicit human approval before submission via PRAW.

## How It Works
1. Read-Only Monitoring: Scans public posts/comments for commercial intent signals. No user data is stored, sold, or used for ad targeting.
2. AI Drafting: Generates Q&A-style, citation-friendly drafts aligned with E-E-A-T and GEO best practices.
3. Human Approval Gate: All drafts land in a local JSON queue + CLI/dashboard. Nothing is published without explicit operator approval.
4. Compliance & Rate Check: Validates subreddit rules, flair requirements, and enforces hard rate limits (max 3 posts/day, 5 comments/day, 0 unsolicited DMs).
5. Publish & Track: Submits via PRAW with randomized delays (3–6 min). Logs engagement, AI citation pickup, and full audit trails.

## Compliance & Safety Features
| Policy Requirement | Implementation |
|--------------------|----------------|
| Human Approval | All posts/comments/DMs require explicit operator approval. Zero automated publishing. |
| Bot Transparency | All outbound content includes: "AI-assisted by [Name] | GEO Specialist". Bot profile clearly discloses purpose. |
| Rate Limits | Hard-coded caps: 3 posts/day, 5 comments/day. Randomized 3–6 min delays. PRAW backoff respected. |
| No Spam/Cross-Posting | Unique drafts per thread. No identical/substantially similar content across subreddits. |
| Subreddit Rules | Pre-publish check parses sidebar/rules, flair requirements, and self-promo policies. Skips non-compliant targets. |
| Data Handling | Read-only access to public content. No data resale, no AI training, no user profiling, no re-identification. |
| Audit Logging | Every approval, rejection, publish, and rate-limit event is timestamped and stored locally for review. |
| Devvit Incompatibility | Requires external Python orchestration (PRAW + OpenClaw + LLM API), local approval UI, CRM sync, and persistent session management. Devvit's serverless runtime does not support this architecture. |

## Tech Stack
- Orchestrator: OpenClaw (local gateway, human-in-the-loop exec approvals)
- Reddit API: PRAW (OAuth2 script type, read-heavy, rate-limited)
- AI Drafting: OpenAI/Anthropic API (GEO-optimized Q&A, schema, citations)
- Approval UI: Flask dashboard + CLI queue (`approval_queue.json`)
- Runtime: Python 3.11, Ubuntu LTS, systemd service, loopback gateway
- Logging: Local JSON audit trails, redacted outputs, no cloud sync

## Setup (Review-Only)
```bash
git clone <repository-url>
cd geo-reddit-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill with sandbox/test credentials only
python3 openclaw_wrapper.py status
```
> 🔒 Production credentials are never committed. The `.env` file is gitignored. Reviewers can request read-only access to a sandbox branch with test tokens.

## Reddit API Compliance Statement
This workflow fully complies with Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy):
- ✅ Approval Required: Explicit written request submitted via Reddit's developer form. No API usage prior to approval.
- ✅ Transparent Purpose: GEO research & human-approved content drafting for AI search visibility. No masking, no multi-account abuse.
- ✅ Respect Limits: PRAW OAuth2, hard rate caps, randomized delays, zero circumvention of API or network limits.
- ✅ Bot Transparency: Clear disclosure in profile & signatures. Explicit user consent required for any private communication.
- ✅ Prohibited Activities: Zero vote manipulation, zero spam, zero cross-posting, zero safety mechanism circumvention.
- ✅ No Unapproved Commercialization/AI Training: Public data used only for contextual drafting. No resale, no sharing, no ML training, no ad targeting.
- ✅ Privacy & Security: No sensitive data inference, no re-identification, no de-anonymization. Local-only storage, redacted logs, tight filesystem permissions.

## Review Access
- This repository is private by default.
- Reddit review team can request read-only access via email or GitHub collaborator invite.
- A sandbox branch with test credentials and mock subreddit targets is available upon request.
- Full audit logs, rate-limit configs, and approval queue samples can be provided for compliance verification.

## Contact
- Operator: Dyogo Ortega
- Email: dyogoho@gmail.com
- Reddit Account: u/Encryptedx00x
- Purpose: Commercial API access for human-approved GEO content & lead research.

---
© 2024 GEO-Reddit-Agent. Built for compliance, transparency, and community-aligned AI search optimization.
```
