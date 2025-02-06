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
# 🚀 TAB 2: REWORK DATA ANALYSIS (With Date & Model Selection)
# ============================================================
with tab2:
    st.header("🔍 Rework Data Analysis")

    # 📌 File Upload
    rework_file = st.file_uploader("📂 Upload Rework Data CSV", type="csv", key="rework_upload")

    if rework_file is not None:
        df = pd.read_csv(rework_file)

        # 📌 Clean Column Names
        df.columns = df.columns.str.strip()

        # 📌 Standardize Text Fields
        df['NG Part'] = df['NG Part'].astype(str).str.strip().str.upper()
        df['NG Detail'] = df['NG Detail'].astype(str).str.strip().str.upper()
        df['NG Description'] = df['NG Description'].fillna("Unknown")
        df['Action'] = df['Action'].fillna("Unknown")
        df['Discard reason'] = df['Discard reason'].fillna("Unknown")
        df['Model'] = df['Model'].fillna("Unknown")

        # 📌 Convert Date Column
        df['Rework Date'] = pd.to_datetime(df['Rework Date'], errors='coerce')

        # 📌 Date Range Selector
        min_date = df['Rework Date'].min().date()
        max_date = df['Rework Date'].max().date()
        start_date, end_date = st.date_input("📅 Select Date Range", [min_date, max_date])

        # 📌 Filter Data Based on Date
        df = df[(df['Rework Date'].dt.date >= start_date) & (df['Rework Date'].dt.date <= end_date)]

        # 📌 Pareto Analysis - Discard Reason
        st.subheader("🗑️ Pareto Chart of Discard Reasons")
        discard_counts = df['Discard reason'].value_counts()
        cumulative_percentage = discard_counts.cumsum() / discard_counts.sum() * 100

        fig_discard, ax1 = plt.subplots(figsize=(10, 6))
        ax1.bar(discard_counts.index[:10], discard_counts.values[:10], color='red', alpha=0.7)
        ax1.set_ylabel('Frequency', color='red')
        ax1.set_xticklabels(discard_counts.index[:10], rotation=45, ha='right')

        ax2 = ax1.twinx()
        ax2.plot(discard_counts.index[:10], cumulative_percentage[:10], color='black', marker='o', linestyle='dashed')
        ax2.set_ylabel('Cumulative Percentage', color='black')
        ax2.axhline(y=80, color='gray', linestyle='dotted')

        plt.title('Pareto Chart of Top 10 Discard Reasons')
        st.pyplot(fig_discard)

        # 📌 Pareto Analysis - Action
        st.subheader("🛠 Pareto Chart of Actions Taken")
        action_counts = df['Action'].value_counts()
        cumulative_percentage = action_counts.cumsum() / action_counts.sum() * 100

        fig_action, ax3 = plt.subplots(figsize=(10, 6))
        ax3.bar(action_counts.index[:10], action_counts.values[:10], color='blue', alpha=0.7)
        ax3.set_ylabel('Frequency', color='blue')
        ax3.set_xticklabels(action_counts.index[:10], rotation=45, ha='right')

        ax4 = ax3.twinx()
        ax4.plot(action_counts.index[:10], cumulative_percentage[:10], color='black', marker='o', linestyle='dashed')
        ax4.set_ylabel('Cumulative Percentage', color='black')
        ax4.axhline(y=80, color='gray', linestyle='dotted')

        plt.title('Pareto Chart of Top 10 Actions Taken')
        st.pyplot(fig_action)

        # 📌 Dropdown Filters
        selected_discard = st.selectbox("🗑 Select Discard Reason to Analyze", ["All"] + df['Discard reason'].unique().tolist())
        selected_action = st.selectbox("🛠 Select Action to Analyze", ["All"] + df['Action'].unique().tolist())

        # 📌 Apply Filters
        filtered_df = df.copy()
        if selected_discard != "All":
            filtered_df = filtered_df[filtered_df['Discard reason'] == selected_discard]

        if selected_action != "All":
            filtered_df = filtered_df[filtered_df['Action'] == selected_action]

        # 📌 Show Model Breakdown
        st.subheader("🚗 Breakdown of Models Affected")
        model_counts = filtered_df['Model'].value_counts().head(10)

        fig_model, ax_model = plt.subplots(figsize=(8, 5))
        sns.barplot(x=model_counts.values, y=model_counts.index, palette="Purples_r")
        plt.xlabel("Count")
        plt.ylabel("Model")
        plt.title("Top 10 Affected Models")
        st.pyplot(fig_model)

        # 📌 Trends Over Time
        st.subheader("📈 Trends Over Time")
        filtered_df['Rework Day'] = filtered_df['Rework Date'].dt.date
        daily_trends = filtered_df.groupby('Rework Day').size()

        fig_trend, ax_trend = plt.subplots(figsize=(10, 5))
        sns.lineplot(x=daily_trends.index, y=daily_trends.values, marker='o', linestyle='-')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Number of Defects")
        plt.title("Trends of Rework Over Time")
        plt.grid()
        st.pyplot(fig_trend)

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
