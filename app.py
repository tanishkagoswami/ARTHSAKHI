from flask import Flask, render_template, request, redirect, url_for
from datetime import date
from dotenv import load_dotenv
import google.generativeai as genai
import os

app = Flask(__name__)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

user_data = {
    "name": "",
    "income": 0,
    "goal": 0
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
    text = text.lower()

    high_risk_keywords = [
        "otp", "urgent", "click here", "account blocked",
        "kyc expired", "verify now", "bank suspended", "update pan immediately"
    ]

    medium_risk_keywords = [
        "reward", "cashback", "free gift", "limited offer",
        "claim now", "lottery", "winner"
    ]

    for keyword in high_risk_keywords:
        if keyword in text:
            return {
                "level": "High Risk",
                "message": "This message looks suspicious. Do not click links or share personal details.",
                "color": "danger"
            }

    for keyword in medium_risk_keywords:
        if keyword in text:
            return {
                "level": "Medium Risk",
                "message": "This message may be suspicious. Verify the sender before taking action.",
                "color": "warning"
            }

    return {
        "level": "Low Risk",
        "message": "No strong scam pattern detected, but always stay cautious with unknown messages.",
        "color": "success"
    }


def get_today_lesson(module):
    daily_lessons = module.get("daily_lessons", [])

    if not daily_lessons:
        return None

    today_day = date.today().day
    lesson_index = (today_day - 1) % len(daily_lessons)
    return daily_lessons[lesson_index]


def generate_ai_response(user_message):
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

    Rules:
    - Give practical, simple, supportive advice.
    - Focus on budgeting, saving, scam awareness, and financial discipline.
    - Do not claim to be a licensed financial advisor.
    - Keep the answer short and clear.
    - End with: This is educational guidance, not professional financial advice.
    """

    response = model.generate_content(prompt)
    return response.text


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_data["name"] = request.form.get("name", "")
        user_data["income"] = float(request.form.get("income", 0))
        user_data["goal"] = float(request.form.get("goal", 0))
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        title = request.form.get("title")
        amount = request.form.get("amount")
        category = request.form.get("category")

        if title and amount and category:
            expenses.append({
                "title": title,
                "amount": float(amount),
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
        message = request.form.get("message", "")
        result = check_scam_message(message)

    return render_template("scam_checker.html", result=result, message=message)


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
                    bot_response = "Sakhi AI is temporarily unavailable because the Gemini API quota has been exceeded. Please try again later or check your Google AI quota and billing settings."
                else:
                    bot_response = f"Something went wrong: {error_text}"

    return render_template(
        "chatbot.html",
        user_message=user_message,
        bot_response=bot_response
    )


@app.route("/module/<int:module_id>", methods=["GET", "POST"])
def module_detail(module_id):
    selected_module = None
    quiz_result = None

    for module in learning_modules:
        if module["id"] == module_id:
            selected_module = module
            break

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