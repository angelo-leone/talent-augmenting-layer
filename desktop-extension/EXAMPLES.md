# Talent-Augmenting Layer — Usage Examples

These examples demonstrate the core workflows of the Talent-Augmenting Layer desktop extension.

---

## Example 1: Onboarding Assessment

**User prompt:**
> "I'd like to set up my Talent-Augmenting Layer profile. My name is Sarah."

**What happens:**
1. Claude calls `talent_assess_start` with name "Sarah"
2. The tool returns the full assessment protocol with questions and behavioural anchors
3. Claude walks Sarah through the assessment conversationally, asking one question at a time:
   - Dependency risk questions (how critically she evaluates AI output)
   - Growth potential questions (learning goals, feedback orientation)
   - AI literacy questions (understanding of AI capabilities and limits)
   - Expertise self-assessment across her professional domains
   - Task classification (what to automate vs. coach vs. protect)
4. Claude calls `talent_assess_score` with the collected answers
5. Claude calls `talent_assess_create_profile` to generate and save the profile

**Expected output (from `talent_assess_score`):**
```json
{
  "scores": {
    "ADR": { "raw": 3.2, "interpretation": "Moderate dependency risk" },
    "GP": { "raw": 4.1, "interpretation": "High growth potential" },
    "ALI": { "raw": 3.8, "interpretation": "Good AI literacy" },
    "ESA": { "mean": 3.4, "spread": 1.2 },
    "TALRI": { "composite": 62, "interpretation": "Balanced profile — augmentation-ready with coaching in growth areas" }
  },
  "recommended_calibration": {
    "default_friction_level": "medium",
    "cognitive_forcing_domains": ["Strategic planning", "Stakeholder communication"],
    "automation_permitted_domains": ["Data formatting", "Meeting scheduling"]
  }
}
```

---

## Example 2: Task Classification During Work

**User prompt:**
> "Help me write a board presentation about our Q1 results."

**What happens:**
1. Claude calls `talent_classify_task` with the task description
2. Based on Sarah's profile, the tool returns the classification and recommended AI behaviour

**Expected output:**
```json
{
  "task": "Write a board presentation about Q1 results",
  "classification": "coach",
  "reason": "Matches coaching domain: 'Strategic communication'. User rated this domain 2/5 (developing) and flagged it as a growth area.",
  "recommended_behaviour": {
    "mode": "Cognitive Forcing + Coaching",
    "approach": [
      "Ask for the user's initial outline before offering suggestions",
      "Provide frameworks for structuring board presentations",
      "Offer contrastive explanations for communication choices",
      "Review and give feedback rather than writing the full presentation"
    ],
    "friction_level": "medium-high"
  }
}
```

**Claude's response to the user (following the classification):**
> "Before I help with the presentation, what's your initial thinking on the structure? What are the 3-4 key messages you want the board to walk away with? This will help me give you more targeted feedback."

---

## Example 3: Skill Progression Check

**User prompt:**
> "How am I progressing with my skills? Any areas I should watch out for?"

**What happens:**
1. Claude calls `talent_status` with Sarah's name
2. The tool returns a comprehensive report combining profile, calibration, and progression data

**Expected output:**
```json
{
  "profile_summary": {
    "name": "Sarah",
    "role": "Product Manager",
    "TALRI_score": 62,
    "domains_count": 6,
    "last_updated": "2026-03-15"
  },
  "progression": {
    "total_interactions": 47,
    "trend_direction": "improving",
    "domain_signals": {
      "Strategic planning": { "growth": 5, "stable": 3, "atrophy": 0, "direction": "growing" },
      "Data analysis": { "growth": 2, "stable": 8, "atrophy": 1, "direction": "stable" },
      "Technical writing": { "growth": 0, "stable": 1, "atrophy": 4, "direction": "declining" }
    },
    "atrophy_warnings": [
      "Technical writing: 4 atrophy signals detected. This is a protected skill — consider practicing it independently."
    ],
    "engagement_pattern": {
      "passive": 12,
      "active": 25,
      "critical": 10,
      "passive_ratio": 0.26
    }
  },
  "recommendations": [
    "Strong growth in Strategic planning — consider moving from 'coach' to 'augment' mode",
    "Technical writing shows atrophy risk — try a skill refresh exercise",
    "Overall engagement is healthy (74% active/critical)"
  ]
}
```

---

## Example 4: Profile-Aware Expert Augmentation

**User prompt:**
> "Review this SQL query for performance issues" (with a complex query pasted)

**What happens:**
1. Claude calls `talent_classify_task` — returns "augment" because Sarah rated "Data analysis" as 4/5 (advanced)
2. Claude skips basics and jumps straight to edge cases:

**Claude's response:**
> "Two things stand out. First, the subquery on line 12 will cause a full table scan on `orders` — consider rewriting it as a CTE with a date filter pushed down. Second, the LEFT JOIN to `user_preferences` is likely unnecessary here since you're filtering on it in the WHERE clause anyway, which converts it to an INNER JOIN. Have you checked the execution plan? The estimated cost difference could be significant with your table sizes."

3. After the interaction, Claude calls `talent_log_interaction` to record:
   - task_category: "augment"
   - domain: "Data analysis"
   - engagement_level: "critical" (Sarah pushed back on one suggestion)
   - skill_signal: "stable"

---

## Example 5: De-skilling Detection

**User prompt (third time in one session):**
> "Just write the project status email for me."

**What happens:**
1. Claude detects this is the 3rd delegation of "writing" tasks in the session without Sarah offering her own attempt
2. Claude calls `talent_classify_task` — returns "protect" because writing is in Sarah's protected skills list
3. Claude applies the Anti-Autopilot Protocol:

**Claude's response:**
> "I've been writing a few things for you today. Since written communication is one of the skills you flagged as important to maintain, let me flip this one — give me your draft of the key points, and I'll help you refine it. What are the three most important updates the team needs to hear?"
