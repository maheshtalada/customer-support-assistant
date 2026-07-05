# Milestone Progress Reports

Ready-to-paste text for each milestone's "Describe this milestone's progress"
box, with the suggested file to upload.

---

## Milestone 1 — Data Collection
Collected and structured a synthetic telecom customer-support dataset covering 3
representative customers (GOLD/SILVER/BRONZE tiers) with their bills, line-item
charges (including disputable roaming and overage charges with evidence), payment
history, usage history, interaction history, a catalogue of 4 promotional offers,
tier-based dispute policies, and a dispute-ticket store. All data is centralized
behind a single access layer (`app/data_store.py`) so the chatbot reads accounts,
bills, offers and tickets consistently. No real customer data is used.

**Upload:** `data/synthetic_telco.json`

---

## Milestone 2 — Data Preparation
Prepared a labeled corpus for supervised NLU: hand-labeled utterances mapped to
14 intent classes (bill explain, bill dispute, factual dispute, promo inquiry,
confirm yes/no, haggle, create ticket, ticket status, payment query, etc.) and a
3-class sentiment set (POS/NEU/NEG). Implemented a shared text-preprocessing step
(lowercasing, contraction expansion, punctuation cleanup while preserving `$` and
`%`) applied identically at training and inference time.

**Upload:** `app/nlu/dataset.py`

---

## Milestone 3 — Develop NLU Model
Built the deep-learning NLU pipeline: a TF-IDF + Multi-Layer-Perceptron (neural
network) intent classifier and a second MLP for sentiment analysis, plus
rule-based entity extraction (charge IDs, amounts, dispute topic, yes/no).
Signals are fused into a single per-turn frame consumed by the dialogue engine,
with a keyword fallback for low-confidence inputs. Evaluated on a held-out split:
sentiment ~83% accuracy, intent ~62% (limited by the compact PoC seed corpus).
Metrics reproducible via `python evaluate.py`.

**Upload:** `docs/milestones/nlu_evaluation.txt`

---

## Milestone 4 — Create NLG Module
Implemented response generation with grounded templates that carry the correct
account facts, optionally rephrased into natural, human-like language by a local
LLM (Ollama · llama3.2). The provider is pluggable via `.env`
(ollama / template / openai / anthropic) with automatic fallback to templates if
the LLM is unavailable. The LLM is constrained to never invent numbers, charges
or offers, keeping every reply factually grounded.

**Upload:** `docs/demo/demo_llm.mp4`

---

## Milestone 5 — Optimize with Reinforcement Learning
Added an epsilon-greedy reinforcement-learning bandit that learns which offers
customers actually accept. Each offer is an arm tracking shows/accepts; the
learned acceptance value is blended into the deterministic recommendation score
so better-performing offers rise over time. Rewards come from a live feedback
loop (accept/decline and thumbs up/down), and the policy persists across sessions.

**Upload:** `app/rl/bandit.py`

---

## Milestone 6 — Deployment & Monitoring
Deployed the chatbot as a runnable Streamlit web app (welcome → login → identity
verification → chat) with a hub-and-spoke multi-agent brain. Added live
monitoring: per-turn intent/sentiment/active-agent signals, an RL learning table,
and KPI aggregation (resolution rate, latency, CSAT proxy) from persisted session
logs. Verified end-to-end with automated tests and screen-recorded demos.

**Upload:** `docs/demo/demo.mp4` (or `docs/screenshots/07-handoff-retention.png`)
