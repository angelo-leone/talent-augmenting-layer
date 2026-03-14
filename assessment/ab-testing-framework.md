# Talent-Augmenting Layer — A/B Testing & Measurement Framework

> Does TAL actually work? This framework measures user outcomes.
> What makes this publishable AND sellable.

---

## What We Need to Prove

### Primary Hypotheses

**H1: TAL reduces AI dependency risk**
- Users with TAL profiles have lower dependency risk scores over time than control group
- Measured: ADR score trajectory (scoring-instrument.md Section A)

**H2: TAL improves skill development**
- Users coached by TAL show faster expertise growth than uncoached users
- Measured: ESA ratings over time (scoring-instrument.md Section C)

**H3: TAL prevents de-skilling**
- Protected skills show stable or improving ratings; unprotected skills don't decline faster
- Measured: Before/after ESA ratings for protected vs. unprotected domains

**H4: TAL improves AI literacy**
- Users with TAL calibration develop stronger AI usage patterns
- Measured: ALI score trajectory (scoring-instrument.md Section D)

**H5: TAL improves work output quality**
- Work products created with TAL are rated higher by blind reviewers
- Measured: Quality ratings by independent evaluators

---

## Study Design

### Design 1: Within-Subjects (Single Organisation)

**Setup**: All participants assessed at T0. Half get TAL (treatment), half use standard AI (control). Reassess at T1 (3 months) and T2 (6 months).

```
Timeline:
  T0 (Week 0)     → Full TALQ assessment for ALL participants
  T0-T1            → Treatment: TAL active | Control: Standard AI use
  T1 (Month 3)     → Re-assess ALL participants (TALQ + ESA)
  T1-T2            → Continue same conditions
  T2 (Month 6)     → Final assessment + qualitative interviews
  T2+              → Optional crossover: Control gets TAL
```

**Sample size**: Minimum 30 per group (power analysis for d=0.35 effect, the Bucinca contrastive explanation effect size, at alpha=0.05 and power=0.80).

**Randomization**: Stratify by role and initial expertise level to balance groups.

### Design 2: Across-Organisations (Marketplace Deployment)

**Setup**: Organisation A adopts TAL; Organisation B (matched sector/size) serves as control. Natural experiment design.

**Matching criteria**: Sector, org size, AI tool availability, average tenure, baseline AI usage.

**Advantage**: Ecological validity — real organisational contexts.
**Risk**: Many confounders. Address with propensity score matching.

### Design 3: Time-Series (Self-Control)

**Setup**: Each user serves as their own control. Measure before TAL adoption, then track trajectory after.

```
Phase 1 (Weeks 1-4):    Baseline — standard AI use, log interactions
Phase 2 (Weeks 5-8):    TAL activated — track all metrics
Phase 3 (Weeks 9-12):   TAL continued — observe adaptation and growth
Phase 4 (Week 13):      TAL removed — test skill retention
```

**Advantage**: Controls for individual differences.
**Risk**: Order effects, maturation effects. Address with interrupted time-series analysis.

---

## Measurement Instruments

### Quantitative Measures

| Measure | Instrument | Frequency | Source |
|---------|-----------|-----------|--------|
| AI Dependency Risk | TALQ Section A (5 items) | Monthly | Self-report |
| Growth Potential | TALQ Section B (5 items) | Monthly | Self-report |
| Expertise Ratings | TALQ Section C (per domain) | Monthly | Self-report + behavioural evidence |
| AI Literacy | TALQ Section D (4 items) | Monthly | Self-report |
| Interaction Patterns | MCP interaction logs | Continuous | System data |
| Engagement Quality | MCP engagement level logs | Continuous | System data |
| Skill Signals | MCP growth/atrophy logs | Continuous | System data |

### Behavioural Measures (from interaction logs)

| Metric | Computation | What It Shows |
|--------|------------|---------------|
| **Passive ratio** | passive_interactions / total_interactions | Over-reliance tendency |
| **Hypothesis-first rate** | interactions_where_user_proposed_first / coach_interactions | Cognitive engagement |
| **Revision depth** | avg(user_edits_to_AI_output) | Critical evaluation |
| **Domain progression** | domains_moving_coach→augment / total_coached_domains | Skill growth velocity |
| **Friction acceptance** | completed_challenges / offered_challenges | Learning orientation |
| **Independence rate** | tasks_completed_without_AI / total_tasks_in_coached_domains | Skill confidence |

### Qualitative Measures

| Method | Timing | Questions |
|--------|--------|-----------|
| Semi-structured interview | T1, T2 | "How has your AI usage changed? What skills feel stronger/weaker? Do you notice the friction? Is it helpful or annoying?" |
| Work sample analysis | T0, T1, T2 | Blind rating of matched work products (same task type, with/without TAL) |
| Manager assessment | T1, T2 | "Has this person's work quality/independence changed? How?" |

---

## Analysis Plan

### Primary Analyses

**H1-H4**: Mixed-effects linear models
```
score ~ time * condition + (1|participant)
```
- Fixed effects: time (T0/T1/T2), condition (TAL/control), interaction
- Random intercept per participant
- Key test: significant time × condition interaction

**H5**: Independent samples t-test on blind quality ratings
```
quality_rating ~ condition
```

### Secondary Analyses

**Moderation**: Does initial expertise level moderate TAL effectiveness?
```
score ~ time * condition * baseline_expertise + (1|participant)
```

**Dose-response**: Does more interaction with TAL = bigger effect?
```
delta_score ~ total_interactions + coaching_frequency + friction_acceptance
```

**Domain-specific**: Which domains show the largest effects?
```
For each domain: domain_score ~ time * condition + (1|participant)
```

### Interaction Log Analyses

**Time-series**: Plot weekly passive ratio, hypothesis-first rate, independence rate
```
For each participant:
  - Fit trend line to weekly metrics
  - Compare slopes between TAL and control groups
  - Test for structural breaks at TAL activation
```

**Sequence analysis**: Do interaction patterns change over time?
```
Markov chain analysis:
  - Model transition probabilities: automate→augment→coach→protect
  - Test whether TAL users show more "upward" transitions
```

---

## Success Criteria

### Minimum Viable Evidence (for publication)

| Hypothesis | Effect Size | p-value | Evidence Level |
|-----------|-------------|---------|----------------|
| H1: Reduced dependency | d ≥ 0.25 | p < 0.05 | Medium |
| H2: Faster skill growth | d ≥ 0.30 | p < 0.05 | Medium |
| H3: Prevented de-skilling | d ≥ 0.20 | p < 0.05 | Small-medium |
| H4: Improved AI literacy | d ≥ 0.25 | p < 0.05 | Medium |
| H5: Better work quality | d ≥ 0.35 | p < 0.05 | Medium |

### Business Case Metrics (for marketplace)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to competence | 20% faster | Weeks from onboarding to proficient rating |
| AI tool ROI | 15% higher | Productivity gains WITH TAL vs. standard AI |
| Skill retention | 30% better | Post-AI-removal performance |
| Employee satisfaction | +10 NPS | Survey comparison |
| De-skilling incidents | 50% fewer | Atrophy warning count comparison |

---

## Implementation in the MCP Server

The MCP server already captures the data needed for most analyses:

```python
# Each interaction is logged with:
talent_log_interaction(
    name="Angelo",
    task_category="coach",        # → task distribution
    domain="economic_analysis",   # → domain-specific tracking
    engagement_level="active",    # → passive ratio computation
    skill_signal="growth",        # → growth/atrophy signals
    notes="User identified counterfactual independently"
)

# Progression analysis available via:
talent_get_progression(name="Angelo")
# Returns: weekly trends, domain signals, atrophy warnings, trend direction

# Org summary for group comparisons:
talent_org_summary()
# Returns: aggregated stats across all profiles
```

**To add**: Systematic before/after TALQ scores stored in profile change log.

---

## Ethical Considerations

1. **Informed consent**: All participants must understand what's being measured
2. **No performance evaluation**: TAL data must NOT be used for performance reviews
3. **Anonymization**: Org-level dashboards show aggregated data only
4. **Right to withdraw**: Participants can delete their profile at any time
5. **No deception**: Control group knows they're in a study (but not the specific hypothesis)
6. **Data ownership**: Workers own their profiles; org sees only aggregates
