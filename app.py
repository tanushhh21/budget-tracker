import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import json

# ----------------------------
# Data Storage Setup
# ----------------------------
DATA_FILE = "finlight_data.json"

# Load data from file if exists
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state["monthly_allowance"] = data.get("monthly_allowance", 5000)
            st.session_state["expenses"] = pd.DataFrame(data.get("expenses", {}))
            st.session_state["saving_goals"] = data.get("saving_goals", [])
            st.session_state["recurring_expenses"] = data.get("recurring_expenses", [])

# Save current session state to file
def save_data():
    expenses = st.session_state["expenses"].copy()
    expenses["Date"] = expenses["Date"].astype(str)  # Convert date to string for JSON

    data = {
        "monthly_allowance": st.session_state["monthly_allowance"],
        "expenses": expenses.to_dict(),
        "saving_goals": st.session_state.get("saving_goals", []),
        "recurring_expenses": st.session_state.get("recurring_expenses", [])
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

if "initialized" not in st.session_state:
    st.session_state["monthly_allowance"] = 5000
    st.session_state["expenses"] = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])
    st.session_state["saving_goals"] = []
    st.session_state["recurring_expenses"] = []
    load_data()
    st.session_state["initialized"] = True

# ----------------------------
# App Title
# ----------------------------
st.title("💸 FinLight - Smart Finance OS for Students")

# ----------------------------
# Monthly Allowance
# ----------------------------
st.subheader("Set Your Monthly Allowance")
current_allowance = st.session_state["monthly_allowance"]
updated_allowance = st.number_input("Monthly Allowance (₹)", min_value=0, step=100, value=current_allowance)
st.session_state["monthly_allowance"] = updated_allowance
save_data()

st.markdown("---")

# ----------------------------
# Add an Expense
# ----------------------------
st.subheader("Add an Expense")
with st.form("expense_form"):
    date = st.date_input("Date", value=datetime.today())
    category = st.selectbox("Category", ["Food", "Books", "Rent", "Transport", "Entertainment", "Other"])
    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    note = st.text_input("Optional Note")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        new_expense = pd.DataFrame([{
            'Date': date,
            'Category': category,
            'Amount': amount,
            'Note': note
        }])
        st.session_state["expenses"] = pd.concat([st.session_state["expenses"], new_expense], ignore_index=True)
        st.success("Expense added!")
        save_data()

st.markdown("---")

# ----------------------------
# Recurring Expenses
# ----------------------------
st.subheader("🔁 Add Recurring Monthly Expenses")
with st.form("recurring_form"):
    recurring_name = st.text_input("Subscription Name (e.g., Netflix)")
    recurring_amount = st.number_input("Monthly Cost (₹)", min_value=0.0, step=10.0)
    recurring_category = st.selectbox("Category", ["Subscription", "Rent", "Utilities", "Other"])
    add_recurring = st.form_submit_button("Add Recurring Expense")

    if add_recurring and recurring_name:
        st.session_state["recurring_expenses"].append({
            "Name": recurring_name,
            "Amount": recurring_amount,
            "Category": recurring_category
        })
        st.success("Recurring expense added!")
        save_data()

if st.session_state["recurring_expenses"]:
    st.write("### Your Recurring Expenses")
    for r in st.session_state["recurring_expenses"]:
        st.markdown(f"**{r['Name']}** ({r['Category']}): ₹{r['Amount']}/month")

    total_recurring = sum(item['Amount'] for item in st.session_state["recurring_expenses"])
    st.markdown(f"**Total Monthly Recurring:** ₹{total_recurring}")
else:
    total_recurring = 0

st.markdown("---")

# ----------------------------
# Forecast Burn Rate (Improved)
# ----------------------------
st.subheader("📉 Forecast: When Will You Run Out of Money?")

expenses_df = st.session_state["expenses"].copy()
expenses_df["Date"] = pd.to_datetime(expenses_df["Date"]).dt.date

if not expenses_df.empty:
    today = datetime.today().date()
    start_of_month = today.replace(day=1)
    days_passed = (today - start_of_month).days + 1  # Include today
    total_spent = expenses_df[expenses_df["Date"] >= start_of_month]["Amount"].sum()
    average_daily_spend = total_spent / days_passed

    monthly_allowance = st.session_state["monthly_allowance"]
    estimated_days_left = int(monthly_allowance / average_daily_spend) if average_daily_spend > 0 else 9999

    st.metric("Average Daily Spend", f"₹{average_daily_spend:.2f}")
    st.metric("Estimated Days Your Budget Will Last", f"{estimated_days_left} days")

    if estimated_days_left < 30:
        st.warning("⚠️ At this rate, you may exceed your budget before the month ends.")
    else:
        st.success("✅ You're on track with your spending!")
else:
    st.info("Add some expenses to enable forecasting.")

st.markdown("---")

# ----------------------------
# Smart Spending Summary
# ----------------------------
st.subheader("📊 Smart Spending Summary")

total_spent = expenses_df["Amount"].sum()
remaining_budget = st.session_state["monthly_allowance"] - total_spent

col1, col2 = st.columns(2)
col1.metric("Total Spent So Far", f"₹{total_spent:.2f}")
col2.metric("Remaining Budget", f"₹{remaining_budget:.2f}")

st.markdown("---")

# ----------------------------
# Expense Breakdown & History
# ----------------------------
st.subheader("📂 Category Breakdown")
if not st.session_state["expenses"].empty:
    pie_data = st.session_state["expenses"].groupby("Category")["Amount"].sum().reset_index()
    fig = px.pie(pie_data, names='Category', values='Amount', title='Spending Breakdown')
    st.plotly_chart(fig)

    st.subheader("📋 Expense History")
    st.dataframe(st.session_state["expenses"], use_container_width=True)
else:
    st.info("No expenses added yet. Start tracking!")
