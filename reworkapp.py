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
# 🚀 TAB 1: MACHINE DATA ANALYSIS (With Date Range & Parts Run)
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

        # 📌 Date Range Selector
        min_date = data['Inspection Date'].min().date()
        max_date = data['Inspection Date'].max().date()
        start_date, end_date = st.date_input("📅 Select Date Range", [min_date, max_date], key="machine_date_range")

        # 📌 Filter Data Based on Selected Date Range
        data = data[(data['Inspection Date'].dt.date >= start_date) & (data['Inspection Date'].dt.date <= end_date)]

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

        # 📌 Calculate Parts Run per Hour
        parts_run_per_hour = data.groupby(['Date', 'Hour']).size()

        # 📌 Display summary statistics
        st.subheader("📊 Summary Statistics")
        st.write(f"🔹 **Average Interval:** {timedelta(seconds=avg_interval)} ({avg_interval:.2f} seconds)")
        st.write(f"🔹 **Total Downtime:** {timedelta(seconds=total_downtime)} ({total_downtime:.2f} seconds)")
        st.write(f"🔹 **Downtime Percentage:** {downtime_percentage:.2f}%")

        # 📌 Display hourly averages
        st.subheader("⏳ Hourly Averages")
        st.write(hourly_averages)

        # 📌 Display Number of Parts Run Per Hour
        st.subheader("⚙️ Parts Run Per Hour")
        st.write(parts_run_per_hour)

        # 📌 Parts Run Per Hour - Bar Chart
        st.subheader("📊 Parts Run Per Hour (Bar Chart)")
        fig_parts, ax_parts = plt.subplots(figsize=(10, 5))
        parts_run_per_hour.unstack().plot(kind='bar', stacked=True, ax=ax_parts, colormap="Blues_r")
        plt.xlabel("Hour")
        plt.ylabel("Number of Parts")
        plt.title("Parts Run Per Hour")
        plt.xticks(rotation=45)
        st.pyplot(fig_parts)

        # 📌 Option to download hourly parts run data as CSV
        st.download_button(
            label="📥 Download Parts Run Per Hour Data",
            data=parts_run_per_hour.reset_index().to_csv(index=False),
            file_name="parts_run_per_hour.csv",
            mime="text/csv"
        )

# ============================================================
# 🚀 TAB 2: REWORK DATA ANALYSIS (Enhanced with Interactive Graph Updates)
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
        df['NG Description'] = df['NG Description'].fillna("Unknown")
        df['Action'] = df['Action'].fillna("Unknown")
        df['Discard reason'] = df['Discard reason'].fillna("Unknown")
        df['Model'] = df['Model'].fillna("Unknown")

        # 📌 Convert Date Column
        df['Rework Date'] = pd.to_datetime(df['Rework Date'], errors='coerce')

        # 📌 Date Range Selector
        min_date = df['Rework Date'].min().date()
        max_date = df['Rework Date'].max().date()
        start_date, end_date = st.date_input("📅 Select Date Range", [min_date, max_date], key="rework_date_range")

        # 📌 Filter Data Based on Date
        df = df[(df['Rework Date'].dt.date >= start_date) & (df['Rework Date'].dt.date <= end_date)]

        # 📌 Rework Data Analysis with Interactive Graphs
        selected_discard = st.selectbox("🗑 Select Discard Reason to Analyze", ["All"] + df['Discard reason'].unique().tolist())
        selected_action = st.selectbox("🛠 Select Action to Analyze", ["All"] + df['Action'].unique().tolist())

        # 📌 Apply Filters
        filtered_df = df.copy()
        if selected_discard != "All":
            filtered_df = filtered_df[filtered_df['Discard reason'] == selected_discard]

        if selected_action != "All":
            filtered_df = filtered_df[filtered_df['Action'] == selected_action]

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
