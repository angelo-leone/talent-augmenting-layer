# TAOS launch plan

Public launch roadmap. Living document — re-read at the start of every session, tick items as they ship.

---

## Where we are today

**Shipped infrastructure**:

- Hosted web app at `proworker-hosted.onrender.com` with Google OAuth, assessment, dashboard, multi-format export.
- Remote MCP server at `proworker-hosted.onrender.com/mcp` with OAuth, ambient instructions (gated by `MCP_SEND_INSTRUCTIONS`), DB-backed `HostedProfileStore` for authenticated users.
- Four install paths live in the landing: Cowork (marketplace), Claude Code, Claude Chat, ChatGPT (Developer mode), Codex, Gemini (paste-in), Others.
- Two plugin variants in the GitHub marketplace: `TAOS` for everything-not-Claude-Code, `TAOS for Claude Code` for the plugin-with-hooks experience.
- Web-based quick-update flow (`/profile/update`) mirrors the `/talent-update` MCP skill.
- Pilot data validates the thesis: NPS +13 over standard AI, cognitive forcing rated 4/5 unanimous, 4 of 6 say employer should adopt.

**Not yet shipped, blocking launch**:

- Pricing page wired to billing.
- Paddle (or Stripe + Stripe Tax) integration in the `ENABLE_BILLING=false` scaffold.
- Trial onboarding flow (sign-up → assessment → connector → first session).
- In-app trial countdown + email reminders.
- Submission to Anthropic Cowork marketplace.
- Submission to ChatGPT Apps directory.
- A public-launch artifact (pilot writeup as a Substack post).

---

## Pricing decision

**Tier:** £10 / user / month, single tier at launch. Defensible against the pilot exit data (median band £6-15, two of six in £16-30, median £10) and against comparables (Notion AI £8-10, ChatGPT Plus £20). Risk: signals "cheap" rather than "valuable". Counterweight: low price reduces the trial-conversion barrier and we want compounding profile data, which needs sticky users more than high ARPU at v1.

**Revisit point:** After 90 days of paid users, look at conversion rate. If trial → paid > 5%, test £15. If < 2%, hold the price and focus on value demonstration.

**Trial mechanics:** 30-day free trial, **no credit card required**. Trade-off: lower conversion. Mitigation: aggressive but humane in-app countdown, three reminder emails, graceful degradation on day 31 (read-only profile, no edits) so users return rather than disappear.

**Cancellation:** one-click from `/account`, no friend-asking, no dark patterns. Builds the trust the product is selling.

**Refunds:** automate via Paddle dashboard. Single human review threshold (>£30 charge) before processing. Below that, refund + email reply same day.

---

## Billing stack decision

**Use Paddle, not Stripe directly.** Paddle as merchant of record handles:

- VAT MOSS for EU customers (the real bureaucracy bear).
- US sales tax across nexus states.
- Invoicing and receipts.
- Card chargeback handling.

Stripe + Stripe Tax is the alternative but you would still be merchant of record for invoicing and customer-of-record purposes. At sub-£90k revenue, Paddle's ~5% cut buys back weeks of admin per year. Switching merchants later is more painful than picking the right one now.

**Sequence:**

1. Sign up for Paddle, get the sandbox keys.
2. Wire the `ENABLE_BILLING=true` scaffold to Paddle's API (currently stubbed for Stripe; needs an adapter).
3. Add Paddle's checkout overlay to the pricing page.
4. Test end-to-end: trial sign-up → 30-day trigger → charge → access continues.
5. Switch to live Paddle keys for launch.

---

## UK-bureaucracy sequence

Mirror "only do this when revenue justifies":

| Trigger | Action |
|---|---|
| Now (any revenue) | Sole trader / self-employed. Register with HMRC for Self Assessment. |
| Any revenue | Use Paddle (merchant of record) so VAT MOSS is handled. No personal VAT registration needed. |
| Approaching £90k turnover | Register for VAT in the UK. |
| Approaching £50k annual revenue | Talk to an accountant about incorporating as a Ltd company (tax efficiency, liability separation). |
| Any time you handle GDPR data | The hosted app already does (Privacy Policy, audit log, account export, delete). Stays good. |

---

## Pre-launch checklist (target: 4 weeks from today)

Order is dependency-aware. Tick items as they ship.

### Week 1: billing and trial

- [ ] Paddle account + sandbox API keys.
- [ ] Adapt `hosted/billing.py` to Paddle's API (currently stubbed against Stripe).
- [ ] Wire the pricing page (`hosted/templates/pricing.html`) to Paddle checkout.
- [ ] Sign-up flow: Google login → assessment → "Start 30-day free trial" → connector → first session. End-to-end smoke test.
- [ ] User table: `trial_started_at`, `trial_status` ("active", "expired", "converted", "cancelled") columns.
- [ ] Cron / scheduler: day 23, 28, 30, 31 events fire from the existing scheduler.

### Week 2: emails and countdown

- [ ] Wire the seven email templates in `emails/` into `hosted/email_service.py`.
- [ ] Pick the final subject line for each from the draft alternates.
- [ ] In-app banner on the dashboard showing days-remaining during trial.
- [ ] Cancellation route `/account/cancel` with one-click confirm and a "what happens to my data" explainer.
- [ ] Read-only mode at day 31: profile is viewable and exportable but `/profile/update` and MCP write tools return a friendly "trial expired, upgrade to continue updating" response.

### Week 3: polish and marketplace prep

- [ ] Pricing page copy refresh (lead with the trial, not the price).
- [ ] Landing page CTA above the fold: "Try free for 30 days. No credit card."
- [ ] Public privacy / terms of service review (already drafted; needs a legal sense-check at the trial-payment intersection).
- [ ] Anthropic Cowork marketplace submission: prepare description, screenshots, demo video, partner-application form.
- [ ] ChatGPT Apps directory submission: prepare manifest, screenshots, OAuth scopes, demo recording.

### Week 4: launch artifact

- [ ] Substack post: "What we learned shipping a coaching AI to 10 pilot users". Lead with the headline pilot numbers; show the cognitive-forcing protocol; honest about the friction-tax finding.
- [ ] LinkedIn cross-post.
- [ ] Twitter / X thread with the pilot stats.
- [ ] Producthunt? (Decide closer to date. ProductHunt is noisy for serious B2B but credible for personal-use SaaS.)
- [ ] Outreach list: 30 people in the senior-IC / consultant / creator network for a private launch ping the day before public.

---

## Launch week

Day 0:

- [ ] Flip `ENABLE_BILLING=true` and `MCP_SEND_INSTRUCTIONS=true` on production.
- [ ] Verify Render deploy succeeds on the live blueprint.
- [ ] Sanity-test the pricing flow end-to-end with a test card.
- [ ] Send the launch Substack at 9am UK time.
- [ ] Cross-post to LinkedIn, X.
- [ ] Email the private launch list.

Days 1-7:

- [ ] Respond to every sign-up. Personal welcome from Angelo, not a template, for the first ~50 users.
- [ ] Track funnel: landing visits → sign-up → assessment complete → connector added → first coaching turn.
- [ ] Daily review of audit log + Render error rate.
- [ ] First Discord / community channel? Decide.

---

## Post-launch growth (weeks 5 to 12)

**Distribution channels, in order of leverage:**

1. **Anthropic Cowork marketplace listing.** The single highest-leverage channel because the audience is exactly your buyer and Anthropic actively promotes partner plugins. Goal: be listed within 4 weeks of launch. Submission via [their developer program](https://www.anthropic.com/partners) or via direct outreach to devrel.

2. **Solita conversion.** Per `CLAUDE.md`, the Director of Strategy has asked for a wider deployment conversation. Sign Solita pre- or just-post-launch. A signed enterprise contract is the strongest external validation.

3. **Pilot writeup as content.** The Substack on day 0 is the spike; turn it into a series. Topics: cognitive forcing, the friction-tax finding, the discoverability crisis, what coaching looks like when it actually works.

4. **LinkedIn + targeted outbound** to senior IC / consultant / creator personas. Cold-but-warm: people you've personally engaged with TAOS-relevant content. Aim for 5 to 10 outbound messages per week.

5. **Anthropic ecosystem visibility.** Anthropic developer Discord, devrel relationships, partner Slack. TAOS is built on Anthropic's stack; this is compounding distribution.

6. **ChatGPT Apps directory.** Lower priority than Anthropic because OpenAI's Apps SDK approval is slower and less promotional, but worth submitting because (a) it's free and (b) it signals legitimacy.

7. **Reddit / niche forums** (`r/ClaudeAI`, `r/ChatGPT`, `r/SaaS`, etc.). Useful for hard-skeptical-power-user feedback but low conversion. Worth a thread at launch then occasional engagement, not a primary channel.

**Content cadence:** one Substack post every 2 weeks for the first 12 weeks. Topics drawn from the pilot data, the de-skilling research base (Bastani PNAS 2025, Mollick HBS/BCG 2023, Kosmyna MIT 2025), and what you observe in production.

---

## Anthropic Cowork marketplace submission

**Goal:** get TAOS into the official `claude.com/plugins` directory under "Personal" or as a partner-built plugin.

**Materials needed:**

- Plugin name, tagline, description (≤ 200 chars).
- Three screenshots (assessment in progress, dashboard, coaching session in Cowork).
- Demo video (≤ 90 seconds): user runs assessment, gets profile, asks for coaching.
- The GitHub repo URL (`https://github.com/angelo-leone/talent-augmenting-layer`).
- The marketplace.json manifest (already shipped at `.claude-plugin/marketplace.json`).
- Author / company info.

**Submission path (best guess; may shift):**

- Direct contact via [Anthropic partners form](https://www.anthropic.com/partners). Pitch as a productivity plugin with research-backed pedagogy.
- Or: post the marketplace.json + repo on Anthropic's developer Discord and ask for inclusion review.

**Approval criteria (inferred):** safety review, OAuth implementation, terms of service, no surprising data flows.

---

## ChatGPT Apps directory submission

**Goal:** become a verified ChatGPT App so users discover TAOS through ChatGPT's Apps surface.

**Materials needed:**

- App manifest matching OpenAI's Apps SDK spec.
- Privacy policy URL (have it: `proworker-hosted.onrender.com/privacy`).
- Terms of service.
- OAuth scopes.
- Demo video.
- Description, category (productivity), tagline.

**Submission path:**

- OpenAI developer console → Apps → New App → submit for review.
- Review takes 2 to 6 weeks per OpenAI's docs.

**Approval criteria (per OpenAI docs):**

- App must be useful beyond a single prompt.
- Clear data-handling story.
- OAuth conformance.
- No use of ChatGPT branding except as documented.

---

## Email cadence

Drafts live in `emails/`. Each file has a YAML frontmatter (`subject`, `send_after_days`, `audience`) and the body in Markdown. Pick one subject per email from the alternates before wiring to `email_service.py`.

| File | When | Audience | Purpose |
|---|---|---|---|
| `emails/01-welcome.md` | T+0 (sign-up) | Every new user | Onboarding nudge: complete assessment + pick a client |
| `emails/02-day-7-checkin.md` | T+7 days | Trial users | Gentle: how is the coach? |
| `emails/03-day-23-nudge.md` | T+23 days | Trial users | "Week ahead in the experiment" |
| `emails/04-day-28-reminder.md` | T+28 days | Trial users | Two days left + upgrade CTA |
| `emails/05-day-30-last-chance.md` | T+30 days | Trial users | Final-day prompt |
| `emails/06-day-31-readonly.md` | T+31 days | Lapsed trial users | "Your coach is paused" |
| `emails/07-cancelled.md` | On cancellation | Cancelling users | Confirm + data control |

---

## Open questions / decisions still to make

- **Discord or no Discord?** Community has compounding value but operational cost. Defer until ~500 paid users? Or start at launch on the back of the Substack audience?
- **Free tier or trial-only?** Trial-only is cleaner. A perpetual free tier may help discovery but cannibalises conversion. Default: trial-only at launch, reconsider at 90 days.
- **Annual plan?** £100/year (≈ 17% discount). Worth adding to the pricing page if Paddle integration supports it cleanly. Decide week 3.
- **Team plan?** Multiple seats with org-admin controls (already half-built in `hosted/org_service.py`). Defer to v1.1; needs the line-manager-controls design call that has already been deferred.
- **Profile portability between providers?** A user who builds their profile on ChatGPT then switches to Cowork — does their profile move? Today: yes if they signed in via the OAuth flow on both, the hosted profile is shared. Need to test and document.

---

## Reminders for cold-pickup

- Run `python3 cowork-plugin/_build_skills.py` after editing `plugin/tal-system-prompt.md` or any `cowork-plugin/protocols/*.md` to regenerate the Cowork skill files.
- Render auto-deploys from `main`. After pushing, wait 30 to 60 seconds for the cold start.
- The legacy "Worker-Augmenting Layer" blueprint on Render is orphaned and emails on every push; detach or delete it (see `docs/RENDER_CONSOLIDATION.md`).
- `MCP_SEND_INSTRUCTIONS` stays `false` until pilot is fully closed; flip on the Render dashboard, no redeploy needed.
- Per-pilot user impact analysis already done — most active pilot users are unaffected by code changes since the OAuth path is opt-in.
