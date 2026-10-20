import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(page_title="Lagnuvo - Daily Production", layout="wide")
st.title("Lagnuvo - Daily production sheet")

# Init
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame([
        {"Date": "05-10-26", "Item Code": "FG0389", "Item Name": "MILI 1350+ HOME UPS 12V-V23", "Qty": 150, "Produced": 105, "Balance": -45, "Remark": "power loss"},
        {"Date": "05-10-26", "Item Code": "FG0509", "Item Name": "ZEST LI-1500/12.8V HOME UPS", "Qty": 20, "Produced": 20, "Balance": 0, "Remark": ""},
    ])

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Tools")
    
    st.subheader("1. Excel Upload")
    uploaded = st.file_uploader("Excel File തിരഞ്ഞെടുക്കൂ", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded:
        try:
            # Try read
            xls = pd.ExcelFile(uploaded)
            sheet = st.selectbox("Sheet Select", xls.sheet_names)
            df_temp = pd.read_excel(xls, sheet_name=sheet)
            # Clean columns
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            st.write("Preview:", df_temp.head(3))
            
            # Auto map
            plan_col = st.selectbox("Qty / Plan Column ഏതാണ്?", df_temp.columns, index=len(df_temp.columns)-2 if len(df_temp.columns)>2 else 0)
            code_col = st.selectbox("Item Code Column", df_temp.columns, index=1 if len(df_temp.columns)>1 else 0)
            name_col = st.selectbox("Item Name Column", df_temp.columns, index=2 if len(df_temp.columns)>2 else 0)
            
            if st.button("✅ Load to Table", type="primary"):
                new_data = []
                for _, r in df_temp.iterrows():
                    try:
                        qty = int(pd.to_numeric(r.get(plan_col, 0), errors='coerce') or 0)
                        if qty == 0 and str(r.get(code_col,"")).strip() == "":
                            continue
                        new_data.append({
                            "Date": str(date.today().strftime("%d-%m-%y")),
                            "Item Code": str(r.get(code_col, "")),
                            "Item Name": str(r.get(name_col, "")),
                            "Qty": qty,
                            "Produced": 0,
                            "Balance": -qty,
                            "Remark": ""
                        })
                    except:
                        continue
                if new_data:
                    st.session_state.df = pd.DataFrame(new_data)
                    st.success(f"{len(new_data)} rows loaded!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    st.subheader("2. Excel-ൽ നിന്ന് Copy Paste")
    st.caption("Excel-ൽ നിന്ന് Ctrl+C ചെയ്ത് ഇവിടെ Ctrl+V ചെയ്യുക")
    pasted_text = st.text_area("Paste here", height=150, placeholder="Excel-ൽ നിന്ന് Copy ചെയ്ത് ഇവിടെ Paste ചെയ്യൂ...")
    if pasted_text.strip() and st.button("Paste Data Load ചെയ്യുക"):
        try:
            # Try to parse TSV pasted from Excel
            lines = pasted_text.strip().split("\n")
            new_data = []
            for line in lines:
                parts = line.split("\t") # Excel copy is tab-separated
                if len(parts) < 3:
                    parts = line.split(",")
                # Expect: Date, Code, Name, Qty, Produced, Remark or similar
                if len(parts) >= 3:
                    # Heuristic mapping
                    item_code = parts[1] if len(parts)>1 else parts[0]
                    item_name = parts[2] if len(parts)>2 else ""
                    qty = 0
                    try:
                        # find a number
                        for p in parts:
                            if p.strip().isdigit():
                                qty = int(p.strip())
                                break
                    except:
                        pass
                    new_data.append({
                        "Date": parts[0] if len(parts)>0 else str(date.today().strftime("%d-%m-%y")),
                        "Item Code": item_code,
                        "Item Name": item_name,
                        "Qty": qty,
                        "Produced": 0,
                        "Balance": -qty,
                        "Remark": parts[-1] if len(parts)>4 else ""
                    })
            if new_data:
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_data)], ignore_index=True)
                st.success("Pasted!")
                st.rerun()
        except Exception as e:
            st.error(f"Paste Error: {e}")

    st.divider()
    if st.button("➕ Add Empty Row"):
        new_row = pd.DataFrame([{"Date": str(date.today().strftime("%d-%m-%y")), "Item Code": "", "Item Name": "", "Qty": 0, "Produced": 0, "Balance": 0, "Remark": ""}])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()
    if st.button("🗑️ Clear All (None Remove)"):
        st.session_state.df = pd.DataFrame([{"Date": str(date.today().strftime("%d-%m-%y")), "Item Code": "", "Item Name": "", "Qty": 0, "Produced": 0, "Balance": 0, "Remark": ""}])
        st.rerun()

# --- MAIN TABLE ---
# Clean None
df_display = st.session_state.df.replace("None", "").replace("nan", "").fillna("")
# Remove fully empty None rows
df_display = df_display[~((df_display["Item Code"].astype(str).str.strip() == "") & (df_display["Item Name"].astype(str).str.strip() == "") & (df_display["Qty"].astype(str) == "0")) | (df_display["Item Code"] != "")]

# If empty after filter, keep one
if df_display.empty:
    df_display = pd.DataFrame([{"Date": str(date.today().strftime("%d-%m-%y")), "Item Code": "", "Item Name": "", "Qty": 0, "Produced": 0, "Balance": 0, "Remark": ""}])

edited_df = st.data_editor(
    df_display,
    num_rows="dynamic",
    use_container_width=True,
    height=650,
    key="editor_final"
)

# Auto Calc
if not edited_df.empty:
    edited_df["Qty"] = pd.to_numeric(edited_df["Qty"], errors='coerce').fillna(0).astype(int)
    edited_df["Produced"] = pd.to_numeric(edited_df["Produced"], errors='coerce').fillna(0).astype(int)
    edited_df["Balance"] = edited_df["Produced"] - edited_df["Qty"]
    # Keep only valid rows in session
    st.session_state.df = edited_df.replace("None", "").fillna("")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Qty", int(edited_df["Qty"].sum()))
    c2.metric("Total Produced", int(edited_df["Produced"].sum()))
    c3.metric("Pending", int((edited_df["Qty"] - edited_df["Produced"]).sum()))

# Downloads
col1, col2 = st.columns(2)
with col1:
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"Lagnuvo_Daily_{date.today()}.csv")
with col2:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False)
    st.download_button("📥 Download Excel", output.getvalue(), f"Lagnuvo_Daily_{date.today()}.xlsx")
