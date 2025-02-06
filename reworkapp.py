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
# 🚀 TAB 1: MACHINE DATA ANALYSIS (Fixed KeyError Issue)
# ============================================================
with tab1:
    st.header("⚙️ Machine Data Analysis")

    # 📌 User Inputs
    expected_cycle_time = st.number_input("🔢 Enter Expected Cycle Time (seconds):", min_value=1, value=30, step=1)
    break_time = st.number_input("☕ Enter Total Break Time (minutes):", min_value=0, value=15, step=1)
    lunch_time = st.number_input("🍽️ Enter Lunch Break Time (minutes):", min_value=0, value=30, step=1)
    utilization = st.slider("📈 Select Utilization Percentage:", min_value=50, max_value=100, value=85, step=1)

    # 📌 File Upload
    uploaded_file = st.file_uploader("📂 Upload Machine Data CSV", type="csv", key="machine_upload")

    if uploaded_file is not None:
        # 📌 Load data
        data = pd.read_csv(uploaded_file)

        # 📌 Check if 'Inspection Date' exists
        if 'Inspection Date' not in data.columns:
            st.error("❌ Error: 'Inspection Date' column not found in uploaded file!")
        else:
            # 📌 Convert time column to datetime
            data['Inspection Date'] = pd.to_datetime(data['Inspection Date'], errors='coerce')

            # 📌 Ensure Date & Hour columns exist
            data['Date'] = data['Inspection Date'].dt.date
            data['Hour'] = data['Inspection Date'].dt.hour

            # 📌 Sort values
            data.sort_values(by='Inspection Date', inplace=True)

            # 📌 Date Range Selector
            min_date = data['Inspection Date'].min().date()
            max_date = data['Inspection Date'].max().date()
            start_date, end_date = st.date_input("📅 Select Date Range", [min_date, max_date], key="machine_date_range")

            # 📌 Filter Data Based on Selected Date Range
            data = data[(data['Inspection Date'].dt.date >= start_date) & (data['Inspection Date'].dt.date <= end_date)]

            # 📌 Recalculate Parts Run per Hour (Fix KeyError)
            if data.empty:
                st.warning("⚠️ No data available for the selected date range.")
            else:
                parts_run_per_hour = data.groupby(['Date', 'Hour']).size()

                # 📌 Calculate Target Parts Per Hour based on Utilization
                effective_cycle_time = expected_cycle_time / (utilization / 100)
                target_parts_per_hour = 3600 / effective_cycle_time  # 3600 seconds in an hour

                # 📌 Compare Actual vs. Target Parts Per Hour
                hourly_comparison = parts_run_per_hour.reset_index()
                hourly_comparison.rename(columns={0: "Actual Parts"}, inplace=True)
                hourly_comparison['Target Parts'] = target_parts_per_hour
                hourly_comparison['Difference'] = hourly_comparison["Actual Parts"] - hourly_comparison["Target Parts"]

                # 📌 Display Summary
                st.subheader("📊 Summary Statistics")
                st.write(f"🔹 **Selected Utilization:** {utilization}%")
                st.write(f"🔹 **Target Parts Per Hour:** {target_parts_per_hour:.2f}")

                # 📌 Display Hourly Performance
                st.subheader("📊 Hourly Performance: Actual vs. Target")
                st.write(hourly_comparison)

                # 📌 Option to download hourly performance data
                st.download_button(
                    label="📥 Download Hourly Performance Data",
                    data=hourly_comparison.to_csv(index=False),
                    file_name="hourly_performance.csv",
                    mime="text/csv"
                )
