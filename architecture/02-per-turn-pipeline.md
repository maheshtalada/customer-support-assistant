# 02 — Per-turn Pipeline

Every customer message is processed by the same deterministic pipeline inside
`coordinator.handle_turn(state, text)`. This is the "thick brain" — the UI does
none of it.

## Pipeline (flow)

```mermaid
flowchart TD
    A["Customer message (text)"] --> B["NLU pipeline<br/>nlu/pipeline.understand()"]

    subgraph NLU["Parallel understanding (M3)"]
        B1["Intent — MLP<br/>intent_model.classify()"]
        B2["Sentiment — MLP<br/>sentiment_model.analyze()"]
        B3["Entities — regex<br/>entities.extract()"]
    end
    B --> B1 & B2 & B3
    B1 & B2 & B3 --> F["Fuse → TurnFrame"]

    F --> P["Policy engine<br/>→ Directive(tone, escalate, rule)"]
    P --> R{"Active spoke?"}

    R -- billing --> RB["Route: UC-01 billing / UC-02 offers"]
    RB --> H{"Handoff trigger?"}
    H -- no --> G
    H -- yes --> SW["Swap spoke → retention<br/>+ specialist intro & first pitch"]
    SW --> G

    R -- retention --> RR["Retention ladder<br/>retention_flow.handle()"]
    RR --> G["NLG compose<br/>nlg/generator.compose()"]

    G --> L{"LLM configured & reachable?"}
    L -- yes --> L1["Local LLM rephrases template<br/>(grounded, no new facts)"]
    L -- no --> L2["Use template verbatim"]
    L1 & L2 --> O["Reply + signals + action"]
    O --> REC["state.record(): trajectories, turn log"]
    REC --> UI["Return to UI"]
```

## Sequence (with objects)

```mermaid
sequenceDiagram
    participant U as Customer
    participant UI as Streamlit
    participant CO as Coordinator (HUB)
    participant NLU as NLU pipeline
    participant POL as Policy engine
    participant SP as Active spoke flow
    participant REC as Recommendation+RL
    participant NLG as NLG/LLM
    participant ST as ConversationState

    U->>UI: message
    UI->>CO: handle_turn(state, text)
    CO->>NLU: understand(text)
    NLU-->>CO: TurnFrame(intent, sentiment, entities)
    CO->>POL: evaluate(frame, state)
    POL-->>CO: Directive(tone, escalate, rule)
    CO->>CO: detect_handoff? (may swap spoke)
    CO->>SP: handle(state, frame)
    SP->>REC: recommend(cust)  %% offers/retention only
    REC-->>SP: ranked offers (RL-reweighted)
    SP-->>CO: {template, facts, offer_cards, action}
    CO->>NLG: compose(persona, template, facts, directive)
    NLG-->>CO: reply text (LLM or template)
    CO->>ST: record(frame, response, latency)
    CO-->>UI: response + live signals
    UI-->>U: reply + updated signal panel
```

## Steps in detail

| # | Step | Code | Output |
| --- | --- | --- | --- |
| 1 | **Understand** — intent + sentiment + entities, fused | `nlu/pipeline.py` | `TurnFrame` |
| 2 | **Policy** — deterministic tone/escalation rules | `policy_engine.py` | `Directive` |
| 3 | **Handoff check** — should the hub swap billing→retention? | `coordinator._detect_handoff` | reason tag or `None` |
| 4 | **Route** — pick UC-01 / UC-02 / retention ladder, advancing any active flow | `coordinator._route_billing`, `flows/*` | flow response dict |
| 5 | **Recommend** — score eligible offers, RL re-weight | `recommendation_engine.py` + `rl/bandit.py` | ranked offers |
| 6 | **Generate** — template, optionally LLM-rephrased | `nlg/generator.py`, `nlg/llm_provider.py` | reply text |
| 7 | **Record** — update trajectories + append turn log | `conversation_state.py` | updated state |

### The `TurnFrame` (fusion object)

```python
TurnFrame(
    text, intent, intent_conf,
    sentiment, sentiment_score,  # -1..1
    sentiment_intensity,         # 0..1
    entities,                    # {charge_ids, offer_ids, dispute_topic, affirmation}
)
```

### The `Directive` (policy output)

```python
Directive(tone, empathy, escalate: bool, rule)
# rules: irate_customer | sentiment_declining | positive_promo |
#        factual_dispute | default
```

Latency for each turn is measured in `handle_turn` and stored on the turn log,
feeding the average-latency KPI (objective #5).
