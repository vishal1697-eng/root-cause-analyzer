from flask import Flask, render_template, request, redirect
import sqlite3

# 🔹 OpenAI (optional - with fallback)
from openai import OpenAI
import os

client = OpenAI(api_key="your_actual_api_key_here")

app = Flask(__name__)

# 🔹 Create DB
def init_db():
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident TEXT,
        result TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# 🔹 AI + fallback logic
def analyze(incident):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Find root cause and solution for: {incident}"}
            ]
        )
        return response.choices[0].message.content

    except Exception:
        incident = incident.lower()

        if "server" in incident:
            return """Step 1: Checking server performance
Step 2: CPU usage is high

Root Cause: High CPU Usage
Solution: Restart server"""

        elif "database" in incident:
            return """Step 1: Checking database connection
Step 2: Connection failed

Root Cause: Invalid DB configuration
Solution: Fix DB credentials"""

        elif "login" in incident:
            return """Step 1: Login module checked
Step 2: Authentication failed

Root Cause: Invalid user input or backend issue
Solution: Validate input and fix API"""

        else:
            return """Step 1: Issue analyzed
Step 2: No known pattern

Root Cause: Unknown
Solution: Check logs"""


# 🔹 MAIN ROUTE
@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    search_query = request.args.get("search")

    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()

    # Save new incident
    if request.method == "POST":
        user_input = request.form["incident"]
        result = analyze(user_input)

        cursor.execute(
            "INSERT INTO incidents (incident, result) VALUES (?, ?)",
            (user_input, result)
        )
        conn.commit()

    # 🔍 Search feature
    if search_query:
        cursor.execute(
            "SELECT * FROM incidents WHERE incident LIKE ? ORDER BY id DESC",
            ('%' + search_query + '%',)
        )
    else:
        cursor.execute("SELECT * FROM incidents ORDER BY id DESC")

    history = cursor.fetchall()
    conn.close()

    return render_template("index.html", result=result, history=history)


# 🔹 DELETE ROUTE
@app.route("/delete")
def delete():
    conn = sqlite3.connect("incidents.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM incidents")
    conn.commit()
    conn.close()

    return redirect("/")  # 🔥 redirect back to home


# 🔹 RUN APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)