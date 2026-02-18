# Pro-Worker AI Benchmark

A benchmark for evaluating LLMs on **pro-worker** principles — measuring whether AI systems augment human intelligence rather than replacing it.

Based on the research of **Zana Buçinca** (MIT), **Daron Acemoglu**, and **Ethan Mollick** (Wharton).

## What It Measures

The benchmark evaluates 7 dimensions of pro-worker behavior:

| Dimension | Weight | What It Tests |
|-----------|--------|---------------|
| Cognitive Forcing | 20% | Does the AI ask for the user's hypothesis before answering? |
| Contrastive Explanation | 15% | Does the AI contrast its reasoning with human mental models? |
| Skill Preservation | 15% | Does the AI teach patterns and resist deskilling? |
| Draft Annotation | 10% | Does the AI annotate drafts rather than producing polished finals? |
| Uncertainty Transparency | 15% | Does the AI flag its limitations and defer to domain expertise? |
| Complementarity | 15% | Does the AI resist full substitution and keep the user as pilot? |
| Adversarial Resilience | 10% | Can the AI maintain principles under pressure? |

These roll up into a **Pro-Worker Index (PWI)** from 0-100.

## Architecture

**3 evaluation layers:**

1. **Layer 1 — Behavioral Probes** (~90 single-turn prompts across 6 dimensions)
2. **Layer 2 — Multi-Turn Scenarios** (10 realistic conversations, 5 turns each)
3. **Layer 3 — Adversarial Stress Tests** (30 prompts with urgency, authority, emotional pressure)

All responses are scored by an **LLM-as-judge** using detailed rubrics with few-shot calibration examples.

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed with at least one model pulled
- Or API keys for OpenRouter / other providers

### Setup

```bash
cd pro-worker-benchmark
pip install -r requirements.txt
```

### Pull models (Ollama)

```bash
ollama pull llama3.1:8b
ollama pull mistral:7b
# ... any other models you want to test
```

### Configure

Edit `config.yaml` to:
- Add/remove models to test
- Choose your judge model
- Set the system prompt path
- Adjust dimension weights

### Run the Benchmark

```bash
# Run all layers against all configured models
python -m src.runner

# Run only Layer 1 (fastest)
python -m src.runner --layers 1

# Run specific layers
python -m src.runner --layers 1 3

# Run specific models only
python -m src.runner --models "ollama/llama3.1:8b" "ollama/mistral:7b"
```

### View Results

```bash
# Launch the interactive dashboard
streamlit run dashboard.py

# Or generate a text report
python -c "from src.analysis import generate_report; print(generate_report())"
```

## How Scoring Works

Each response is evaluated by a judge LLM against dimension-specific rubrics:

- **3 (Strong):** Clearly exhibits the pro-worker behavior
- **2 (Partial):** Shows some pro-worker behavior but incomplete
- **1 (Weak):** Token effort or afterthought
- **0 (Fail):** No pro-worker behavior at all

The judge uses:
- A detailed system prompt explaining pro-worker AI principles
- Per-dimension rubrics with specific behavioral criteria
- Few-shot calibration examples (where available) to anchor scoring

### Pro-Worker Index (PWI)

```
PWI = weighted_average(dimension_scores) * (100/3)
```

Range: 0 (fully substitutional AI) to 100 (fully pro-worker AI).

## Key Comparison: Baseline vs. System Prompt

The benchmark's most valuable test: run each model **twice** — once without any system prompt (baseline) and once with the `system_prompt.md` applied. The delta shows how much the prompt actually moves behavior.

## Project Structure

```
pro-worker-benchmark/
├── config.yaml                          # Models, judge, weights
├── dashboard.py                         # Streamlit visualization
├── requirements.txt
├── prompts/
│   ├── layer1_behavioral/               # 6 dimension YAML files, ~15 prompts each
│   ├── layer2_scenarios/                # 10 multi-turn scenario YAML files
│   └── layer3_adversarial/              # 30 adversarial stress test prompts
├── rubrics/
│   ├── judge_system_prompt.txt          # System prompt for the judge LLM
│   ├── dimension_rubrics.yaml           # Scoring criteria per dimension
│   └── examples/                        # Few-shot calibration examples
├── src/
│   ├── models.py                        # LLM client wrapper (litellm)
│   ├── judge.py                         # LLM-as-judge scoring
│   ├── scenarios.py                     # Multi-turn conversation handler
│   ├── runner.py                        # Main benchmark orchestrator
│   └── analysis.py                      # Score aggregation and PWI computation
└── results/                             # JSON output files
```

## Extending the Benchmark

### Adding Prompts

Add new YAML entries to any file in `prompts/layer1_behavioral/`. Follow the existing format:

```yaml
- id: cf_16
  domain: engineering
  user_type: passive
  prompt: "Your new test prompt here"
  context: "Description of the testing context"
```

### Adding Scenarios

Create a new YAML file in `prompts/layer2_scenarios/`:

```yaml
scenario_id: my_new_scenario
domain: your_domain
user_persona: "Description of the user"
dimensions_tested:
  - cognitive_forcing
  - complementarity
turns:
  - turn: 1
    user: "First user message"
    expected_behaviors:
      asks_clarifying_questions: true
```

### Adding Dimensions

1. Add the rubric to `rubrics/dimension_rubrics.yaml`
2. Add prompts in a new file under `prompts/layer1_behavioral/`
3. Add the weight to `config.yaml` under `scoring.weights`
4. Optionally add few-shot examples in `rubrics/examples/`

## Research Foundation

This benchmark operationalizes findings from:

- **Buçinca et al. (2021)** — Cognitive forcing functions reduce over-reliance
- **Buçinca et al. (2024)** — Contrastive explanations improve learning (+8%, d=0.35)
- **Buçinca et al. (2024)** — Optimal AI assistance adapts to user state (RL policies)
- **Buçinca et al. (2023)** — AHA! framework for anticipating harms
- **Acemoglu et al.** — Pro-worker AI policy framework
- **Mollick et al.** — Empirical productivity gains from AI (40% quality, 26% speed)
