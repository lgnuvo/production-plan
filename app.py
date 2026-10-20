import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Ignuvo Production Plan", layout="wide")
st.title("Ignuvo - Daily Production Plan")

if 'orders' not in st.session_state:
    st.session_state.orders = []

st.sidebar.header("New Order")
with st.sidebar.form("order_form"):
    customer = st.text_input("Customer Name")
    product = st.text_input("Product / Item")
    qty = st.number_input("Quantity", min_value=1, value=100)
    due_date = st.date_input("Due Date", value=date.today())
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Add Order")
    if submitted and customer and product:
        st.session_state.orders.append({
            "Customer": customer,
            "Product": product,
            "Qty": qty,
            "Due Date": due_date.strftime("%Y-%m-%d"),
            "Priority": priority,
            "Status": "Pending"
        })
        st.success("Order Added!")

if st.session_state.orders:
    df = pd.DataFrame(st.session_state.orders)
    st.subheader("Production Queue")
    st.dataframe(df, use_container_width=True)
    total_qty = df['Qty'].sum()
    st.metric("Total Pending Qty", total_qty)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Plan as CSV", csv, "production_plan.csv", "text/csv")
else:
    st.info("No orders yet. Add an order from the sidebar.")