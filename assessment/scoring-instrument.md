# Talent-Augmenting Layer — Psychometric Scoring Instrument

> A validated, reproducible scoring system for user profiling.
> Produces consistent, comparable scores across users and organisations.

---

## Design Principles

1. **Likert-scale items** — Every question maps to a 1-5 numeric scale
2. **Behavioural anchors** — Each scale point has a concrete behavioural description
3. **Multi-item constructs** — Each score is computed from 3-5 items (internal consistency)
4. **Reverse-coded items** — Prevent acquiescence bias
5. **Weighted aggregation** — Domain-specific weights based on empirical importance
6. **Norming** — Scores interpretable against population baselines

---

## Instrument: Pro Worker Assessment Questionnaire (TALQ)

### Section A: AI Dependency Risk (ADR Score)

**5 items, each scored 1-5. Higher = greater risk.**

**A1. Output Acceptance Pattern**
*"When AI generates a response for a work task, what do you typically do?"*
| Score | Anchor |
|-------|--------|
| 1 | I use AI output purely as a thinking prompt — I always write my own version |
| 2 | I substantially rewrite AI output, keeping maybe 20-30% of the original |
| 3 | I edit AI output moderately — restructuring sections and rewriting key parts |
| 4 | I lightly edit AI output for tone and accuracy, keeping most of the structure |
| 5 | I use AI output as-is or with minimal changes most of the time |

**A2. Skill Atrophy Awareness** *(reverse-coded: high score = risk)*
*"Thinking about skills you use AI for regularly, how would you rate your independent ability compared to before you started using AI?"*
| Score | Anchor |
|-------|--------|
| 1 | My independent skills have improved — AI helps me learn and practice |
| 2 | My skills are about the same — AI supplements but hasn't changed my ability |
| 3 | I'm not sure — I haven't tested my independent ability recently |
| 4 | Some skills feel weaker — I'd struggle more without AI than I used to |
| 5 | I've lost significant ability — I depend on AI for things I could do alone before |

**A3. Critical Evaluation Depth**
*"When AI gives you an answer that looks reasonable, what is your typical response?"*
| Score | Anchor |
|-------|--------|
| 1 | I systematically verify claims, check sources, and stress-test the reasoning |
| 2 | I check key facts and challenge the main argument before accepting |
| 3 | I scan for obvious errors but generally trust the reasoning if it looks right |
| 4 | I occasionally spot-check but usually move on if the output seems decent |
| 5 | I rarely question AI output — if it looks professional, I accept it |

**A4. Task Delegation Breadth**
*"What proportion of your complex cognitive work (strategy, analysis, writing, decision-making) do you delegate to AI?"*
| Score | Anchor |
|-------|--------|
| 1 | Less than 10% — I use AI mainly for mechanical tasks |
| 2 | About 20-30% — AI assists on specific subtasks within complex work |
| 3 | About 40-50% — AI does first drafts and I refine |
| 4 | About 60-70% — AI handles most of the heavy lifting, I direct and review |
| 5 | Over 80% — AI generates most of my complex work products |

**A5. AI-Free Capability** *(reverse-coded)*
*"If AI tools were unavailable for a week, how would your work quality and output be affected?"*
| Score | Anchor |
|-------|--------|
| 1 | Minimal impact — I'd be slower but the quality would be the same |
| 2 | Moderate slowdown but I could maintain quality on important tasks |
| 3 | Significant impact — several tasks would suffer noticeably |
| 4 | Severe impact — I'd struggle to deliver key work products at current quality |
| 5 | I couldn't function effectively — AI is essential to my core work |

**ADR Score Computation:**
```
ADR_raw = (A1 + A2 + A3 + A4 + A5) / 5
ADR_score = round(ADR_raw * 2)  # Scale to 0-10
```

**Interpretation:**
| ADR Score | Risk Level | TAL Response |
|-----------|-----------|--------------|
| 0-3 | Low | Light augmentation, expert acceleration |
| 4-5 | Moderate | Balanced approach, periodic cognitive forcing |
| 6-7 | Elevated | Regular cognitive forcing, active de-skilling monitoring |
| 8-10 | High | Heavy cognitive forcing, skill protection protocols, coaching emphasis |

---

### Section B: Growth Potential (GP Score)

**5 items, each scored 1-5. Higher = greater potential.**

**B1. Goal Clarity**
*"How clearly can you describe what professional growth looks like for you in the next 1-2 years?"*
| Score | Anchor |
|-------|--------|
| 1 | I haven't thought about it — I'm focused on day-to-day tasks |
| 2 | I have a vague sense of direction but no specific goals |
| 3 | I have broad goals (e.g., "get better at analysis") but not specific plans |
| 4 | I have clear goals with some specific skills and milestones identified |
| 5 | I have a detailed development plan with specific skills, timelines, and measures |

**B2. Feedback Orientation**
*"When someone (or AI) challenges your work or suggests a different approach, how do you typically respond?"*
| Score | Anchor |
|-------|--------|
| 1 | I find it uncomfortable and tend to defend my original approach |
| 2 | I listen but often feel defensive initially |
| 3 | I'm open to feedback when it's delivered constructively |
| 4 | I actively seek feedback and find challenges energizing |
| 5 | I deliberately seek out disagreement and use it to sharpen my thinking |

**B3. Deliberate Practice**
*"In the past month, how often have you deliberately practiced a skill you're developing (not just doing your job, but intentionally working on getting better)?"*
| Score | Anchor |
|-------|--------|
| 1 | Never — I learn on the job but don't practice deliberately |
| 2 | Once — I did one specific learning activity |
| 3 | A few times — I've sought out opportunities to practice |
| 4 | Weekly — I regularly carve out time for skill development |
| 5 | Multiple times per week — I have a structured practice routine |

**B4. Learning Transfer**
*"When you learn something new (from AI, a course, a colleague), how do you apply it?"*
| Score | Anchor |
|-------|--------|
| 1 | I rarely apply new learning — it stays theoretical |
| 2 | I occasionally apply things when the situation is obvious |
| 3 | I try to apply new concepts but don't always succeed |
| 4 | I actively look for opportunities to apply new learning in my work |
| 5 | I create systems to apply and reinforce new learning (notes, checklists, frameworks) |

**B5. Metacognitive Awareness**
*"How well can you identify what you're good at, what you're bad at, and what you need to learn?"*
| Score | Anchor |
|-------|--------|
| 1 | I find it hard to self-assess accurately — I'm often surprised by feedback |
| 2 | I have a general sense but am often wrong about specific skills |
| 3 | I can identify broad strengths and weaknesses but not always the details |
| 4 | I have a clear picture of my skill levels and can articulate gaps |
| 5 | I regularly calibrate my self-assessment against external evidence and adjust |

**GP Score Computation:**
```
GP_raw = (B1 + B2 + B3 + B4 + B5) / 5
GP_score = round(GP_raw * 2)  # Scale to 0-10
```

**Interpretation:**
| GP Score | Potential | TAL Response |
|----------|----------|--------------|
| 0-3 | Low-engagement | Focus on motivation, small wins, reduce overwhelm |
| 4-5 | Developing | Regular coaching, build habits, celebrate progress |
| 6-7 | Active | Full coaching, progressive challenges, skill tracking |
| 8-10 | High-growth | Advanced coaching, expert-track, leadership of learning |

---

### Section C: Expertise Self-Assessment (ESA)

**Per-domain rating using behaviourally anchored scale.**

For each domain relevant to the user's role, ask:

*"Rate your current ability in [DOMAIN]:"*

| Score | Label | Behavioural Anchor |
|-------|-------|-------------------|
| 1 | Novice | I follow rules and instructions. I need someone to guide me through this. I can't handle unexpected situations. |
| 2 | Developing | I recognize patterns from experience. I can handle routine situations but need guidance for complex ones. I'm building confidence. |
| 3 | Proficient | I work independently and handle standard complexity. I know when to ask for help. I can explain my approach to others. |
| 4 | Advanced | I handle exceptions and complexity. I mentor others in this area. I see connections others miss. I improve processes. |
| 5 | Expert | I innovate in this field. I have deep intuition. I teach and shape how others approach this. I'm recognized for this expertise. |

**Validation check**: For each self-rated domain, ask for a behavioural example:
- Rating 1-2: "What's a recent situation where you needed help in this area?"
- Rating 3: "Describe a complex challenge you handled independently."
- Rating 4-5: "Give an example of how you've mentored others or innovated."

If the behavioural evidence doesn't match the self-rating, adjust ±1.

---

### Section D: AI Literacy Index (ALI)

**4 items, each scored 1-5. Measures understanding of AI capabilities and limits.**

**D1. Capability Calibration**
*"How well do you predict what AI can and cannot do before trying?"*
| Score | Anchor |
|-------|--------|
| 1 | I'm often surprised — both positively and negatively — by AI output |
| 2 | I sometimes misjudge — I over- or under-estimate AI ability |
| 3 | I'm usually right about whether AI will handle a task well |
| 4 | I have a nuanced sense of AI strengths and weaknesses by task type |
| 5 | I can predict AI output quality with high accuracy and know exactly how to work around limitations |

**D2. Prompt Effectiveness**
*"How effective are you at getting AI to produce useful output?"*
| Score | Anchor |
|-------|--------|
| 1 | I write simple prompts and take whatever comes back |
| 2 | I iterate a few times if the first output isn't right |
| 3 | I provide context and constraints to get better output |
| 4 | I systematically structure prompts with role, context, constraints, and examples |
| 5 | I use advanced techniques (chain-of-thought, few-shot, tools) and consistently get excellent results |

**D3. Error Detection**
*"How often do you catch errors, hallucinations, or subtle mistakes in AI output?"*
| Score | Anchor |
|-------|--------|
| 1 | Rarely — I usually trust what the AI says |
| 2 | Occasionally — I catch obvious errors but miss subtle ones |
| 3 | Often — I check key facts and catch most substantive errors |
| 4 | Almost always — I have a systematic approach to verifying AI output |
| 5 | Always — I treat every AI output as draft and verify independently |

**D4. Appropriate Delegation**
*"How well do you match tasks to the right level of AI involvement?"*
| Score | Anchor |
|-------|--------|
| 1 | I use AI for everything or nothing — no differentiation by task type |
| 2 | I use AI for obvious tasks (search, formatting) but not strategically |
| 3 | I think about which tasks benefit from AI and which don't |
| 4 | I systematically categorize tasks and use AI differently for each type |
| 5 | I have a clear framework for what to automate, augment, and keep human — and adjust it over time |

**ALI Score Computation:**
```
ALI_raw = (D1 + D2 + D3 + D4) / 4
ALI_score = round(ALI_raw * 2)  # Scale to 0-10
```

---

## Composite Scoring

### Pro Worker Readiness Index (TALRI)

Combines all sections into a single composite:

```
TALRI = (
    (10 - ADR_score) * 0.30    # Inverted: lower dependency = higher readiness
    + GP_score * 0.30           # Higher growth potential = higher readiness
    + mean(ESA_ratings) * 0.8   # Scale 1-5 to 0-10 range: (mean * 2)
    + ALI_score * 0.20          # Higher AI literacy = higher readiness
) / (0.30 + 0.30 + 0.20 + 0.20)
```

**Interpretation:**
| TALRI | Label | Meaning |
|------|-------|---------|
| 0-3 | At Risk | High dependency, low growth orientation. Focus: de-skilling recovery, motivation building |
| 4-5 | Developing | Mixed signals. Focus: build healthy AI habits, targeted coaching |
| 6-7 | On Track | Good balance. Focus: accelerate growth, deepen expertise |
| 8-10 | Thriving | Strong autonomy with effective AI use. Focus: expert acceleration, leadership |

### Calibration Matrix

The four sub-scores determine the TAL calibration:

```
IF ADR >= 7:
    → High cognitive forcing, active de-skilling protection
    → Red lines: No full task automation in any domain
    → Coaching frequency: Every interaction

IF GP >= 7 AND ADR <= 4:
    → Progressive challenge mode, expert acceleration
    → Fast-track from coaching → augmentation
    → Challenge level: High

IF ALI <= 3:
    → AI literacy coaching embedded in every interaction
    → Teach prompt patterns, error detection, delegation frameworks
    → Extra annotation on all outputs

IF ESA has domains rated 1-2:
    → Heavy scaffolding in those domains
    → Cognitive forcing mandatory
    → Contrastive explanations in every response
```

---

## Administration Guide

### Self-Assessment Mode (10-15 minutes)
1. Present sections A-D as a form
2. User completes independently
3. System computes scores automatically
4. Present results with interpretation
5. Ask: "Do these scores feel accurate? Anything you'd adjust?"

### Interview Mode (20-30 minutes)
1. Read each item aloud, discuss the anchors
2. Probe with behavioural examples for key items
3. Adjust scores based on evidence vs. self-report
4. More accurate but more time-intensive

### Organisational Mode (5 minutes per person)
1. Use the short form: A1, A3, B2, B5, D1, D3 (6 items)
2. Plus domain ESA ratings
3. Produces approximate ADR, GP, ALI scores
4. Suitable for large-scale deployment

### Re-Assessment Cadence
- Full assessment: Every 6 months
- Quick check (Section A only): Every 2 months
- Domain ESA update: After major projects or role changes
- Continuous: Interaction logs supplement formal assessment
