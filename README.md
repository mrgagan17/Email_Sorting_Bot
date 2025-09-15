# Email_Sorting_Bot

A Python-based **Email Sorting Bot** that automatically classifies your emails based on priority (High, Medium, Low, Others) and sends mobile notifications for urgent emails. The bot uses **Machine Learning** for classification and can be used with Gmail accounts.  

---

## 📖 Description

This project is designed to help users manage their emails more efficiently. It automatically:

- Fetches emails from your inbox (both read and unread) from the last 30 days.
- Classifies emails into **High, Medium, Low, or Others** using a **Naive Bayes ML model** trained on email subjects and contents.
- Applies **keyword and domain-based overrides** for critical alerts like assignments, deadlines, or security notifications.
- Sends **Pushbullet notifications** for high-priority emails to your mobile device.
- Sends a **daily summary email** with all categorized emails for review.

This tool is ideal for professionals, students, and anyone who wants to **stay on top of important emails automatically**.

---

## ⚡ Features

- ✅ **ML-Based Classification** using `scikit-learn` (Naive Bayes + TF-IDF).
- ✅ **Keyword Overrides** to prioritize critical emails (e.g., security alerts, task deadlines).
- ✅ **Domain-Based Filtering** for promotional or newsletter emails.
- ✅ **Push Notifications** to mobile via **Pushbullet** for urgent emails.
- ✅ **Daily Summary Email** of all emails in the past 30 days.
- ✅ Handles both **read and unread emails**.
- ✅ Displays email **subject, sender, date, priority, and confidence**.

---

## 🛠️ Tools & Libraries Used

- **Python 3.11+**
- `imaplib` – Fetch emails from Gmail.
- `email` – Parse email messages.
- `smtplib` – Send summary emails.
- `requests` – Push notifications via Pushbullet API.
- `scikit-learn` – Machine Learning (Naive Bayes + TF-IDF Vectorizer).
- `pandas` – Data handling for training dataset.
- `pickle` – Save & load trained ML model.
- `datetime` – Handle email dates.
- `re` & `html` – Clean email content.
- Gmail account with **App Password** (for secure login).

---

When you run the **train_model.py** it will generate model.pkl and vectorizer.pkl files


---
## Install dependencies:

pip install -r requirements.txt

---

Create a **config.json** file with your credentials:

{

    "email": "your_email@gmail.com",

    "password": "your_app_password",

    "pushbullet_token": "your_pushbullet_access_token"

}

