import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

st.set_page_config(page_title="Ignuvo - Production Plan", layout="wide")
st.title("Ignuvo - Monthly to Daily Production Plan")

st.sidebar.header("Settings")
total_cap = st.sidebar.number_input("Total Factory Capacity / Day", value=150)
wd = st.sidebar.number_input("Working Days", value=26)
month = st.sidebar.text_input("Month (YYYY-MM)", value="2026-08")
uploaded = st.sidebar.file_uploader("Upload Monthly Excel", type=["xlsx","xls"])

st.info("Excel Format: Item Code | Item Name | Day Capacity | Monthly Plan")

if uploaded:
    df = pd.read_excel(uploaded)
    st.write("Loaded Data", df.head())
    code_col = st.selectbox("Item Code Column", df.columns, index=0)
    name_col = st.selectbox("Item Name Column", df.columns, index=1 if len(df.columns)>1 else 0)
    cap_col = st.selectbox("Day Capacity Column", df.columns, index=2 if len(df.columns)>2 else 0)
    plan_col = st.selectbox("Monthly Plan Column", df.columns, index=3 if len(df.columns)>3 else 0)
    
    if st.button("Generate Daily Plan"):
        monthly = []
        for _, r in df.iterrows():
            try:
                plan = float(r[plan_col])
                cap = float(r[cap_col])
                if plan>0 and cap>0:
                    monthly.append({"code": str(r[code_col]), "name": str(r[name_col]), "cap": cap, "plan": plan, "remain": plan})
            except:
                continue
        
        start = date.fromisoformat(month+"-01")
        dates = []
        d = start
        while len(dates) < wd:
            if d.weekday() != 6:
                dates.append(d)
            d += timedelta(days=1)
        
        daily_rows = []
        totals = []
        for dt in dates:
            remain_day = total_cap
            day_total = 0
            for item in sorted(monthly, key=lambda x: x["remain"], reverse=True):
                if item["remain"] <=0: continue
                if remain_day <=0: break
                prod = min(item["cap"], item["remain"], remain_day)
                if prod>0:
                    daily_rows.append({"Date": str(dt), "ItemCode": item["code"], "ItemName": item["name"], "DayCapacity": item["cap"], "MonthlyPlan": item["plan"], "DailyProduction": prod, "Balance": item["remain"]-prod})
                    item["remain"] -= prod
                    remain_day -= prod
                    day_total += prod
            totals.append({"Date": str(dt), "TotalProduction": day_total, "CapacityLeft": total_cap-day_total})
        
        daily_df = pd.DataFrame(daily_rows)
        total_df = pd.DataFrame(totals)
        summary = []
        for it in monthly:
            produced = it["plan"]-it["remain"]
            summary.append({"ItemCode": it["code"], "ItemName": it["name"], "MonthlyPlan": it["plan"], "Produced": produced, "Balance": it["remain"], "Status": "Done" if it["remain"]==0 else "Pending"})
        summary_df = pd.DataFrame(summary)
        
        st.success(f"Generated! Total Produced: {summary_df['Produced'].sum()}")
        tab1, tab2, tab3 = st.tabs(["Daily Detail", "Daily Totals", "Summary"])
        with tab1: st.dataframe(daily_df, use_container_width=True)
        with tab2: st.dataframe(total_df, use_container_width=True)
        with tab3: st.dataframe(summary_df, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            daily_df.to_excel(writer, sheet_name="Daily_Detail", index=False)
            total_df.to_excel(writer, sheet_name="Daily_Totals", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        st.download_button("Download Daily Plan Excel", output.getvalue(), file_name=f"Daily_Plan_{month}.xlsx")
else:
    st.warning("Monthly Plan Excel Upload ചെയ്യൂ")
