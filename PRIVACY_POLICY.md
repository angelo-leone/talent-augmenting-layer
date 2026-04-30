# Privacy Policy

**Talent-Augmenting OS (TAOS)**
Last updated: 2026-04-30
Effective: 2026-04-30

---

## 1. Why this document exists, and how to read it

TAOS is not a single product. It ships through several distinct channels, and the way your data is handled depends entirely on **which channel you use**. This policy describes each channel separately. If a section is not relevant to how you installed TAOS, you can ignore it.

The three channels are:

- **A. Local install** (Claude Code plugin, Claude Desktop Extension, stdio MCP server, universal system prompt pasted into another LLM). Everything runs on your own machine.
- **B. Hosted web app** at `https://proworker-hosted.onrender.com`. Browser-based, requires a Google sign-in, runs on infrastructure operated by the Licensor.
- **C. Remote MCP endpoint** at `https://proworker-hosted.onrender.com/mcp`. The same hosted infrastructure as B, but accessed by an MCP client over OAuth 2.1.

In all three cases, the **content of any conversation with the LLM (the actual reasoning model)** is governed by the LLM provider's privacy policy, not this one. TAOS's privacy posture covers the data we control: your profile, your assessment results, your interaction logs, and your account.

---

## 2. Who we are (Data Controller)

For Channels B and C (the hosted services), the Data Controller under GDPR is:

> Angelo Leone
> Email: `angelo.leone1204@gmail.com`
> GitHub issues: <https://github.com/angelo-leone/talent-augmenting-layer/issues>

For Channel A (local install), there is no controller other than yourself. TAOS running on your own machine processes your own data; we have no access to it.

---

## 3. Channel A: Local install

If you run the universal system prompt, the Custom GPT / Gemini Gem / Claude Project, the stdio MCP server, the Claude Desktop Extension, or the Claude Cowork plugin **without using the hosted app or remote MCP endpoint**:

### What is stored

- **Profile files**: `~/.talent-augmenting-layer/profiles/pro-*.md` (or in the repo's `profiles/` directory if you cloned the repo). Markdown, human-readable, editable by you.
- **Interaction logs**: JSONL files alongside the profiles, recording task category, domain, engagement level, and skill signal.
- **Assessment session state**: a transient JSON file while an assessment is in progress.

### What is NOT collected

- No data is transmitted from your machine to the Licensor.
- No telemetry, analytics, or usage tracking.
- No API keys or secrets are stored or read by TAOS.
- No cookies, fingerprinting, or device identifiers.

### Your data stays where you put it

The local channel is data-sovereign by construction. Use the `talent_delete_profile` MCP tool, or simply delete the files, to remove your data.

### Important caveat about the LLM you use

The LLM you connect TAOS to (Claude, ChatGPT, Gemini, Cursor, Codex, etc.) sees your conversation and is governed by **that vendor's** privacy policy, not this one. TAOS does not change that. If you are subject to a corporate "no customer data to LLM training" requirement, configure your LLM tier accordingly (most paid tiers exclude training).

---

## 4. Channel B: Hosted web app

If you sign in at `https://proworker-hosted.onrender.com`:

### Personal data we collect and store

| Category | Source | Why we store it | Retention |
| --- | --- | --- | --- |
| Email address, name, profile picture URL | Google OAuth on sign-in | Authenticate you, send check-in reminders, identify you in the org admin dashboard | Until you delete your account |
| Google subject ID (`google_id`) | Google OAuth | Stable identifier to recognise repeat sign-ins | Until you delete your account |
| Assessment conversation transcript | You typing into the assessment chat | Score the assessment, generate your profile | Until you delete your account or 24 months from creation, whichever comes first |
| Profile content (markdown, scores, calibration) | Generated from your assessment | Provide the personalisation TAOS exists to provide | Until you delete your account |
| Interaction telemetry (`<tal_log>` blocks): task category, domain, engagement level, skill signal, session id | Logged from your conversations with the LLM | Compute progression and atrophy signals shown in your dashboard | 24 months rolling, then aggregated |
| Check-in survey responses | You answering the 2-week reminder | Track skill growth/atrophy over time | Until you delete your account |
| Per-turn assessment latency (`latency_ms`) | Server-side timing | Diagnose performance issues | 90 days rolling |
| Organisation membership and role | Set by you or by your org admin | Multi-tenancy: scope analytics to your org | Until you leave or delete your account |
| OAuth audit data for the remote MCP endpoint (token jti, expiry, client) | OAuth 2.1 flow | Required for token revocation and security investigation | 90 days after token expiry |

### What we do NOT store

- We do not store passwords; sign-in is delegated to Google.
- We do not store payment information unless you sign up for a paid tier (Stripe is the processor; we store only a customer ID and subscription status). At time of writing, billing is feature-flagged off.
- We do not log full LLM prompts or LLM outputs to disk by default. Only the **structured telemetry** in `<tal_log>` blocks is persisted.

### Lawful basis (GDPR)

- **Contract**: storing your profile and assessment results is necessary to provide the service you signed up for (Article 6(1)(b)).
- **Legitimate interest**: aggregate, anonymised analytics for service improvement (Article 6(1)(f)). You can opt out by deleting your account.
- **Consent**: optional pilot telemetry export to Google Drive (Article 6(1)(a)). Off by default; you can withdraw consent at any time.

### Subprocessors

The hosted app uses the following third-party processors. By using the hosted app you consent to data transfer to these processors. We will publish prior notice of any change to this list.

| Subprocessor | Purpose | Data shared | Region |
| --- | --- | --- | --- |
| Render, Inc. | Application hosting and managed PostgreSQL | All persisted data listed above | US (default region; EU region available on request) |
| Google LLC (OAuth 2.0) | Authentication only | Email, name, profile picture URL, Google subject ID | Global |
| Google LLC (Gemini API) | Powers the conversational assessment | Assessment turn content during the assessment session | Global; "no-train" enforced via paid API tier |
| SendGrid (Twilio Inc.), optional | Sends 2-week check-in reminder emails and org-invite emails | Email address, user name, reminder content | US |
| Google LLC (Drive API), optional | Anonymised pilot telemetry export | De-identified aggregated metrics; never email or name | Global |
| Stripe, Inc., optional and feature-flagged off at time of writing | Subscription billing if you sign up for a paid tier | Email, billing details, subscription state | US, EU |

### Data residency

The default Render region is US-East. For pilot or commercial customers with an EU residency requirement, we can deploy a separate instance in Render's EU region (Frankfurt). Contact `angelo.leone1204@gmail.com` to request EU residency before signing up.

### Retention and deletion

You can delete your account and all associated data through the dashboard, or by emailing `angelo.leone1204@gmail.com` with the subject "DELETE my TAOS account". On deletion we hard-delete: user row, profile rows, assessment sessions, chat logs, check-in reminders, OAuth tokens, and any pilot survey responses. Aggregated, fully anonymised analytics may persist beyond deletion.

We will respond to deletion requests within 30 days and confirm completion in writing.

---

## 5. Channel C: Remote MCP endpoint

If you use an MCP client (Claude Desktop, Claude Code, Cursor, Codex CLI, etc.) configured to point at `https://proworker-hosted.onrender.com/mcp`:

The data handling is identical to Channel B (the hosted web app). The MCP endpoint is the same FastAPI service, the same PostgreSQL database, the same OAuth flow. The only difference is the access surface.

Additional considerations specific to the remote MCP channel:

- **OAuth 2.1 + PKCE.** Your MCP client performs an OAuth handshake against Google; we issue access tokens (JWTs) that are required for every tool call. Tokens are short-lived; refresh tokens are stored encrypted at rest in PostgreSQL.
- **No persistent connections.** The endpoint uses Streamable HTTP, not long-lived sessions, so there is no idle connection holding state about you.
- **CORS allow-list.** The MCP endpoint accepts cross-origin requests from any origin to support browser-based MCP clients; this does not weaken authentication, which is still required.
- **Rate limiting and audit logging** apply to MCP requests on the same basis as the hosted web app.

---

## 6. Pilot programmes

If you are a participant in a research pilot run with TAOS (e.g. Solita, Vanguard):

- Your participation is governed by a **separate Participant Information Sheet** that the pilot operator provides at consent time. That document specifies the additional data collected, the lawful basis, and your withdrawal rights for the pilot.
- Pilot-specific tables (`pilot_surveys`, `chat_logs` with elevated detail) are populated only during the pilot window.
- Pilot data may be exported to Google Drive in **fully anonymised** form (no email, no name, no Google subject ID) for academic or operational analysis. This export is opt-in at the pilot level; ask the pilot operator if you are unsure.
- Pilot data is deleted, or fully anonymised and aggregated, within 90 days of pilot completion.

---

## 7. Your rights (GDPR and equivalents)

Regardless of channel, where applicable law gives you the following rights, you can exercise them by emailing `angelo.leone1204@gmail.com`:

- **Access**: receive a copy of all personal data we hold about you.
- **Rectification**: correct inaccurate data.
- **Erasure** ("right to be forgotten"): delete your account and all associated data.
- **Restriction**: ask us to stop processing while a complaint is investigated.
- **Portability**: receive your profile and interaction logs in machine-readable form (we will export markdown + JSON).
- **Objection**: object to processing based on legitimate interest.
- **Withdrawal of consent** for any consent-based processing (e.g. pilot telemetry export).
- **Complaint**: lodge a complaint with your supervisory authority. For EU residents, this is your national Data Protection Authority. For UK residents, the ICO.

We respond to subject-access requests within 30 days.

---

## 8. Data security

We apply the following technical and organisational measures:

- **Encryption in transit**: TLS 1.2+ on all hosted endpoints.
- **Encryption at rest**: Render's managed PostgreSQL encrypts data at rest; access keys are managed by the platform.
- **Authentication**: Google OAuth for end users; OAuth 2.1 + PKCE for remote MCP clients.
- **Access control**: only the Licensor (and explicitly designated personnel, currently none) has administrative access to the production database.
- **Secret management**: production secrets are held in Render environment variables, not in source control.
- **Dependency scanning**: GitHub Dependabot is enabled on the source repository.
- **Audit logging**: administrative actions on the hosted service are logged; the audit log is available to organisation admins for actions on their own org.
- **Incident response**: in the event of a personal-data breach, we will notify affected users and supervisory authorities within 72 hours where required by GDPR Article 33.

We do not currently hold a SOC 2 or ISO 27001 certificate. We are in the process of building a SOC 2 readiness programme and expect to pursue Type I attestation in the next 6 to 12 months. Up-to-date status is available on request.

---

## 9. Children

TAOS is not directed at children under 16. We do not knowingly collect data from minors. If you believe a child has signed in, contact us and we will delete the account.

---

## 10. International data transfers

Where the hosted app processes personal data outside the EU, we rely on the European Commission's Standard Contractual Clauses with the relevant subprocessor (Google, Render, SendGrid, Stripe). Where we have offered EU data residency to a specific customer, transfers outside the EU are minimised to the operationally necessary minimum (e.g. Google OAuth metadata).

---

## 11. Changes to this policy

We will publish material changes to this policy at the same URL with an updated "Last updated" date and, where the change affects how we process your data, send a notification to the email address on file at least 30 days before the change takes effect. Continued use after the effective date constitutes acceptance.

---

## 12. Contact

`angelo.leone1204@gmail.com` for any privacy question, subject-access request, or DPA enquiry. For commercial-licensing or security-questionnaire questions, see also `COMMERCIAL.md` and the security section of the README.
