import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
from io import BytesIO

# 📌 Streamlit App Title
st.title("📊 Multi-Tool Data Analysis App")

# 📌 Create Tabs
tab1, tab2 = st.tabs(["⚙️ Machine Data Analysis", "🔍 Rework Data Analysis"])

# ============================================================
# 🚀 TAB 1: MACHINE DATA ANALYSIS (Now with Adjustable Utilization)
# ============================================================
with tab1:
    st.header("⚙️ Machine Data Analysis")

    # 📌 User Inputs for Custom Cycle Time, Breaks, and Utilization
    expected_cycle_time = st.number_input("🔢 Enter Expected Cycle Time (seconds):", min_value=1, value=30, step=1)
    break_time = st.number_input("☕ Enter Total Break Time (minutes):", min_value=0, value=15, step=1)
    lunch_time = st.number_input("🍽️ Enter Lunch Break Time (minutes):", min_value=0, value=30, step=1)
    utilization = st.slider("📈 Select Utilization Percentage:", min_value=50, max_value=100, value=85, step=1)

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

        # 📌 Calculate Parts Run per Hour
        data['Hour'] = data['Inspection Date'].dt.hour
        parts_run_per_hour = data.groupby(['Date', 'Hour']).size()

        # 📌 Calculate Target Parts Per Hour based on Utilization
        effective_cycle_time = expected_cycle_time / (utilization / 100)  # Adjust cycle time for utilization
        target_parts_per_hour = 3600 / effective_cycle_time  # 3600 seconds in an hour

        # 📌 Compare Actual vs. Target Parts Per Hour
        hourly_comparison = parts_run_per_hour.reset_index()
        hourly_comparison['Target Parts'] = target_parts_per_hour
        hourly_comparison['Difference'] = hourly_comparison[0] - hourly_comparison['Target Parts']
        hourly_comparison.rename(columns={0: "Actual Parts"}, inplace=True)

        # 📌 Display Summary Statistics
        st.subheader("📊 Summary Statistics")
        st.write(f"🔹 **Selected Utilization:** {utilization}%")
        st.write(f"🔹 **Target Parts Per Hour:** {target_parts_per_hour:.2f}")

        # 📌 Display Hourly Performance Comparison
        st.subheader("📊 Hourly Performance: Actual vs. Target")
        st.write(hourly_comparison)

        # 📌 Option to download hourly performance data
        st.download_button(
            label="📥 Download Hourly Performance Data",
            data=hourly_comparison.to_csv(index=False),
            file_name="hourly_performance.csv",
            mime="text/csv"
        )

# ============================================================
# 🚀 TAB 2: REWORK DATA ANALYSIS (Fully Restored)
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

        # 📌 Dropdown Filters
        selected_discard = st.selectbox("🗑 Select Discard Reason", ["All"] + df['Discard reason'].unique().tolist())
        selected_action = st.selectbox("🛠 Select Action", ["All"] + df['Action'].unique().tolist())

        # 📌 Apply Filters
        filtered_df = df.copy()
        if selected_discard != "All":
            filtered_df = filtered_df[filtered_df['Discard reason'] == selected_discard]

        if selected_action != "All":
            filtered_df = filtered_df[filtered_df['Action'] == selected_action]

        # 📌 Pareto Chart - Discard Reasons
        st.subheader("🗑 Pareto Chart of Discard Reasons")
        discard_counts = df['Discard reason'].value_counts()
        fig_discard, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(x=discard_counts.index[:10], y=discard_counts.values[:10], palette="Reds_r")
        plt.xticks(rotation=45)
        plt.xlabel("Discard Reason")
        plt.ylabel("Frequency")
        plt.title("Top 10 Discard Reasons")
        st.pyplot(fig_discard)

        # 📌 Pareto Chart - Actions Taken
        st.subheader("🛠 Pareto Chart of Actions Taken")
        action_counts = df['Action'].value_counts()
        fig_action, ax2 = plt.subplots(figsize=(10, 6))
        sns.barplot(x=action_counts.index[:10], y=action_counts.values[:10], palette="Blues_r")
        plt.xticks(rotation=45)
        plt.xlabel("Action Taken")
        plt.ylabel("Frequency")
        plt.title("Top 10 Actions Taken")
        st.pyplot(fig_action)

        # 📌 Save Filtered Data
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Filtered Data")
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Rework Data (Excel)",
            data=output,
            file_name="Filtered_Rework_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
