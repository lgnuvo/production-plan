import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Ignuvo - Daily Production", layout="wide")
st.title("📋 Ignuvo - Daily Production Sheet")
st.caption("Google Sheet പോലെ ഇവിടെ നേരിട്ട് Edit ചെയ്യാം - Balance Auto Calculate ആകും")

# Initialize data in session
if 'df' not in st.session_state:
    # Default data matching your screenshot
    st.session_state.df = pd.DataFrame([
        {"Date": "05-10-26", "Item Code": "FG0389", "Item Name": "MILI 1350+ HOME UPS 12V-V23", "Qty": 150, "Produced": 105, "Balance": -45, "Remark": "power loss"},
        {"Date": "05-10-26", "Item Code": "FG0509", "Item Name": "ZEST LI-1500/12.8V HOME UPS", "Qty": 20, "Produced": 20, "Balance": 0, "Remark": ""},
        {"Date": "06-10-26", "Item Code": "FG0385", "Item Name": "MILI 1100+ HOME UPS 12V-V23", "Qty": 0, "Produced": 0, "Balance": 0, "Remark": ""},
        {"Date": "06-10-26", "Item Code": "FG0387", "Item Name": "MILI 1650+ HOME UPS 12V-V23", "Qty": 100, "Produced": 0, "Balance": -100, "Remark": ""},
    ])

# Sidebar - Upload to auto-fill
with st.sidebar:
    st.header("⚙️ Tools")
    uploaded = st.file_uploader("Monthly Excel (Oct Plan) Upload ചെയ്താൽ Daily ആയി Auto-Fill ആകും", type=["xlsx"])
    if uploaded:
        try:
            df_raw = pd.read_excel(uploaded, header=None)
            h_idx = 0
            for i, row in df_raw.head(10).iterrows():
                if "Item Code" in str(row.values):
                    h_idx = i
                    break
            df_month = pd.read_excel(uploaded, header=h_idx)
            df_month.columns = [str(c).strip() for c in df_month.columns]
            plan_col = next((c for c in df_month.columns if "plan" in c.lower()), None)
            if plan_col:
                st.success(f"Found {plan_col} - {len(df_month)} items")
                if st.button("Generate Daily Sheet from this"):
                    code_col = next((c for c in df_month.columns if "code" in c.lower()), df_month.columns[1])
                    name_col = next((c for c in df_month.columns if "name" in c.lower()), df_month.columns[2])
                    new_data = []
                    for _, r in df_month.iterrows():
                        qty = pd.to_numeric(r.get(plan_col, 0), errors='coerce')
                        if qty and qty > 0:
                            new_data.append({
                                "Date": str(date.today().strftime("%d-%m-%y")),
                                "Item Code": r.get(code_col, ""),
                                "Item Name": r.get(name_col, ""),
                                "Qty": int(qty),
                                "Produced": 0,
                                "Balance": -int(qty),
                                "Remark": ""
                            })
                    st.session_state.df = pd.DataFrame(new_data)
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    if st.button("➕ Add Empty Row"):
        new_row = pd.DataFrame([{"Date": str(date.today().strftime("%d-%m-%y")), "Item Code": "", "Item Name": "", "Qty": 0, "Produced": 0, "Balance": 0, "Remark": ""}])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()
    
    if st.button("🗑️ Clear All"):
        st.session_state.df = pd.DataFrame(columns=["Date","Item Code","Item Name","Qty","Produced","Balance","Remark"])
        st.rerun()

st.info("👇 താഴെ Table-ൽ Double Click ചെയ്ത് Edit ചെയ്യാം. താഴെ + Click ചെയ്താൽ പുതിയ Row Add ആകും. Produced അടിച്ചാൽ Balance Auto ആകും.")

# Editable Table - Like Google Sheet
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    height=600,
    column_config={
        "Date": st.column_config.TextColumn("Date", width="small"),
        "Item Code": st.column_config.TextColumn("Item Code", width="small"),
        "Item Name": st.column_config.TextColumn("Item Name", width="large"),
        "Qty": st.column_config.NumberColumn("Qty", min_value=0, step=1),
        "Produced": st.column_config.NumberColumn("Produced", min_value=0, step=1),
        "Balance": st.column_config.NumberColumn("Balance", disabled=True, help="Auto: Produced - Qty"),
        "Remark": st.column_config.TextColumn("Remaek", width="medium"),
    },
    key="editor"
)

# Auto Calculate Balance
if not edited_df.empty:
    edited_df["Qty"] = pd.to_numeric(edited_df["Qty"], errors='coerce').fillna(0).astype(int)
    edited_df["Produced"] = pd.to_numeric(edited_df["Produced"], errors='coerce').fillna(0).astype(int)
    edited_df["Balance"] = edited_df["Produced"] - edited_df["Qty"]
    st.session_state.df = edited_df

    # Summary
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Qty", int(edited_df["Qty"].sum()))
    c2.metric("Total Produced", int(edited_df["Produced"].sum()))
    c3.metric("Total Balance", int(edited_df["Balance"].sum()))
    c4.metric("Pending", int((edited_df["Qty"] - edited_df["Produced"]).sum()))

# Download
col1, col2 = st.columns(2)
with col1:
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download as Excel CSV", csv, f"Ignuvo_Daily_{date.today()}.csv", "text/csv")
with col2:
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False)
    st.download_button("📥 Download as .xlsx", output.getvalue(), f"Ignuvo_Daily_{date.today()}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Link: ignuvo-planner.streamlit.app - ഇത് എല്ലാവർക്കും Open ആക്കി കൊടുത്താൽ എല്ലാവർക്കും ഇതുപോലെ Google Sheet പോലെ Edit ചെയ്യാം")
