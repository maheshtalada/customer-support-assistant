"""M4 NLG — response generation. The flows always produce a deterministic
`template` string plus structured `facts`. If an LLM provider is configured, we
ask it to *rephrase the template in the persona's voice without adding facts*;
otherwise we return the template verbatim. This keeps replies grounded (no
hallucinated numbers) while allowing human-like phrasing — the NLG objective."""
from . import llm_provider

_PERSONA_STYLE = {
    "Aria": "a warm, concise telecom billing & offers assistant",
    "Ray": "a calm, senior retention specialist who resolves tough cases",
}


def compose(persona, template, facts=None, directive=None, use_llm=True):
    """Return the final reply text."""
    if not (use_llm and llm_provider.available()):
        return template

    style = _PERSONA_STYLE.get(persona, "a helpful support agent")
    tone = f" Keep a {directive.tone} tone." if directive else ""
    system = (
        f"You are {persona}, {style}, speaking TO the customer. Rephrase the "
        f"agent message below into a natural, friendly, 1-2 sentence reply.{tone} "
        "Speak in the second person ('you', 'your') as the support agent — NEVER "
        "speak as the customer or in the first person about the customer's account. "
        "Keep it as a reply the agent says to the customer. Do NOT invent any "
        "numbers, dates, charges, offers or facts not already in the message. "
        "Do not add greetings if none is present. Return only the reply text."
    )
    fact_block = ""
    if facts:
        fact_block = "\nGrounded facts (do not contradict):\n" + \
            "\n".join(f"- {k}: {v}" for k, v in facts.items())
    user = f"Assistant message: {template}{fact_block}"

    out = llm_provider.generate(system, user)
    return out or template     # fallback to template on any failure
