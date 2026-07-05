"""M4 NLG — pluggable LLM provider, selected via .env (LLM_PROVIDER).

  ollama    -> local model over HTTP (default; best for the offline demo)
  template  -> no LLM, caller uses the deterministic template text as-is
  openai    -> hosted OpenAI  (enable later; set OPENAI_API_KEY)
  anthropic -> hosted Anthropic (enable later; set ANTHROPIC_API_KEY)

Every provider is best-effort: if the LLM is unreachable or errors, we return
None and the generator falls back to the deterministic template so the demo
never breaks."""
import requests
from .. import config


def available():
    """Is an actual LLM configured (not pure-template mode)?"""
    return config.LLM_PROVIDER in ("ollama", "openai", "anthropic")


def status():
    p = config.LLM_PROVIDER
    if p == "ollama":
        return f"ollama · {config.OLLAMA_MODEL}"
    if p == "openai":
        return f"openai · {config.OPENAI_MODEL}"
    if p == "anthropic":
        return f"anthropic · {config.ANTHROPIC_MODEL}"
    return "template (no LLM)"


def generate(system: str, user: str, timeout=20):
    """Return polished text, or None to signal 'use the template'."""
    p = config.LLM_PROVIDER
    try:
        if p == "ollama":
            return _ollama(system, user, timeout)
        if p == "openai":
            return _openai(system, user, timeout)
        if p == "anthropic":
            return _anthropic(system, user, timeout)
    except Exception:
        return None      # any failure -> template fallback
    return None


def _ollama(system, user, timeout):
    r = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _openai(system, user, timeout):
    if not config.OPENAI_API_KEY:
        return None
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def _anthropic(system, user, timeout):
    if not config.ANTHROPIC_API_KEY:
        return None
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()
