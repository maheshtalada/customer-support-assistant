"""M6 Deployment & Monitoring — Streamlit chat UI.

Flow:  login (email + password)  ->  identity check (last 4 on file)  ->  chat.
The chat is a real conversation UI (st.chat_message / st.chat_input) with a live
signal + monitoring panel in the sidebar so the hub-and-spoke, NLU signals, RL
learning and KPIs are all visible on camera.

Run from the repo root:   streamlit run ui/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from app import auth, data_store, coordinator, metrics
from app.nlg import llm_provider
from app.rl import bandit

st.set_page_config(page_title="Telco Support Chatbot", page_icon="💬", layout="wide")

AVATARS = {"customer": "🧑", "Aria": "🤖", "Ray": "🧑‍💼"}
SENTI_EMOJI = {"POS": "🙂", "NEU": "😐", "NEG": "😟"}


def esc(text):
    """Escape $ so Streamlit doesn't render '$..$' as LaTeX math."""
    return (text or "").replace("$", "\\$")


# ── session bootstrap ────────────────────────────────────────────────────────
def _init():
    ss = st.session_state
    ss.setdefault("stage", "welcome")
    ss.setdefault("cust", None)
    ss.setdefault("convo", None)
    ss.setdefault("messages", [])
    ss.setdefault("use_llm", llm_provider.available())


_init()
ss = st.session_state


# ── WELCOME / LANDING ────────────────────────────────────────────────────────
def welcome_screen():
    st.title("💬 Telco Customer Support Assistant")
    st.subheader("Your AI assistant for billing questions, disputes & personalized offers")
    st.write("Get instant, secure help with your telecom account — no waiting on hold. "
             "Chat in plain English and the assistant understands your intent, checks "
             "your account, and resolves your issue on the spot.")

    st.markdown("#### What you can do")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🧾 Understand your bill")
        st.caption("Ask why your bill changed and get a clear, line-by-line breakdown "
                   "of every charge.")
    with c2:
        st.markdown("### ⚖️ Dispute a charge")
        st.caption("Challenge a roaming or overage charge. The assistant shows the "
                   "evidence and resolves it with a credit, waiver, or dispute ticket.")
    with c3:
        st.markdown("### 🎁 Get offers")
        st.caption("Receive personalized discounts and plan recommendations matched "
                   "to your usage and loyalty tier.")

    st.markdown("#### How it works")
    h1, h2, h3 = st.columns(3)
    h1.info("**1. Verify your identity**\n\nSign in and confirm the last 4 digits of "
            "your ID — your account stays secure.")
    h2.info("**2. Chat naturally**\n\nAsk your question in your own words. No menus, "
            "no keywords to memorize.")
    h3.info("**3. Get it resolved**\n\nThe assistant takes action — applies a credit, "
            "opens a ticket, or activates an offer — and confirms it.")

    st.caption("🔒 A specialist assistant automatically steps in for tougher cases. "
               "This is a demo using synthetic accounts — no real customer data.")

    st.divider()
    b1, b2, b3 = st.columns([1, 1, 1])
    if b2.button("Get started  →", type="primary", use_container_width=True):
        ss.stage = "login"
        st.rerun()


# ── LOGIN ────────────────────────────────────────────────────────────────────
def login_screen():
    st.title("💬 Telco Customer Support Assistant")
    st.caption("Sign in and verify your identity to chat about billing disputes and offers.")
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                cust = auth.check_login(email, password)
                if cust:
                    ss.cust, ss.stage = cust, "verify"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        if st.button("← Back to home"):
            ss.stage = "welcome"
            st.rerun()
    with col2:
        st.info("**Demo logins** (password: `teleco123`)")
        st.table([{"Name": d["name"], "Email": d["email"], "Tier": d["tier"],
                   "ID last4": d["last4"]} for d in auth.demo_directory()])


def verify_screen():
    cust = ss.cust
    st.title("🔐 Identity verification")
    st.write(f"Hi **{cust['first_name']}** — for your security, confirm the "
             "**last 4 digits of the ID on file** before we continue.")
    with st.form("verify"):
        last4 = st.text_input("Last 4 digits", max_chars=4)
        c1, c2 = st.columns(2)
        if c1.form_submit_button("Verify", type="primary"):
            if auth.verify_identity(cust, last4):
                ss.convo = coordinator.start_session(cust["customer_id"])
                ss.messages = [{"role": "Aria", "text":
                    f"Hi {cust['first_name']}! I'm Aria, your support assistant. "
                    "I can explain your bill, help with a disputed charge, or find "
                    "offers for you. What can I help with today?", "meta": None}]
                ss.stage = "chat"
                st.rerun()
            else:
                st.error("That doesn't match our records. (Hint: shown on the login page.)")
        if c2.form_submit_button("Back"):
            ss.stage = "login"
            st.rerun()


# ── SIDEBAR: context + live signals + monitoring ─────────────────────────────
def sidebar():
    cust = ss.cust
    bill = data_store.get_bill(cust["customer_id"])
    convo = ss.convo
    with st.sidebar:
        st.subheader(f"👤 {cust['first_name']} {cust['last_name']}")
        st.caption(f"{cust['loyalty_tier']} · {cust['segment']} · "
                   f"{cust['tenure_months']}mo · {cust['plan']}")
        if bill:
            st.metric(f"Current bill ({bill['cycle']})", f"${bill['total_usd']}",
                      f"${bill['total_usd'] - bill['previous_usd']} vs last month")

        st.divider()
        st.markdown("### 📡 Live signals")
        last = convo.turns[-1] if convo.turns else None
        if last:
            c1, c2 = st.columns(2)
            c1.metric("Intent", last["intent"], f"{int(last['intent_conf']*100)}%")
            c2.metric("Sentiment", SENTI_EMOJI.get(last["sentiment"], "😐"),
                      last["sentiment"])
            spoke = "🟢 Billing (Aria)" if convo.active_spoke == "billing" \
                else "🟣 Retention (Ray)"
            st.write(f"**Active spoke:** {spoke}")
            if convo.handoff_reason:
                st.write(f"**Handoff reason:** `{convo.handoff_reason}`")
            st.write(f"**Resolution:** `{convo.resolution_status}`")
        else:
            st.caption("Signals appear once you send a message.")

        st.divider()
        st.markdown("### 🧠 Config")
        ss.use_llm = st.toggle(f"LLM phrasing ({llm_provider.status()})",
                               value=ss.use_llm,
                               help="On: rephrase via the configured LLM (falls back "
                                    "to templates if unreachable). Off: pure templates.")

        with st.expander("🎯 RL offer learning (M5)"):
            snap = bandit.snapshot()
            if snap:
                st.table([{"offer": k.replace("OFFER-", ""), "shown": v["shows"],
                           "accepted": v["accepts"], "Q": v["q"]}
                          for k, v in snap.items()])
            else:
                st.caption("No offer feedback recorded yet.")

        with st.expander("📊 KPIs (M6 monitoring)"):
            fb = [t["feedback"] for t in convo.turns if t.get("feedback")]
            up = sum(1 for f in fb if f == "up")
            st.metric("This session CSAT", f"{up}/{len(fb)}" if fb else "—",
                      help="👍 vs total ratings this chat")
            st.caption("Across saved sessions:")
            st.json(metrics.conversation_metrics())

        st.divider()
        if st.button("💾 End & save session"):
            coordinator.save_session(convo)
            st.success(f"Saved {convo.session_id}")
        if st.button("🚪 Log out"):
            for k in ("stage", "cust", "convo", "messages"):
                ss.pop(k, None)
            st.rerun()


# ── CHAT ─────────────────────────────────────────────────────────────────────
def chat_screen():
    sidebar()
    st.title("💬 Support chat")

    for m in ss.messages:
        role = m["role"]
        with st.chat_message("user" if role == "customer" else "assistant",
                             avatar=AVATARS.get(role, "🤖")):
            if role != "customer":
                st.caption(f"**{role}** · {'Retention specialist' if role=='Ray' else 'Billing & offers'}")
            st.write(esc(m["text"]))
            meta = m.get("meta")
            if meta:
                if meta.get("handoff"):
                    st.info(f"⚡ Handed off to **Retention specialist (Ray)** — "
                            f"reason: `{meta['handoff_reason']}`")
                if meta.get("offer_cards"):
                    cols = st.columns(len(meta["offer_cards"]))
                    for col, oc in zip(cols, meta["offer_cards"]):
                        col.metric(oc["title"][:22], f"${oc['value']}",
                                   f"score {oc['score']}")
                chips = (f"intent `{meta['intent']}` · sentiment "
                         f"{SENTI_EMOJI.get(meta['sentiment'],'')} · "
                         f"policy `{meta['directive']}` · {meta['latency_ms']}ms")
                st.caption(chips)
                idx = meta.get("turn_idx")
                if idx is not None and idx < len(ss.convo.turns):
                    fb = ss.convo.turns[idx].get("feedback")
                    b1, b2, _ = st.columns([1, 1, 8])
                    if b1.button("👍", key=f"up{idx}", disabled=fb == "up"):
                        ss.convo.turns[idx]["feedback"] = "up"
                        st.rerun()
                    if b2.button("👎", key=f"down{idx}", disabled=fb == "down"):
                        ss.convo.turns[idx]["feedback"] = "down"
                        st.rerun()

    if prompt := st.chat_input("Ask about your bill, a charge, or offers…"):
        ss.messages.append({"role": "customer", "text": prompt, "meta": None})
        r = coordinator.handle_turn(ss.convo, prompt, use_llm=ss.use_llm)
        r["turn_idx"] = len(ss.convo.turns) - 1     # link message -> stored turn
        ss.messages.append({"role": r["speaker"], "text": r["text"], "meta": r})
        st.rerun()


# ── router ───────────────────────────────────────────────────────────────────
if ss.stage == "welcome":
    welcome_screen()
elif ss.stage == "login":
    login_screen()
elif ss.stage == "verify":
    verify_screen()
else:
    chat_screen()
