"""M3 NLU — unified pipeline. Turns raw user text into a single structured
`TurnFrame` (intent + sentiment + entities) that the coordinator/flows consume.
This is the fusion step from the reference 'thick brain' design."""
from dataclasses import dataclass, field
from . import intent_model, sentiment_model, entities


@dataclass
class TurnFrame:
    text: str
    intent: str
    intent_conf: float
    sentiment: str            # POS / NEU / NEG
    sentiment_score: float    # -1..1
    sentiment_intensity: float
    entities: dict = field(default_factory=dict)


def understand(text: str) -> TurnFrame:
    intent, conf = intent_model.classify(text)
    label, score, intensity = sentiment_model.analyze(text)
    ents = entities.extract(text)
    return TurnFrame(
        text=text, intent=intent, intent_conf=round(conf, 2),
        sentiment=label, sentiment_score=score, sentiment_intensity=intensity,
        entities=ents,
    )
