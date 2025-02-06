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
# 🚀 TAB 1: MACHINE DATA ANALYSIS (With Utilization & Best/Worst Hours)
# ============================================================
with tab1:
    st.header("⚙️ Machine Data Analysis")

    # 📌 User Inputs for Custom Cycle Time & Breaks
    expected_cycle_time = st.number_input("🔢 Enter Expected Cycle Time (seconds):", min_value=1, value=30, step=1)
    break_time = st.number_input("☕ Enter Total Break Time (minutes):", min_value=0, value=15, step=1)
    lunch_time = st.number_input("🍽️ Enter Lunch Break Time (minutes):", min_value=0, value=30, step=1)
    utilization_option = st.checkbox("📈 Use 85% Utilization for Target Calculation", value=True)

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

        # 📌 Calculate hourly averages
        hourly_averages = data.groupby(['Date', 'Hour'])['Time Difference'].mean()

        # 📌 Calculate Parts Run per Hour
        parts_run_per_hour = data.groupby(['Date', 'Hour']).size()

        # 📌 Calculate Target Parts Per Hour
        if utilization_option:
            effective_cycle_time = expected_cycle_time / 0.85  # Adjust for 85% utilization
        else:
            effective_cycle_time = expected_cycle_time

        target_parts_per_hour = 3600 / effective_cycle_time  # 3600 seconds in an hour

        # 📌 Compare Actual vs. Target Parts Per Hour
        hourly_comparison = parts_run_per_hour.reset_index()
        hourly_comparison['Target Parts'] = target_parts_per_hour
        hourly_comparison['Difference'] = hourly_comparison[0] - hourly_comparison['Target Parts']
        hourly_comparison.rename(columns={0: "Actual Parts"}, inplace=True)

        # 📌 Display Summary Statistics
        st.subheader("📊 Summary Statistics")
        st.write(f"🔹 **Target Parts Per Hour (Based on {85 if utilization_option else 100}% Utilization):** {target_parts_per_hour:.2f}")
        st.write(f"🔹 **Total Downtime:** {timedelta(seconds=data['Downtime'].sum())} ({data['Downtime'].sum():.2f} seconds)")

        # 📌 Display Hourly Performance Comparison
        st.subheader("📊 Hourly Performance: Actual vs. Target")
        st.write(hourly_comparison)

        # 📌 Display Number of Parts Run Per Hour - Bar Chart
        st.subheader("📊 Parts Run Per Hour (Bar Chart)")
        fig_parts, ax_parts = plt.subplots(figsize=(10, 5))
        sns.barplot(x=hourly_comparison["Hour"], y=hourly_comparison["Actual Parts"], color="blue", label="Actual Parts")
        sns.lineplot(x=hourly_comparison["Hour"], y=hourly_comparison["Target Parts"], color="red", marker="o", label="Target Parts", ax=ax_parts)
        plt.xlabel("Hour")
        plt.ylabel("Number of Parts")
        plt.title("Parts Run Per Hour vs Target")
        plt.legend()
        st.pyplot(fig_parts)

        # 📌 Find Best and Worst Hours
        best_hour = hourly_comparison.loc[hourly_comparison["Difference"].idxmax()]
        worst_hour = hourly_comparison.loc[hourly_comparison["Difference"].idxmin()]

        st.subheader("🏆 Best & Worst Hours")
        st.write(f"✅ **Best Hour:** {int(best_hour['Hour'])}:00 with **{int(best_hour['Actual Parts'])} parts** (Target: {int(best_hour['Target Parts'])})")
        st.write(f"❌ **Worst Hour:** {int(worst_hour['Hour'])}:00 with **{int(worst_hour['Actual Parts'])} parts** (Target: {int(worst_hour['Target Parts'])})")

        # 📌 Option to download hourly performance data
        st.download_button(
            label="📥 Download Hourly Performance Data",
            data=hourly_comparison.to_csv(index=False),
            file_name="hourly_performance.csv",
            mime="text/csv"
        )

# ============================================================
# 🚀 TAB 2: REWORK DATA ANALYSIS (Remains the Same)
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

        # 📌 Save Filtered Data
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Filtered Data")
        output.seek(0)

        st.download_button(
            label="📥 Download Filtered Data (Excel)",
            data=output,
            file_name="Filtered_Rework_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
