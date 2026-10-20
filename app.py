import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ignuvo Planner", layout="wide")
st.title("🏭 Ignuvo - Monthly to Daily Production Plan")

# Sidebar Settings
st.sidebar.header("⚙️ Settings")
daily_capacity = st.sidebar.number_input("Total Capacity / Day", value=2000, min_value=100)
working_days = st.sidebar.number_input("Working Days in Month", value=26, min_value=1, max_value=31)
start_date = st.sidebar.date_input("Start Date")

uploaded_file = st.sidebar.file_uploader("Upload Monthly Excel", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.subheader("📊 Uploaded Monthly Data")
        st.dataframe(df.head(), use_container_width=True)

        # Auto-detect quantity column
        qty_col = None
        for col in df.columns:
            if 'qty' in str(col).lower() or 'quantity' in str(col).lower() or 'nos' in str(col).lower() or 'order' in str(col).lower():
                qty_col = col
                break
        if not qty_col:
            qty_col = df.columns[-1] # last column as qty

        st.info(f"Using Quantity Column: *{qty_col}*")

        if st.button("Generate Daily Plan", type="primary"):
            # Simple distribution logic
            total_monthly = df[qty_col].sum()
            per_day = total_monthly / working_days
            
            st.success(f"Generated! Total Monthly: {total_monthly} | Avg Per Day: {per_day:.1f}")

            # Create daily plan
            daily_plans = []
            for day in range(1, working_days + 1):
                daily_df = df.copy()
                daily_df['Daily Qty'] = (daily_df[qty_col] / working_days).round().astype(int)
                daily_df['Day'] = f"Day {day}"
                daily_plans.append(daily_df)
            
            final_plan = pd.concat(daily_plans)
            
            st.subheader("📅 Daily Plan Preview")
            st.dataframe(final_plan.head(50), use_container_width=True)

            # Download
            csv = final_plan.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Daily Plan as CSV", csv, "Ignuvo_Daily_Plan.csv", "text/csv")

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("👈 Please upload your Monthly Excel file from the sidebar to start.")
    st.markdown("""
    *Excel Format Expected:*
    - Column 1: Model / Item Name
    - Column 2: Quantity / Order Qty
    Example:
    | Model | Qty |
    |---|---| 
    | B-Cell | 5000 |
    """)
