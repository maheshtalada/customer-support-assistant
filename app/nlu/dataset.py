"""M2 Data Preparation — the labeled seed corpus for supervised NLU.

Two labeled sets:
  INTENT_DATA     (utterance -> intent)         -> trains the intent MLP
  SENTIMENT_DATA  (utterance -> POS/NEU/NEG)    -> trains the sentiment MLP

This is a compact, hand-labeled dataset representative of billing-dispute and
offer-recommendation conversations. In a full build these rows would be mined
from the chat logs / FAQs / support tickets described in the project tasks;
for the PoC they are curated so the models are explainable and reproducible."""

# Canonical intent taxonomy used across the brain.
INTENTS = [
    "GREETING", "BILL_EXPLAIN", "BILL_DISPUTE", "FACTUAL_DISPUTE",
    "PROMO_INQUIRY", "CONFIRM_YES", "CONFIRM_NO", "HAGGLE",
    "CREATE_TICKET", "TICKET_STATUS", "HUMAN_HANDOFF",
    "PAYMENT_QUERY", "GOODBYE", "FALLBACK",
]

INTENT_DATA = [
    # GREETING
    ("hi there", "GREETING"), ("hello", "GREETING"), ("hey good morning", "GREETING"),
    ("hi can you help me", "GREETING"), ("hello i need some help", "GREETING"),
    # BILL_EXPLAIN
    ("why is my bill higher this month", "BILL_EXPLAIN"),
    ("my bill went up can you explain", "BILL_EXPLAIN"),
    ("what are these charges on my bill", "BILL_EXPLAIN"),
    ("can you break down my bill", "BILL_EXPLAIN"),
    ("why did i pay more than last month", "BILL_EXPLAIN"),
    ("explain my current bill please", "BILL_EXPLAIN"),
    ("what is this extra charge", "BILL_EXPLAIN"),
    ("my bill looks wrong this cycle", "BILL_EXPLAIN"),
    # BILL_DISPUTE
    ("i want to dispute a charge", "BILL_DISPUTE"),
    ("this roaming charge is wrong", "BILL_DISPUTE"),
    ("i should not be charged for this", "BILL_DISPUTE"),
    ("that overage fee is incorrect", "BILL_DISPUTE"),
    ("i disagree with this charge", "BILL_DISPUTE"),
    ("please remove this charge", "BILL_DISPUTE"),
    ("i want a refund for this fee", "BILL_DISPUTE"),
    ("this charge should not be here", "BILL_DISPUTE"),
    # FACTUAL_DISPUTE
    ("i never went to mexico", "FACTUAL_DISPUTE"),
    ("i did not travel anywhere", "FACTUAL_DISPUTE"),
    ("i didn't use that much data", "FACTUAL_DISPUTE"),
    ("that wasn't me", "FACTUAL_DISPUTE"),
    ("i never used roaming", "FACTUAL_DISPUTE"),
    ("i was never abroad", "FACTUAL_DISPUTE"),
    ("i didn't go there", "FACTUAL_DISPUTE"),
    # PROMO_INQUIRY
    ("do you have any offers for me", "PROMO_INQUIRY"),
    ("any discounts available", "PROMO_INQUIRY"),
    ("what deals can i get", "PROMO_INQUIRY"),
    ("are there any promotions", "PROMO_INQUIRY"),
    ("can i get a better plan", "PROMO_INQUIRY"),
    ("show me my offers", "PROMO_INQUIRY"),
    ("is there a loyalty reward", "PROMO_INQUIRY"),
    ("recommend me a deal", "PROMO_INQUIRY"),
    # CONFIRM_YES
    ("yes please", "CONFIRM_YES"), ("yeah go ahead", "CONFIRM_YES"),
    ("sure sounds good", "CONFIRM_YES"), ("ok apply it", "CONFIRM_YES"),
    ("yes i accept", "CONFIRM_YES"), ("that works for me", "CONFIRM_YES"),
    ("absolutely", "CONFIRM_YES"),
    # CONFIRM_NO
    ("no thanks", "CONFIRM_NO"), ("not interested", "CONFIRM_NO"),
    ("no i don't want that", "CONFIRM_NO"), ("nah skip it", "CONFIRM_NO"),
    ("no thank you", "CONFIRM_NO"), ("i'll pass", "CONFIRM_NO"),
    # HAGGLE
    ("that's too expensive", "HAGGLE"),
    ("can you do better than that", "HAGGLE"),
    ("that offer is not good enough", "HAGGLE"),
    ("i'll cancel if you can't help", "HAGGLE"),
    ("i'm thinking of switching to another carrier", "HAGGLE"),
    ("give me a bigger discount", "HAGGLE"),
    ("that's still too much money", "HAGGLE"),
    ("i want a better deal or i'm leaving", "HAGGLE"),
    # CREATE_TICKET
    ("open a formal dispute", "CREATE_TICKET"),
    ("i want to file a complaint", "CREATE_TICKET"),
    ("please raise a ticket for this", "CREATE_TICKET"),
    ("log this as a dispute", "CREATE_TICKET"),
    ("escalate this officially", "CREATE_TICKET"),
    # TICKET_STATUS
    ("what is the status of my ticket", "TICKET_STATUS"),
    ("any update on my complaint", "TICKET_STATUS"),
    ("did my dispute get resolved", "TICKET_STATUS"),
    ("check my ticket status", "TICKET_STATUS"),
    # HUMAN_HANDOFF
    ("i want to talk to a human", "HUMAN_HANDOFF"),
    ("connect me to an agent", "HUMAN_HANDOFF"),
    ("let me speak to a manager", "HUMAN_HANDOFF"),
    ("i need a real person", "HUMAN_HANDOFF"),
    ("transfer me to a supervisor", "HUMAN_HANDOFF"),
    # PAYMENT_QUERY
    ("when did i last pay", "PAYMENT_QUERY"),
    ("show my payment history", "PAYMENT_QUERY"),
    ("did my payment go through", "PAYMENT_QUERY"),
    ("what did i pay last month", "PAYMENT_QUERY"),
    # GOODBYE
    ("that's all thanks", "GOODBYE"), ("goodbye", "GOODBYE"),
    ("thanks bye", "GOODBYE"), ("we're done thank you", "GOODBYE"),
    # FALLBACK / out of scope
    ("what's the weather today", "FALLBACK"),
    ("tell me a joke", "FALLBACK"),
    ("who won the match", "FALLBACK"),
    ("asdf random text", "FALLBACK"),
    # ── extra examples (improve generalization + held-out metrics) ────────────
    ("good afternoon", "GREETING"), ("hey there team", "GREETING"),
    ("hi i have a query", "GREETING"), ("hello anyone there", "GREETING"),
    ("why has my bill increased", "BILL_EXPLAIN"),
    ("my monthly charge is higher", "BILL_EXPLAIN"),
    ("what is this amount for", "BILL_EXPLAIN"),
    ("help me understand my charges", "BILL_EXPLAIN"),
    ("this fee should be removed", "BILL_DISPUTE"),
    ("i am being overcharged", "BILL_DISPUTE"),
    ("this bill is not correct", "BILL_DISPUTE"),
    ("i want my money back for this", "BILL_DISPUTE"),
    ("i did not make those calls", "FACTUAL_DISPUTE"),
    ("i was not roaming at all", "FACTUAL_DISPUTE"),
    ("that trip never happened", "FACTUAL_DISPUTE"),
    ("i did not exceed my data", "FACTUAL_DISPUTE"),
    ("what promotions do i qualify for", "PROMO_INQUIRY"),
    ("any special offer for me today", "PROMO_INQUIRY"),
    ("do i get a loyalty discount", "PROMO_INQUIRY"),
    ("suggest a good plan upgrade", "PROMO_INQUIRY"),
    ("yes lets do it", "CONFIRM_YES"), ("okay please apply", "CONFIRM_YES"),
    ("sure why not", "CONFIRM_YES"), ("yep sounds good", "CONFIRM_YES"),
    ("no i do not want it", "CONFIRM_NO"), ("nope not for me", "CONFIRM_NO"),
    ("not right now thanks", "CONFIRM_NO"), ("i would rather not", "CONFIRM_NO"),
    ("that price is too high", "HAGGLE"), ("i expected a bigger discount", "HAGGLE"),
    ("your competitor offers more", "HAGGLE"), ("i might leave for another network", "HAGGLE"),
    ("register a formal complaint", "CREATE_TICKET"),
    ("i want to lodge a dispute officially", "CREATE_TICKET"),
    ("create a support ticket please", "CREATE_TICKET"),
    ("has my ticket been resolved", "TICKET_STATUS"),
    ("track my complaint please", "TICKET_STATUS"),
    ("what happened to my dispute", "TICKET_STATUS"),
    ("i need to speak with someone", "HUMAN_HANDOFF"),
    ("get me a live representative", "HUMAN_HANDOFF"),
    ("i want a human not a bot", "HUMAN_HANDOFF"),
    ("show me my recent payments", "PAYMENT_QUERY"),
    ("has my last bill been paid", "PAYMENT_QUERY"),
    ("when is my payment due", "PAYMENT_QUERY"),
    ("that will be all thank you", "GOODBYE"), ("see you later", "GOODBYE"),
    ("ok bye now", "GOODBYE"),
    ("play some music", "FALLBACK"), ("what time is it", "FALLBACK"),
    ("random gibberish here", "FALLBACK"),
]

SENTIMENT_DATA = [
    # POSITIVE
    ("thank you so much that's great", "POS"), ("that sounds perfect", "POS"),
    ("awesome i really appreciate it", "POS"), ("yes that makes me happy", "POS"),
    ("wonderful thanks for helping", "POS"), ("great deal i love it", "POS"),
    ("that works nicely thanks", "POS"), ("excellent good job", "POS"),
    # NEGATIVE
    ("this is ridiculous", "NEG"), ("i'm really frustrated with this", "NEG"),
    ("this is unacceptable", "NEG"), ("i'm angry about these charges", "NEG"),
    ("worst service ever", "NEG"), ("this is a scam", "NEG"),
    ("i'm fed up and want to leave", "NEG"), ("terrible experience", "NEG"),
    ("this is wrong and unfair", "NEG"), ("i hate dealing with this", "NEG"),
    # NEUTRAL
    ("why is my bill higher", "NEU"), ("show me my offers", "NEU"),
    ("what is the status", "NEU"), ("can you explain the charge", "NEU"),
    ("i have a question about my plan", "NEU"), ("ok tell me more", "NEU"),
    ("what are my options", "NEU"), ("i want to check my payment", "NEU"),
    # extra POSITIVE
    ("this is really helpful thank you", "POS"), ("appreciate the quick help", "POS"),
    ("that is a fair deal i am happy", "POS"), ("brilliant that solves it", "POS"),
    ("you have been very helpful", "POS"), ("thanks that is exactly what i needed", "POS"),
    # extra NEGATIVE
    ("i am furious about this charge", "NEG"), ("this is completely unfair", "NEG"),
    ("i am so annoyed right now", "NEG"), ("this keeps happening and it is awful", "NEG"),
    ("i am disappointed with the service", "NEG"), ("stop overcharging me this is wrong", "NEG"),
    # extra NEUTRAL
    ("hello i need help", "NEU"), ("hi there", "NEU"),
    ("can you check my account", "NEU"), ("i want to dispute a charge", "NEU"),
    ("what offers do i have", "NEU"), ("open a ticket for me", "NEU"),
    ("i never went to mexico", "NEU"), ("please explain this line item", "NEU"),
]
