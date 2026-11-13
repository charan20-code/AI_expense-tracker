from datetime import date
import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR / "expenses.db"
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Education", "Health", "Entertainment", "Other"]

st.set_page_config(page_title="Pennywise | Expense Tracker", page_icon="💸", layout="wide")
LOCAL_MODEL = "llama3.2:3b"


def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect_db() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL
        )""")


def load_expenses():
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT id, title, amount, category, expense_date FROM expenses ORDER BY expense_date DESC, id DESC"
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows], columns=["id", "title", "amount", "category", "expense_date"])


def add_expense(title, amount, category, expense_date):
    with connect_db() as connection:
        connection.execute(
            "INSERT INTO expenses (title, amount, category, expense_date) VALUES (?, ?, ?, ?)",
            (title.strip(), float(amount), category, expense_date.isoformat()),
        )


def delete_expense(expense_id):
    with connect_db() as connection:
        connection.execute("DELETE FROM expenses WHERE id = ?", (int(expense_id),))


init_db()
st.title("💸 Pennywise")
st.caption("A simple personal expense tracker. Your records stay on this computer.")

expenses = load_expenses()
total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
category_count = expenses["category"].nunique() if not expenses.empty else 0

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Total spent", f"₹{total:,.2f}")
metric2.metric("Expenses logged", len(expenses))
metric3.metric("Categories used", category_count)

with st.expander("✨ AI Spending Coach", expanded=False):
    st.write("Ask for a short insight or spending summary based on your category totals.")
    st.caption("The coach runs locally through Ollama. Your expense summaries stay on this computer.")
    coach_question = st.text_input("What would you like to understand?", placeholder="Which category takes the largest share?")
    if st.button("Ask the coach", type="primary"):
        if expenses.empty:
            st.info("Add some expenses first so the coach has totals to analyze.")
        elif not coach_question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                category_totals = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
                summary = {
                    "total_spent_in_rupees": round(total, 2),
                    "expense_count": int(len(expenses)),
                    "category_totals_in_rupees": {name: round(float(value), 2) for name, value in category_totals.items()},
                }
                prompt = (
                    "You are a helpful personal expense tracking coach. Give concise, practical observations. "
                    "Do not invent trends or dates; the data contains only all-time totals. Do not give investment advice.\n\n"
                    f"Expense summary: {json.dumps(summary)}\n"
                    f"User question: {coach_question.strip()}"
                )
                request = Request(
                    "http://localhost:11434/api/chat",
                    data=json.dumps({
                        "model": LOCAL_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=180) as result:
                    answer = json.loads(result.read().decode("utf-8"))["message"]["content"]
                st.markdown(answer)
            except HTTPError as error:
                st.error(f"Ollama returned an error: {error.read().decode('utf-8', errors='replace')}")
            except URLError:
                st.error("Ollama is not running. Open the Ollama app, then try again.")
            except (KeyError, json.JSONDecodeError, TimeoutError) as error:
                st.error(f"Could not read the local model response: {error}")
    st.caption(f"Local model: {LOCAL_MODEL}. Download it once with `ollama pull {LOCAL_MODEL}`.")

st.divider()
left, right = st.columns([0.9, 1.1], gap="large")

with left:
    st.subheader("Add an expense")
    with st.form("add_expense_form", clear_on_submit=True):
        title = st.text_input("What did you spend on?", max_chars=80, placeholder="e.g. Lunch with friends")
        amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
        category = st.selectbox("Category", CATEGORIES)
        expense_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("Add expense", type="primary", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Enter a short description for this expense.")
            else:
                add_expense(title, amount, category, expense_date)
                st.success("Expense added.")
                st.rerun()

with right:
    st.subheader("Spending by category")
    if expenses.empty:
        st.info("Add your first expense to see the category breakdown.")
    else:
        category_totals = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
        st.bar_chart(category_totals, color="#7659e8", horizontal=True)

st.divider()
st.subheader("Your expenses")
if expenses.empty:
    st.info("Your expense list is empty. Add an expense above to get started.")
else:
    search = st.text_input("Search by description, category, or date", placeholder="Type to filter expenses")
    visible = expenses.copy()
    if search.strip():
        query = search.strip().lower()
        mask = (
            visible["title"].str.lower().str.contains(query, regex=False)
            | visible["category"].str.lower().str.contains(query, regex=False)
            | visible["expense_date"].str.contains(query, regex=False)
        )
        visible = visible[mask]
    st.dataframe(
        visible.rename(columns={"title": "Description", "amount": "Amount (₹)", "category": "Category", "expense_date": "Date"})
        .drop(columns=["id"]),
        hide_index=True,
        use_container_width=True,
        column_config={"Amount (₹)": st.column_config.NumberColumn(format="₹%.2f")},
    )
    if visible.empty:
        st.caption("No expenses match your search.")
    else:
        options = {f"{row.title} · ₹{row.amount:.2f} · {row.expense_date}": int(row.id) for row in visible.itertuples()}
        selected_label = st.selectbox("Choose an expense to delete", ["Select an expense"] + list(options))
        if selected_label != "Select an expense":
            if st.button("Delete selected expense", type="secondary"):
                delete_expense(options[selected_label])
                st.success("Expense deleted.")
                st.rerun()

st.caption("Local app · Saved in expenses.db on this computer")
