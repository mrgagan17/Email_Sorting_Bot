# main.py
import imaplib
import email
import json
import pickle
import re
from email.header import decode_header
from email.mime.text import MIMEText
import smtplib
from datetime import datetime, timedelta
from html import unescape

# ----------------- CONFIG -----------------
with open("config.json", "r") as f:
    cfg = json.load(f)

EMAIL_ACCOUNT = cfg["email"]
PASSWORD = cfg["password"]
MOBILE_EMAIL = cfg.get("mobile_email", EMAIL_ACCOUNT)  # send high-priority notifications here

PROB_THRESHOLD = 0.60
MAX_EMAILS = 100
# ------------------------------------------

# Load trained pipeline
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

HIGH_KEYWORDS = [
    "task completion", "task complete", "assignment", "assignment submission",
    "submit assignment", "submit", "deadline", "due", "urgent",
    "project report", "interview", "action required", "complete the task",
    "submit your assignment", "submission",
    "password", "reset your password", "unusual activity", "security alert",
    "login attempt", "api token", "token expire", "verify your account",
    "account suspended", "account locked", "sign-in attempt", "account activity"
]

LOW_KEYWORDS = [
    "unsubscribe", "offer", "promotion", "discount", "newsletter", "receipt",
    "order confirmation", "welcome to", "verify email", "password reset link",
    "no-reply", "daily digest"
]

LOW_DOMAIN_KEYWORDS = ["pushbullet.com", "udemy", "e.udemymail.com", "amazon", "newsletter", "mailer"]

# ----------------- FUNCTIONS -----------------
def clean_text(s: str) -> str:
    if not s:
        return ""
    s = unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def extract_body(msg_obj):
    body = ""
    if msg_obj.is_multipart():
        for part in msg_obj.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            if ct == "text/plain" and "attachment" not in disp:
                try:
                    part_payload = part.get_payload(decode=True)
                    if part_payload:
                        body = part_payload.decode(errors="replace")
                        return clean_text(body)
                except:
                    continue
        for part in msg_obj.walk():
            if part.get_content_type() == "text/html":
                try:
                    html_payload = part.get_payload(decode=True)
                    if html_payload:
                        h = html_payload.decode(errors="replace")
                        text = re.sub(r"<[^>]+>", " ", h)
                        return clean_text(text)
                except:
                    continue
    else:
        try:
            payload = msg_obj.get_payload(decode=True)
            if payload:
                return clean_text(payload.decode(errors="replace"))
        except:
            return clean_text(str(msg_obj.get_payload()))
    return ""

def domain_of(sender):
    if not sender:
        return ""
    m = re.search(r"@([A-Za-z0-9.-]+)", sender)
    return m.group(1).lower() if m else ""

def apply_overrides(text, sender):
    text_l = text.lower()
    dom = domain_of(sender)

    for kw in HIGH_KEYWORDS:
        if kw in text_l:
            return "High", f"kw:{kw}"

    for kd in LOW_DOMAIN_KEYWORDS:
        if kd in dom or kd in text_l:
            return "Low", f"domain-low:{kd}"

    for kw in LOW_KEYWORDS:
        if kw in text_l:
            return "Low", f"kw:{kw}"

    return None, None

def fetch_and_classify():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")

    since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
    typ, data = mail.search(None, f'(SINCE {since_date})')
    if typ != "OK":
        print("No messages found.")
        return []

    all_ids = data[0].split()
    if not all_ids:
        return []

    email_ids = all_ids[-MAX_EMAILS:]

    results = []
    for eid in email_ids:
        try:
            typ, msg_data = mail.fetch(eid, "(RFC822)")
            if typ != "OK":
                continue
            for part in msg_data:
                if isinstance(part, tuple):
                    msg_obj = email.message_from_bytes(part[1])

                    subj, enc = decode_header(msg_obj.get("Subject", ""))[0]
                    if isinstance(subj, bytes):
                        try:
                            subj = subj.decode(enc if enc else "utf-8", errors="replace")
                        except:
                            subj = subj.decode("utf-8", errors="replace")
                    subj = subj or ""

                    sender = msg_obj.get("From", "Unknown")
                    date_raw = msg_obj.get("Date", "")
                    try:
                        date_dt = email.utils.parsedate_to_datetime(date_raw)
                        date_str = date_dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        date_str = date_raw

                    body = extract_body(msg_obj)
                    combined = f"{subj} {sender} {body}".strip()

                    override_label, reason = apply_overrides(combined, sender)
                    if override_label:
                        label = override_label
                        prob = 1.0
                        note = f"override:{reason}"
                    else:
                        probs = model.predict_proba([combined])[0]
                        classes = model.classes_
                        top_idx = probs.argmax()
                        top_prob = probs[top_idx]
                        predicted = classes[top_idx]
                        if top_prob < PROB_THRESHOLD:
                            label = "Others"
                            prob = float(top_prob)
                            note = f"low_confidence:{top_prob:.2f}"
                        else:
                            label = predicted
                            prob = float(top_prob)
                            note = f"model:{predicted}:{top_prob:.2f}"

                    results.append({
                        "date": date_str,
                        "subject": subj,
                        "from": sender,
                        "priority": label,
                        "prob": prob,
                        "note": note
                    })

        except Exception as e:
            print("Error processing a message:", e)
            continue

    mail.logout()
    results.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M") 
                 if len(x["date"]) >= 16 else datetime.now(), reverse=True)
    return results

# ----------------- SEND HIGH PRIORITY EMAIL -----------------
def send_high_priority_email(items):
    high_items = [it for it in items if it["priority"] == "High" and it["prob"] >= PROB_THRESHOLD]
    if not high_items:
        print("No high-priority emails to send.")
        return

    body = "High-Priority Emails (last 30 days):\n\n"
    for it in high_items:
        body += f"[{it['priority']}] {it['date']} - {it['subject']} - {it['from']} (p={it['prob']:.2f}) note={it['note']}\n"

    msg = MIMEText(body)
    msg["From"] = EMAIL_ACCOUNT
    msg["To"] = MOBILE_EMAIL
    msg["Subject"] = "High-Priority Emails Summary"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ACCOUNT, PASSWORD)
            server.send_message(msg)
        print(f"✅ High-priority email summary sent to {MOBILE_EMAIL}")
    except Exception as e:
        print("Could not send high-priority email:", e)

# ----------------- MAIN -----------------
if __name__ == "__main__":
    items = fetch_and_classify()
    for it in items:
        print(f"[{it['priority']}] {it['date']} - {it['subject']} - {it['from']} (p={it['prob']:.2f}) {it['note']}")

    send_high_priority_email(items)
