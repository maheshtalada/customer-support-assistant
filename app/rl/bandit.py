"""M5 Reinforcement Learning — a lightweight epsilon-greedy bandit that learns
which offers customers actually accept, and nudges the recommendation ranking
accordingly. This is the 'continuous improvement from feedback loops' objective.

Reward model (per offer arm):
  accept  -> reward 1     decline -> reward 0
We track a running value estimate Q(offer) = accepts / shows and blend it into
the deterministic score. Policy persists to data/rl_policy.json so learning
survives restarts (visible in the demo across sessions)."""
import json
from .. import config

_EPSILON = 0.10          # exploration rate
_BLEND = 0.30            # how much learned value shifts the base score


def _load():
    if config.RL_POLICY_PATH.exists():
        return json.loads(config.RL_POLICY_PATH.read_text())
    return {}


def _save(policy):
    config.RL_POLICY_PATH.write_text(json.dumps(policy, indent=2))


def _q(policy, offer_id):
    arm = policy.get(offer_id, {"shows": 0, "accepts": 0})
    shows = arm["shows"]
    return arm["accepts"] / shows if shows else 0.5   # optimistic prior


def adjust_score(offer_id, base_score):
    """Blend the learned acceptance value into the deterministic base score."""
    policy = _load()
    q = _q(policy, offer_id)
    return (1 - _BLEND) * base_score + _BLEND * q


def record_show(offer_id):
    policy = _load()
    arm = policy.setdefault(offer_id, {"shows": 0, "accepts": 0})
    arm["shows"] += 1
    _save(policy)


def record_reward(offer_id, accepted: bool):
    """Feedback loop: update the arm when a customer accepts/declines."""
    policy = _load()
    arm = policy.setdefault(offer_id, {"shows": 0, "accepts": 0})
    if accepted:
        arm["accepts"] += 1
    _save(policy)


def should_explore():
    """Epsilon-greedy: occasionally surface a non-top offer to keep learning.
    Deterministic-ish for the PoC (no RNG import needed at call sites)."""
    import random
    return random.random() < _EPSILON


def snapshot():
    """For the monitoring panel: current learned acceptance rates."""
    policy = _load()
    return {oid: {"shows": a["shows"], "accepts": a["accepts"],
                  "q": round(a["accepts"] / a["shows"], 2) if a["shows"] else None}
            for oid, a in policy.items()}
