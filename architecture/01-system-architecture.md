# 01 — System Architecture

## System context

```mermaid
flowchart TB
    C(["👤 Customer"])
    subgraph APP["Telco Support Chatbot (local PoC)"]
        UI["Streamlit UI"]
        BRAIN["Hub-and-spoke brain (Python)"]
        DATA[("Synthetic telco data<br/>JSON files")]
    end
    LLM["Local LLM · Ollama<br/>(optional)"]

    C -- "types queries<br/>(billing / offers)" --> UI
    UI -- "reply + live signals" --> C
    UI <--> BRAIN
    BRAIN <--> DATA
    BRAIN -. "rephrase reply<br/>(optional)" .-> LLM
```

Everything runs on one laptop. The only optional external process is **Ollama**
for LLM phrasing; if it is absent the app falls back to templates.

## Container / module view

```mermaid
flowchart TB
    subgraph UI_LAYER["Presentation — Streamlit"]
        LOGIN["Login + identity verify<br/>auth.py"]
        CHAT["Chat + signal panel + KPIs"]
    end

    subgraph BRAIN_LAYER["Application — hub-and-spoke brain"]
        CO["Coordinator (HUB)"]
        NLU["NLU pipeline (M3)"]
        POL["Policy engine"]
        FLOWS["Flows: billing / offers / retention"]
        REC["Recommendation engine"]
        RL["RL bandit (M5)"]
        NLG["NLG + LLM provider (M4)"]
        STATE["ConversationState"]
    end

    subgraph DATA_LAYER["Data & config (M1)"]
        JSON[("synthetic_telco.json<br/>synthetic_tickets.json")]
        ENV[".env (LLM provider)"]
        MODELS[("Trained models<br/>*.joblib")]
        SESS[("Session logs + rl_policy.json")]
    end

    CHAT --> CO
    CO --> NLU --> MODELS
    CO --> POL
    CO --> FLOWS --> REC --> RL --> SESS
    CO --> NLG --> ENV
    CO --> STATE --> SESS
    FLOWS --> JSON
    LOGIN --> JSON
```

## Layer responsibilities

| Layer | Responsibility | Key files |
| --- | --- | --- |
| **Presentation** | Auth, chat rendering, live signal panel, KPIs, feedback | `ui/streamlit_app.py`, `app/auth.py` |
| **Application (brain)** | Per-turn understanding, routing, dialogue flows, recommendations, response generation | `app/coordinator.py`, `app/flows/*`, `app/nlu/*`, `app/nlg/*`, `app/policy_engine.py`, `app/recommendation_engine.py`, `app/rl/*` |
| **Data & config** | Synthetic data, trained models, provider config, durable logs | `data/*.json`, `app/nlu/models/*.joblib`, `.env`, `data/sessions/*` |

## Tech stack

| Concern | Choice | Why (PoC) |
| --- | --- | --- |
| UI | **Streamlit** (`st.chat_message` / `st.chat_input`) | One command, one language, real chat UI, easy to record |
| NLU | **scikit-learn MLPClassifier** on TF-IDF | Neural NLU that trains in seconds on CPU, no GPU/heavy deps |
| NLG | Templates + **Ollama** local LLM (pluggable) | Grounded, offline, no API key; provider swap via `.env` |
| RL | Epsilon-greedy **bandit** (JSON-persisted) | Simple, explainable feedback loop |
| Data | **JSON files** | No DB to stand up; fully self-contained |
| Config | **.env** (`python-dotenv`) | `LLM_PROVIDER=ollama\|template\|openai\|anthropic` |

## Design principles

- **Thick brain, thin UI** — all logic lives in `app/`; the UI only renders.
- **Deterministic core, optional LLM** — facts (bills, charges, offers) come
  from data + rules; the LLM only rephrases, so it cannot hallucinate numbers.
- **Grounded fallback everywhere** — no trained model → keyword intent; no
  LLM → template text. The demo never hard-fails.
- **Everything observable** — every turn emits intent/sentiment/spoke/latency/
  resolution signals that the UI and KPI panel display.
