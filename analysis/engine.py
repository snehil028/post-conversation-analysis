# conversation_analysis_simple.py
import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import textstat

# Simple lazy loading so imports are cheap at start
_sbert = None
_sentiment_pipe = None


def get_sbert():
    global _sbert
    if _sbert is None:
        # small / fast model
        _sbert = SentenceTransformer("all-MiniLM-L6-v2")
    return _sbert


def get_sentiment_pipe():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = pipeline("sentiment-analysis",
                                   model="distilbert-base-uncased-finetuned-sst-2-english")
    return _sentiment_pipe


# simple fallback phrases to detect "I don't know"-type answers
FALLBACK_PATTERNS = [r"i don't know", r"can't help", r"sorry", r"i'm not sure"]

# empathy phrases to look for
EMPATHY_PHRASES = ["sorry", "i understand", "i can imagine",
                   "that must be", "i'm here to help", "feel free"]

# completeness words that indicate a full answer
COMPLETE_HINTS = ["here's", "here is", "in summary", "steps to",
                  "follow these", "you can", "solution", "fixed", "done"]

# words that show an assertive factual reply (used in the accuracy heuristic)
ASSERTIVE_WORDS = ["is", "are", "was", "has been", "will",
                   "was shipped", "arrive", "delivered", "confirmed"]

# Helper small functions


def contains_any(text: str, patterns: List[str]) -> bool:
    """Return True if any pattern (substring or regex) is in text (case-insensitive)."""
    low = text.lower()
    for p in patterns:
        if re.search(p, low):
            return True
    return False


def word_overlap_score(a: str, b: str) -> float:
    """
    Very simple 'accuracy' proxy:
    - Return fraction of shared words between user message and AI reply.
    - This is NOT real accuracy but a cheap heuristic: if AI repeats important tokens from user, it's more likely relevant/accurate.
    """
    a_words = set(re.findall(r"\w+", a.lower()))
    b_words = set(re.findall(r"\w+", b.lower()))
    if not a_words or not b_words:
        return 0.0
    overlap = a_words.intersection(b_words)
    return len(overlap) / max(1, len(a_words))

# Main analysis function


def analyze_conversation(conv) -> Dict[str, object]:
    """
    conv is expected to be a Conversation instance (Django model) where conv.messages is iterable
    and each message object has at least:
        - sender (string: 'user' or 'ai')
        - text (string)
        - optional: timestamp (datetime). If not present, function uses mock delays.

    Returns a dict with many metrics (clarity, relevance, accuracy, completeness, sentiment, empathy, response_time, fallback_count, resolution, escalation_need, overall_score).
    """

    # Step 1: collect ordered messages
    messages = list(conv.messages.order_by("id"))
    if not messages:
        return {}

    # split user and ai messages
    user_texts = [m.text for m in messages if m.sender == "user"]
    ai_texts = [m.text for m in messages if m.sender == "ai"]

    # Step 2: sentiment (last up-to-3 user messages)
    sentiment = None
    if user_texts:
        text_for_sent = " ".join(user_texts[-3:])
        try:
            pipe = get_sentiment_pipe()
            res = pipe(text_for_sent[:1000])
            if isinstance(res, list) and res:
                sentiment = res[0].get("label", "").lower()
        except Exception:
            sentiment = None

    # Step 3: clarity of AI replies (Flesch reading ease)
    clarity_vals = []
    for t in ai_texts:
        try:
            clarity_vals.append(textstat.flesch_reading_ease(t))
        except Exception:
            pass
    avg_clarity = sum(clarity_vals) / \
        len(clarity_vals) if clarity_vals else 60.0
    # normalize to 0..1 roughly
    clarity_score = max(0.0, min(1.0, avg_clarity / 100.0))

    # Step 4: relevance via SBERT for AI reply vs previous user message
    relevance_scores = []
    sbert = get_sbert()
    for i, msg in enumerate(messages):
        if msg.sender == "ai" and i > 0 and messages[i-1].sender == "user":
            try:
                a_emb = sbert.encode(msg.text, convert_to_tensor=True)
                u_emb = sbert.encode(
                    messages[i-1].text, convert_to_tensor=True)
                sim = util.cos_sim(a_emb, u_emb).item()
                # sims often ~0..1 for related sentences; clamp
                relevance_scores.append(max(-1.0, min(1.0, float(sim))))
            except Exception:
                continue
    relevance_score = float(sum(relevance_scores) /
                            len(relevance_scores)) if relevance_scores else 0.0

    # Step 5: empathy heurstic
    empathy_hits = 0
    for t in ai_texts:
        if contains_any(t, EMPATHY_PHRASES):
            empathy_hits += 1
    empathy_score = (empathy_hits / max(1, len(ai_texts))) if ai_texts else 0.0

    # Step 6: fallback count
    fallback_count = 0
    for t in ai_texts:
        if contains_any(t, FALLBACK_PATTERNS):
            fallback_count += 1

    # Step 7: resolution detection
    resolved = any(re.search(
        r"\b(thanks|thank you|that helps|resolved|fixed|works now)\b", u.lower()) for u in user_texts)

    # Step 8: response time (average seconds between consecutive messages)
    # if messages have .timestamp (datetime), use it; otherwise use mock delays
    times = []
    for m in messages:
        ts = getattr(m, "timestamp", None)
        if isinstance(ts, datetime):
            times.append(ts)
        else:
            times.append(None)

    # if all timestamps are None -> generate mock times by picking random gaps (in seconds)
    if all(t is None for t in times):
        mock = datetime.utcnow()
        times = []
        for _ in messages:
            # random gap between 2s and 40s
            times.append(mock)
            mock = mock + timedelta(seconds=random.randint(2, 40))
    else:
        # replace None timestamps with previous known time + small delta
        last_known = None
        for i, t in enumerate(times):
            if t is not None:
                last_known = t
            else:
                # put a default 5-second jump
                fill = last_known + \
                    timedelta(seconds=5) if last_known else datetime.utcnow()
                times[i] = fill
                last_known = fill

    # compute diffs
    diffs = []
    for i in range(1, len(times)):
        delta = (times[i] - times[i-1]).total_seconds()
        if delta < 0:
            delta = abs(delta)  # just in case ordering is off
        diffs.append(delta)
    avg_response_time = sum(diffs) / len(diffs) if diffs else 0.0

    # --- Step 9: accuracy heuristic (word overlap between a user message and the AI reply that follows) ---
    accuracy_scores = []
    for i, m in enumerate(messages):
        if m.sender == "ai" and i > 0 and messages[i-1].sender == "user":
            user_msg = messages[i-1].text
            ai_msg = m.text
            overlap = word_overlap_score(user_msg, ai_msg)
            # boost a bit if AI used assertive words (cheap confidence)
            boost = 0.1 if contains_any(ai_msg, ASSERTIVE_WORDS) else 0.0
            score = min(1.0, overlap + boost)
            accuracy_scores.append(score)
    accuracy_score = float(sum(accuracy_scores) /
                           len(accuracy_scores)) if accuracy_scores else 0.0

    # Step 10: completeness heuristic (does AI provide an answer vs ask fro info)
    completeness_scores = []
    for i, m in enumerate(messages):
        if m.sender == "ai":
            text = m.text.lower()
            # if AI asks a question, it's probably incomplete
            if "?" in text or re.search(r"\b(can you|could you|please provide|please share)\b", text):
                completeness_scores.append(0.0)
                continue
            # if AI contains clear answer words, give higher completeness
            if contains_any(text, COMPLETE_HINTS):
                completeness_scores.append(1.0)
                continue
            # otherwise use a middle score based on length
            # short -> low, long -> higher
            completeness_scores.append(min(1.0, len(text.split()) / 40.0))
    completeness_score = float(sum(
        completeness_scores) / len(completeness_scores)) if completeness_scores else 0.0

    # Step 11: escalation need heuristic
    # escalate if negative sentiment, many fallbacks, low accuracy or user explicitly asks escalate
    user_asks_escalation = any(re.search(
        r"\b(human|agent|someone else|supervisor|manager|escalat)\b", u.lower()) for u in user_texts)
    escalation_need = False
    if sentiment == "negative" or fallback_count > 2 or accuracy_score < 0.2 or user_asks_escalation:
        escalation_need = True

    # Step 12: overall score
    # avg the five main numeric signals (clarity, relevance, empathy, accuracy, completeness)
    overall_score = (clarity_score + relevance_score +
                     empathy_score + accuracy_score + completeness_score) / 5.0

    # final results dict
    results = {
        "clarity_score": round(clarity_score, 3),
        "relevance_score": round(relevance_score, 3),
        "accuracy_score": round(accuracy_score, 3),
        "completeness_score": round(completeness_score, 3),
        "sentiment": sentiment,
        "empathy_score": round(empathy_score, 3),
        "avg_response_time_seconds": round(avg_response_time, 2),
        "fallback_count": fallback_count,
        "resolution": resolved,
        "escalation_needed": escalation_need,
        "overall_score": round(overall_score, 3),
    }

    return results

# ---------------- Example usage (for a fresher) -----------------
# from your_app.models import Conversation
# conv = Conversation.objects.get(pk=1)
# metrics = analyze_conversation_simple(conv)
# print(metrics)
