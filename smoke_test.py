"""Offline brain smoke test. Verifies the hub-and-spoke, billing dispute,
offers, RL feedback and handoff all wire together.

By default runs WITHOUT the LLM (fast, deterministic templates). Set
USE_LLM=1 to route replies through the configured LLM provider (.env), e.g.:
    USE_LLM=1 python smoke_test.py
"""
import os
from app import coordinator
from app.nlg import llm_provider

USE_LLM = os.getenv("USE_LLM", "0") == "1"


def run(cid, msgs, title):
    print(f"\n===== {title}  ({cid}) =====")
    st = coordinator.start_session(cid)
    for m in msgs:
        r = coordinator.handle_turn(st, m, use_llm=USE_LLM)
        tag = f"{r['speaker']}/{r['spoke']}"
        print(f"[{tag}] intent={r['intent']}({r['intent_conf']}) "
              f"sent={r['sentiment']} handoff={r['handoff']} res={r['resolution_status']}")
        print("   USER:", m)
        print("   BOT :", r["text"][:170])
        if r["action"]:
            print("   ACT :", r["action"])
    coordinator.save_session(st)
    print("   -> resolution:", st.resolution_status, "| actions:", len(st.actions))


run("CUST-TELCO-1003",
    ["why is my bill higher this month",
     "i never used that much data",
     "that is too expensive can you do better",
     "no that is still too much",
     "ok yes fine apply it"],
    "Billing dispute -> haggle -> retention handoff -> close")

run("CUST-TELCO-1001",
    ["hi there",
     "why is my bill higher this month",
     "wait i never went to mexico",
     "please open a formal dispute ticket"],
    "GOLD roaming dispute -> ticket")

run("CUST-TELCO-1001",
    ["do you have any offers for me",
     "yes please apply it"],
    "Offer recommendation -> accept (RL reward)")

print(f"\n[LLM mode: {'ON — ' + llm_provider.status() if USE_LLM else 'OFF (templates)'}]")
