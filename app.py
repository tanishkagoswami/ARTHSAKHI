from flask import Flask, render_template, request, redirect, url_for
from datetime import date
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re

app = Flask(__name__)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

model = None
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

user_data = {
    "name": "",
    "income": 0.0,
    "goal": 0.0
}

expenses = []

learning_modules = [
    {
        "id": 1,
        "title": "Budgeting Basics",
        "description": "Learn how to divide income, expenses, and savings smartly.",
        "daily_lessons": [
            {"day": 1, "title": "Income vs Expense", "content": "Understand how much money comes in and how much goes out every month."},
            {"day": 2, "title": "Needs vs Wants", "content": "Separate essential spending like food and rent from non-essential spending like impulse shopping."},
            {"day": 3, "title": "50-30-20 Rule", "content": "Use 50% for needs, 30% for wants, and 20% for savings or debt repayment."},
            {"day": 4, "title": "Track Daily Spending", "content": "Record even small expenses because they add up quickly over time."}
        ],
        "quiz": {
            "question": "Which one is usually a need?",
            "options": ["Movie subscription", "Groceries", "Impulse shopping", "Luxury handbag"],
            "answer": "Groceries"
        }
    },
    {
        "id": 2,
        "title": "Smart Saving",
        "description": "Build healthy money habits and create an emergency fund.",
        "daily_lessons": [
            {"day": 1, "title": "Start Small", "content": "Saving small amounts regularly is better than waiting to save large amounts later."},
            {"day": 2, "title": "Emergency Fund", "content": "Aim to build savings that can cover at least 3 months of necessary expenses."},
            {"day": 3, "title": "Set a Goal", "content": "A clear savings goal helps you stay consistent and motivated."},
            {"day": 4, "title": "Avoid Emotional Spending", "content": "Try not to shop when stressed, bored, or upset."}
        ],
        "quiz": {
            "question": "What should you build first?",
            "options": ["Emergency fund", "Luxury budget", "More subscriptions", "Random spending habit"],
            "answer": "Emergency fund"
        }
    },
    {
        "id": 3,
        "title": "Digital Payment Safety",
        "description": "Stay safe from OTP, KYC, and fake payment scams.",
        "daily_lessons": [
            {"day": 1, "title": "Never Share OTP", "content": "Your OTP, PIN, and CVV should never be shared with anyone."},
            {"day": 2, "title": "Fake KYC Alerts", "content": "Banks usually do not ask you to update KYC using random links sent by SMS."},
            {"day": 3, "title": "Suspicious Links", "content": "Do not click unknown payment or refund links from untrusted sources."},
            {"day": 4, "title": "Verify Payment Requests", "content": "Always confirm unknown payment requests before sending money."}
        ],
        "quiz": {
            "question": "What should you never share?",
            "options": ["Budget goal", "Expense category", "OTP", "Savings amount"],
            "answer": "OTP"
        }
    }
]


def safe_float(value, default=0.0):
    try:
        cleaned = str(value).replace(",", "").strip()
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def calculate_totals():
    total_expense = sum(expense["amount"] for expense in expenses)
    remaining_balance = user_data["income"] - total_expense

    if user_data["goal"] > 0:
        savings_progress = int((remaining_balance / user_data["goal"]) * 100)
        savings_progress = max(0, min(savings_progress, 100))
    else:
        savings_progress = 0

    return total_expense, remaining_balance, savings_progress


def check_scam_message(text):
    original_text = text.strip()
    normalized_text = original_text.lower()

    if not original_text:
        return {
            "level": "No Message",
            "message": "Please paste a message to analyze.",
            "color": "warning",
            "reasons": ["No message was provided."],
            "scam_type": "Not available",
            "action": "Paste an SMS, email, UPI request, or suspicious message to continue."
        }

    high_risk_keywords = [
        "otp", "cvv", "upi pin", "password", "click here", "verify now",
        "account blocked", "account suspended", "kyc expired", "bank suspended",
        "update pan immediately", "send money", "pay now", "refund link",
        "claim prize", "gift card", "remote access", "apk file"
    ]

    medium_risk_keywords = [
        "urgent", "reward", "cashback", "free gift", "limited offer",
        "claim now", "lottery", "winner", "offer expires", "exclusive deal",
        "congratulations", "bonus", "prize"
    ]

    authority_keywords = [
        "bank", "reserve bank", "rbi", "income tax", "police", "customs",
        "courier", "electricity bill", "kyc", "upi", "paytm", "phonepe", "gpay"
    ]

    reasons = []
    score = 0
    scam_type = "General suspicious message"

    if any(keyword in normalized_text for keyword in high_risk_keywords):
        reasons.append("The message asks for sensitive details or pushes a risky action.")
        score += 4

    if any(keyword in normalized_text for keyword in medium_risk_keywords):
        reasons.append("The message uses urgency, rewards, or pressure tactics.")
        score += 2

    if any(keyword in normalized_text for keyword in authority_keywords):
        reasons.append("The sender claims to be a trusted service, bank, or authority.")
        score += 1

    if re.search(r"http[s]?://|www\.|bit\.ly|tinyurl|goo\.gl", normalized_text):
        reasons.append("The message contains a link that should be verified carefully.")
        score += 3

    if any(word in normalized_text for word in ["otp", "cvv", "upi pin", "password"]):
        reasons.append("It asks for private financial or account information.")
        score += 4
        scam_type = "Phishing / account takeover scam"

    if any(word in normalized_text for word in ["kyc", "bank", "account blocked", "verify now"]):
        scam_type = "Banking or KYC scam"

    if any(word in normalized_text for word in ["cashback", "reward", "lottery", "winner", "prize"]):
        scam_type = "Prize / reward scam"

    if any(word in normalized_text for word in ["send money", "pay now", "upi", "collect request"]):
        scam_type = "UPI / payment scam"

    if score >= 6:
        return {
            "level": "High Risk",
            "message": "This message shows multiple strong scam indicators. Do not click links, share details, or send money.",
            "color": "high-risk",
            "reasons": reasons or ["Multiple suspicious patterns were detected."],
            "scam_type": scam_type,
            "action": "Do not reply, do not click any link, do not share OTP/PIN/password, and verify only through the official app or website."
        }

    if score >= 3:
        return {
            "level": "Medium Risk",
            "message": "This message has suspicious elements. Verify the sender carefully before taking any action.",
            "color": "medium-risk",
            "reasons": reasons or ["Some suspicious patterns were detected."],
            "scam_type": scam_type,
            "action": "Pause before responding. Cross-check the message using the sender’s official website, app, or customer support number."
        }

    return {
        "level": "Low Risk",
        "message": "No strong scam pattern was detected, but you should still be careful with unknown messages and links.",
        "color": "low-risk",
        "reasons": ["No major phishing or payment scam triggers were found in the message."],
        "scam_type": "No clear scam pattern detected",
        "action": "Stay cautious, especially if the sender is unknown or asks you to click a link or share account information."
    }


def get_today_lesson(module):
    daily_lessons = module.get("daily_lessons", [])

    if not daily_lessons:
        return None

    today_day = date.today().day
    lesson_index = (today_day - 1) % len(daily_lessons)
    return daily_lessons[lesson_index]


def generate_ai_response(user_message):
    if model is None:
        return (
            "<p>Sakhi AI is currently unavailable because the Gemini API key is not configured on the server.</p>"
        )

    total_expense, remaining_balance, savings_progress = calculate_totals()

    user_context = f"""
    User name: {user_data['name']}
    Monthly income: {user_data['income']}
    Savings goal: {user_data['goal']}
    Total expenses: {total_expense}
    Remaining balance: {remaining_balance}
    Savings progress: {savings_progress}%
    """

    prompt = f"""
    You are Sakhi AI, a supportive financial wellness assistant for women.

    Use the user's current financial data below to answer:
    {user_context}

    User question:
    {user_message}

    Respond in clean, professional HTML only.
    Rules:
    - Use only simple HTML tags: <h3>, <p>, <ul>, <li>, <strong>, <br>
    - Make the answer well-structured and easy to read
    - Start with a short supportive introduction
    - If the user asks about budgeting, break the answer into sections
    - Use bullet points where helpful
    - Keep the tone warm, practical, and professional
    - Do not include markdown like ** or ##
    - Do not include ```html
    - Do not include <html>, <body>, or <head> tags
    """

    response = model.generate_content(prompt)
    return response.text


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_data["name"] = request.form.get("name", "").strip()
        user_data["income"] = safe_float(request.form.get("income", 0))
        user_data["goal"] = safe_float(request.form.get("goal", 0))
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount = safe_float(request.form.get("amount", 0))
        category = request.form.get("category", "").strip()

        if title and amount > 0 and category:
            expenses.append({
                "title": title,
                "amount": amount,
                "category": category
            })

    total_expense, remaining_balance, savings_progress = calculate_totals()

    return render_template(
        "dashboard.html",
        user=user_data,
        expenses=expenses,
        total_expense=total_expense,
        remaining_balance=remaining_balance,
        savings_progress=savings_progress
    )


@app.route("/scam-checker", methods=["GET", "POST"])
def scam_checker():
    result = None
    message = ""

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        result = check_scam_message(message)

    return render_template(
        "scam_checker.html",
        result=result,
        message=message
    )


@app.route("/learn")
def learn():
    return render_template("learn.html", modules=learning_modules)


@app.route("/sakhi-ai", methods=["GET", "POST"])
def sakhi_ai():
    user_message = ""
    bot_response = None

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()

        if user_message:
            try:
                bot_response = generate_ai_response(user_message)
            except Exception as e:
                error_text = str(e)

                if "429" in error_text or "quota" in error_text.lower():
                    bot_response = (
                        "<p>Sakhi AI is temporarily unavailable because the Gemini API quota has been exceeded. "
                        "Please try again later or check your Google AI quota and billing settings.</p>"
                    )
                else:
                    bot_response = f"<p>Something went wrong: {error_text}</p>"

    return render_template(
        "chatbot.html",
        user_message=user_message,
        bot_response=bot_response
    )


@app.route("/module/<int:module_id>", methods=["GET", "POST"])
def module_detail(module_id):
    selected_module = next((module for module in learning_modules if module["id"] == module_id), None)
    quiz_result = None

    if not selected_module:
        return "Module not found", 404

    today_lesson = get_today_lesson(selected_module)

    if request.method == "POST":
        selected_answer = request.form.get("answer")
        correct_answer = selected_module["quiz"]["answer"]

        if selected_answer == correct_answer:
            quiz_result = {
                "status": "correct",
                "message": "Correct answer! Great job."
            }
        else:
            quiz_result = {
                "status": "wrong",
                "message": f"Wrong answer. Correct answer is: {correct_answer}"
            }

    return render_template(
        "module_detail.html",
        module=selected_module,
        today_lesson=today_lesson,
        quiz_result=quiz_result
    )


if __name__ == "__main__":
    app.run(debug=True)