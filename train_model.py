# train_model.py
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

# -- Example training data (expand this to improve accuracy) --
texts = [
    # HIGH examples (12)
    "Submit assignment today evening 7:00 pm",
    "Task completion report due tomorrow",
    "Assignment submission required",
    "Urgent: project report due",
    "Interview scheduled on Monday",
    "Please complete the task by EOD",
    "Final project submission deadline",
    "Action required: submit your assignment",
    "Bug fix required - urgent",
    "Your API Token is about to expire",
    "Password expiry notification",
    "License will expire soon",
    # MEDIUM examples (5)
    "Weekly meeting update",
    "Status update on project",
    "Team reminder: standup at 10 AM",
    "Please review attached update",
    "Project status: please read",
    # LOW examples (7)
    "Super Offer- Buy 1 Learn 8, Python, Excel, Google Sheet",
    "Welcome to Pushbullet!",
    "Discount offers on shopping",
    "Newsletter: weekly news",
    "Receipt for your purchase",
    "Your order confirmation",
    "Promotion: 50% off only today",
    # OTHERS / NEUTRAL (7)
    "Hi",
    "Hello there",
    "Quick question",
    "FYI: notes from yesterday",
    "Thanks for your message",
    "Re: hello",
    "Can we talk later?"
]

labels = [
    # High (12)
    "High","High","High","High","High","High","High","High","High","High","High","High",
    # Medium (5)
    "Medium","Medium","Medium","Medium","Medium",
    # Low (7)
    "Low","Low","Low","Low","Low","Low","Low",
    # Others (7)
    "Others","Others","Others","Others","Others","Others","Others"
]


# ✅ Now both have 29 items

# Make DataFrame
df = pd.DataFrame({"text": texts, "priority": labels})

# Pipeline: TF-IDF + Naive Bayes
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_df=0.9)),
    ("clf", MultinomialNB())
])

# Train / eval split
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["priority"], test_size=0.2, random_state=42, stratify=df["priority"]
)

pipeline.fit(X_train, y_train)

# Quick evaluation
y_pred = pipeline.predict(X_test)
print("=== Classification report on small test set ===")
print(classification_report(y_test, y_pred, zero_division=0))

# Save model pipeline
with open("model.pkl", "wb") as f:
    pickle.dump(pipeline, f)

print("✅ Model and vectorizer trained & saved successfully!")
