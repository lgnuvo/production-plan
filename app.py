import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ignuvo Planner", layout="wide")
st.title("🏭 Ignuvo - Monthly to Daily Production Plan")

st.sidebar.header("⚙️ Settings")
daily_capacity = st.sidebar.number_input("Total Capacity / Day", value=2000)
working_days = st.sidebar.number_input("Working Days in Month", value=26)
start_date = st.sidebar.date_input("Start Date")
uploaded_file = st.sidebar.file_uploader("Upload Monthly Excel", type=["xlsx", "xls"])

if uploaded_file:
    # Read file - try to find correct header row
    df_raw = pd.read_excel(uploaded_file, header=None)
    header_row_idx = 0
    for i, row in df_raw.head(10).iterrows():
        row_str = " ".join([str(x) for x in row.values]).lower()
        if "item code" in row_str or "item name" in row_str:
            header_row_idx = i
            break
    
    df = pd.read_excel(uploaded_file, header=header_row_idx)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Clean up: Remove empty rows
    df = df.dropna(subset=[df.columns[1], df.columns[2]], how='all')
    
    st.subheader("📊 Uploaded Monthly Data")
    st.dataframe(df.head(20), use_container_width=True)

    # Auto-detect Plan Qty column - Priority to Oct Plan / Plan
    qty_col = None
    for col in df.columns:
        cl = str(col).lower()
        if "oct plan" in cl or "plan" in cl and "oct" in cl:
            qty_col = col
            break
    if not qty_col:
        for col in df.columns:
            cl = str(col).lower()
            if "plan" in cl or "requirement" in cl or "qty" in cl:
                qty_col = col
                break
    
    if not qty_col:
        st.error(f"Could not find Plan Quantity column! Columns found: {list(df.columns)}")
        st.stop()

    st.success(f"✅ Detected Monthly Quantity Column: *{qty_col}* | Total: {pd.to_numeric(df[qty_col], errors='coerce').sum()}")

    # Detect Item Name / Code columns
    item_code_col = next((c for c in df.columns if "item code" in str(c).lower()), df.columns[1])
    item_name_col = next((c for c in df.columns if "item name" in str(c).lower()), df.columns[2])

    if st.button("Generate Daily Plan", type="primary"):
        # Convert qty to numeric
        df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0).astype(int)
        df = df[df[qty_col] > 0] # Only produce what is planned

        if df.empty:
            st.warning("No quantity in Oct Plan column! Please check Excel.")
            st.stop()

        # Generate daily distribution
        daily_data = []
        for _, row in df.iterrows():
            total_qty = int(row[qty_col])
            per_day = total_qty / working_days
            base = total_qty // working_days
            remainder = total_qty % working_days
            
            for day in range(1, working_days + 1):
                qty_for_day = base + (1 if day <= remainder else 0)
                if qty_for_day > 0:
                    daily_data.append({
                        "Day": f"Day {day}",
                        "Date": pd.to_datetime(start_date) + pd.Timedelta(days=day-1),
                        "Item Code": row[item_code_col],
                        "Item Name": row[item_name_col],
                        "Daily Qty": qty_for_day,
                        "Monthly Total": total_qty
                    })
        
        final_plan = pd.DataFrame(daily_data)
        
        st.subheader(f"📅 Daily Plan - {len(final_plan)} Production Entries")
        
        # Summary per day
        summary = final_plan.groupby("Day")["Daily Qty"].sum().reset_index()
        st.bar_chart(summary.set_index("Day"))
        
        st.dataframe(final_plan, use_container_width=True)

        # Download buttons
        csv = final_plan.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Daily Plan CSV", csv, "Ignuvo_Daily_Plan.csv", "text/csv")
        
        # Also Excel
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_plan.to_excel(writer, index=False, sheet_name='Daily Plan')
            summary.to_excel(writer, index=False, sheet_name='Daily Summary')
        st.download_button("📥 Download as Excel", output.getvalue(), "Ignuvo_Daily_Plan.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("👈 Upload your 123.xlsx file from sidebar")
