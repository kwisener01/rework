import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import difflib  # For fuzzy matching
from datetime import timedelta
from io import BytesIO

# 📌 Streamlit App Title
st.title("📊 Multi-Tool Data Analysis App")

# 📌 Create Tabs
tab1, tab2 = st.tabs(["⚙️ Machine Data Analysis", "🔍 Rework Data Analysis"])

# ============================================================
# 🚀 TAB 1: MACHINE DATA ANALYSIS
# ============================================================
with tab1:
    st.header("⚙️ Machine Data Analysis")

    # 📌 User Inputs for Custom Cycle Time & Breaks
    expected_cycle_time = st.number_input("🔢 Enter Expected Cycle Time (seconds):", min_value=1, value=30, step=1)
    break_time = st.number_input("☕ Enter Total Break Time (minutes):", min_value=0, value=15, step=1)
    lunch_time = st.number_input("🍽️ Enter Lunch Break Time (minutes):", min_value=0, value=30, step=1)

    # 📌 File Upload
    uploaded_file = st.file_uploader("📂 Upload Machine Data CSV", type="csv", key="machine_upload")

    if uploaded_file is not None:
        # 📌 Load data
        data = pd.read_csv(uploaded_file)

        # 📌 Convert time column to datetime
        data['Inspection Date'] = pd.to_datetime(data['Inspection Date'])
        data.sort_values(by='Inspection Date', inplace=True)

        # 📌 Calculate time differences
        data['Time Difference'] = data['Inspection Date'].diff().dt.total_seconds()

        # 📌 Assign date and hour columns
        data['Date'] = data['Inspection Date'].dt.date
        data['Hour'] = data['Inspection Date'].dt.hour

        # 📌 Calculate downtime while excluding breaks and lunch
        total_break_time_seconds = (break_time + lunch_time) * 60  # Convert minutes to seconds
        total_operating_time = (data['Inspection Date'].max() - data['Inspection Date'].min()).total_seconds() - total_break_time_seconds

        data['Downtime'] = data['Time Difference'].apply(lambda x: max(0, x - expected_cycle_time))

        # 📌 Calculate statistics
        valid_intervals = data['Time Difference'].dropna()
        avg_interval = valid_intervals.mean()
        total_downtime = data['Downtime'].sum()

        # Ensure no division by zero
        downtime_percentage = (total_downtime / total_operating_time) * 100 if total_operating_time > 0 else 0

        # 📌 Calculate hourly averages
        hourly_averages = data.groupby(['Date', 'Hour'])['Time Difference'].mean()

        # 📌 Display summary statistics
        st.subheader("📊 Summary Statistics")
        st.write(f"🔹 **Average Interval:** {timedelta(seconds=avg_interval)} ({avg_interval:.2f} seconds)")
        st.write(f"🔹 **Total Downtime:** {timedelta(seconds=total_downtime)} ({total_downtime:.2f} seconds)")
        st.write(f"🔹 **Downtime Percentage:** {downtime_percentage:.2f}%")

        # 📌 Display hourly averages
        st.subheader("⏳ Hourly Averages")
        st.write(hourly_averages)

        # 📌 Option to download hourly averages as CSV
        st.download_button(
            label="📥 Download Hourly Averages",
            data=hourly_averages.reset_index().to_csv(index=False),
            file_name="hourly_averages.csv",
            mime="text/csv"
        )

# ============================================================
# 🚀 TAB 2: REWORK DATA ANALYSIS (Now with Action & Discard Filters)
# ============================================================
with tab2:
    st.header("🔍 Rework Data Analysis")

    # 📌 File Upload
    rework_file = st.file_uploader("📂 Upload Rework Data CSV", type="csv", key="rework_upload")

    if rework_file is not None:
        df = pd.read_csv(rework_file)

        # 📌 Clean Column Names
        df.columns = df.columns.str.strip()

        # 📌 Standardize NG Part and NG Detail text
        df['NG Part'] = df['NG Part'].astype(str).str.strip().str.upper()
        df['NG Detail'] = df['NG Detail'].astype(str).str.strip().str.upper()
        df['NG Description'] = df['NG Description'].fillna("Unknown")

        # 📌 Convert dates to datetime
        df['Rework Date'] = pd.to_datetime(df['Rework Date'], errors='coerce')

        # 📌 Action Filter
        selected_action = st.selectbox("🎯 Select an Action to Analyze Discard Reasons", ["All"] + df['Action'].dropna().unique().tolist())
        selected_discard = st.selectbox("🗑 Select a Discard Reason to Analyze Actions", ["All"] + df['Discard reason'].dropna().unique().tolist())

        # 📌 Filter Data Based on User Selection
        filtered_df = df.copy()
        if selected_action != "All":
            filtered_df = filtered_df[filtered_df['Action'] == selected_action]

        if selected_discard != "All":
            filtered_df = filtered_df[filtered_df['Discard reason'] == selected_discard]

        # 📌 Show Breakdown of Discard Reasons for Selected Action
        if selected_action != "All":
            st.subheader(f"🗑 Discard Reasons for Action: {selected_action}")
            discard_counts = filtered_df['Discard reason'].value_counts().head(10)
            fig_discard, ax_discard = plt.subplots(figsize=(8, 5))
            sns.barplot(x=discard_counts.values, y=discard_counts.index, palette="Reds_r")
            plt.xlabel("Count")
            plt.ylabel("Discard Reason")
            plt.title(f"Top Discard Reasons for {selected_action}")
            st.pyplot(fig_discard)

        # 📌 Show Breakdown of Actions for Selected Discard Reason
        if selected_discard != "All":
            st.subheader(f"🛠 Actions Taken for Discard Reason: {selected_discard}")
            action_counts = filtered_df['Action'].value_counts().head(10)
            fig_action, ax_action = plt.subplots(figsize=(8, 5))
            sns.barplot(x=action_counts.values, y=action_counts.index, palette="Blues_r")
            plt.xlabel("Count")
            plt.ylabel("Action Taken")
            plt.title(f"Top Actions for {selected_discard}")
            st.pyplot(fig_action)

        # 📌 Save Filtered Data
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Filtered Data")
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Data (Excel)",
            data=output,
            file_name="Filtered_Rework_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
