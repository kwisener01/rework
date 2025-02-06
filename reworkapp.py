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

        # 📌 Show Related Charts Based on Selected Discard Reason
        if selected_discard != "All":
            st.subheader(f"🛠 Actions Taken for Discard Reason: {selected_discard}")
            action_counts = filtered_df['Action'].value_counts().head(10)

            fig_action_filtered, ax_action_filtered = plt.subplots(figsize=(8, 5))
            sns.barplot(x=action_counts.values, y=action_counts.index, palette="Blues_r")
            plt.xlabel("Count")
            plt.ylabel("Action Taken")
            plt.title(f"Top 10 Actions for Discard Reason: {selected_discard}")
            st.pyplot(fig_action_filtered)

        # 📌 Show Related Charts Based on Selected Action
        if selected_action != "All":
            st.subheader(f"🗑 Discard Reasons for Action: {selected_action}")
            discard_counts = filtered_df['Discard reason'].value_counts().head(10)

            fig_discard_filtered, ax_discard_filtered = plt.subplots(figsize=(8, 5))
            sns.barplot(x=discard_counts.values, y=discard_counts.index, palette="Reds_r")
            plt.xlabel("Count")
            plt.ylabel("Discard Reason")
            plt.title(f"Top 10 Discard Reasons for Action: {selected_action}")
            st.pyplot(fig_discard_filtered)

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

        # 📌 Model Breakdown
        st.subheader("🚗 Breakdown of Models Affected")
        model_counts = filtered_df['Model'].value_counts().head(10)

        fig_model, ax_model = plt.subplots(figsize=(8, 5))
        sns.barplot(x=model_counts.values, y=model_counts.index, palette="Purples_r")
        plt.xlabel("Count")
        plt.ylabel("Model")
        plt.title("Top 10 Affected Models")
        st.pyplot(fig_model)

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
