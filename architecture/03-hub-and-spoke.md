# 03 — Hub-and-Spoke Multi-Agent Design

Two **AI** agents (spokes) never talk to each other; a **coordinator (hub)**
moves control between them. There is **no human handoff** in this PoC.

```mermaid
flowchart LR
    C(["👤 Customer"]) <--> HUB

    subgraph HUB["HUB — Coordinator (coordinator.py)"]
        direction TB
        H1["NLU → policy → route → NLG"]
        H2["Handoff trigger detection"]
    end

    HUB <--> A
    HUB <--> R

    subgraph A["Spoke 1 — Aria (billing spoke)"]
        A1["UC-01 Billing dispute<br/>flows/billing_flow.py"]
        A2["UC-02 Offers<br/>flows/offers_flow.py"]
    end

    subgraph R["Spoke 2 — Ray (retention spoke)"]
        R1["Negotiation ladder<br/>flows/retention_flow.py"]
    end

    A -. "never directly" .-x R
```

| | Aria (billing spoke) | Ray (retention spoke) |
| --- | --- | --- |
| Persona | Front-line billing & offers assistant | Senior retention specialist |
| Handles | UC-01 dispute, UC-02 offers, ticket status | Negotiation ladder, goodwill/exec credits |
| Entry | Default spoke at session start | Only via a hub handoff |
| Powers | Provisional credit / waiver / ticket | Extra offers + **simulated** supervisor approval |

## Handoff triggers (billing → retention)

Evaluated in `coordinator._detect_handoff`. Only fires while on the billing spoke.

```mermaid
flowchart TD
    T["Turn on billing spoke"] --> C1{"flow requested handoff?<br/>(e.g. offers_exhausted,<br/>voice_cannot_resolve)"}
    C1 -- yes --> DO["Swap to retention"]
    C1 -- no --> C2{"intent = HUMAN_HANDOFF?"}
    C2 -- yes --> DO
    C2 -- no --> C3{"intent = HAGGLE?"}
    C3 -- yes --> DO
    C3 -- no --> C4{"directive.escalate<br/>AND ≥ 2 turns?"}
    C4 -- yes --> DO
    C4 -- no --> STAY["Stay on billing"]

    DO --> INTRO["Ray: bridge line + first ladder pitch<br/>(one turn)"]
```

| Reason tag | Source |
| --- | --- |
| `offers_exhausted` | offers flow ran out of eligible offers |
| `voice_cannot_resolve` | billing flow can't authorize a needed credit |
| `customer_requested` | intent `HUMAN_HANDOFF` |
| `haggle` | intent `HAGGLE` |
| `negative_sentiment` | `directive.escalate` (irate / declining) after ≥2 turns |

On handoff the hub sets `active_spoke="retention"`, records
`escalation_flags += ["handoff:<reason>"]`, and produces Ray's opening line +
first offer in a single turn (`coordinator._retention_intro`).

## UC-01 — Billing dispute state machine (`billing_flow.py`)

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> await_validate: BILL_EXPLAIN / BILL_DISPUTE (surface the odd charge)
    await_validate --> await_resolution_choice: FACTUAL_DISPUTE / BILL_DISPUTE (present evidence + options)
    await_resolution_choice --> resolved: accept credit/waiver → billing.apply_credit
    await_resolution_choice --> resolved: choose ticket → ticketing.create_dispute
    await_resolution_choice --> [*]: needs specialist → request_handoff
    resolved --> [*]
```

Resolution options depend on tier (`data/synthetic_telco.json → dispute_policies`):
GOLD/SILVER get an auto **provisional credit**; a BRONZE **overage** gets a
one-time **50% goodwill waiver**; otherwise the flow requests a handoff.

## UC-02 — Offers state machine (`offers_flow.py`)

```mermaid
stateDiagram-v2
    [*] --> pitch: PROMO_INQUIRY
    pitch --> await_decision: recommend top eligible offer
    await_decision --> resolved: CONFIRM_YES → apply_offer (RL reward +1)
    await_decision --> pitch: CONFIRM_NO → next offer (RL reward 0)
    await_decision --> [*]: no offers left → request_handoff
    resolved --> [*]
```

## Retention ladder (`retention_flow.py`)

```mermaid
stateDiagram-v2
    [*] --> intro: hub handoff
    intro --> pitch_r0: best eligible offer (generous framing)
    pitch_r0 --> resolved: accept → apply (simulated approval)
    pitch_r0 --> pitch_r1: decline → next offer
    pitch_r1 --> resolved: accept
    pitch_r1 --> pitch_r2: decline → stack $15 goodwill credit
    pitch_r2 --> resolved: accept
    pitch_r2 --> pitch_r3: decline → $25 executive credit
    pitch_r3 --> resolved: accept
    pitch_r3 --> closed: decline → graceful close, offers held open (NO human handoff)
    resolved --> [*]
    closed --> [*]
```

Every acceptance is applied behind a **simulated supervisor approval**
(`approval: SIMULATED` on the action record) — no email workflow in this PoC.
