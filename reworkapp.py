import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import difflib
from io import BytesIO

# 📌 Function to Fix Typos & Standardize Defect Names
def fix_typos(df, column, threshold=0.8):
    unique_names = df[column].dropna().unique()
    corrected_names = {}
    
    for name in unique_names:
        match = difflib.get_close_matches(name, corrected_names.keys(), n=1, cutoff=threshold)
        if match:
            corrected_names[name] = match[0]
        else:
            corrected_names[name] = name

    df[column] = df[column].replace(corrected_names)
    return df

# 📌 Function to Analyze Data & Generate Insights
def analyze_rework_data(df):
    # Clean Column Names
    df.columns = df.columns.str.strip()

    # Standardize NG Part and NG Detail text
    df['NG Part'] = df['NG Part'].astype(str).str.strip().str.upper()
    df['NG Detail'] = df['NG Detail'].astype(str).str.strip().str.upper()
    df['NG Description'] = df['NG Description'].fillna("Unknown")

    # Convert dates to datetime
    df['Rework Date'] = pd.to_datetime(df['Rework Date'], errors='coerce')
    
    # Fix Typos in NG Description
    df = fix_typos(df, 'NG Description')

    # 📌 Generate Pareto Chart (Show Only Top 10 Issues)
    top_issues = df['NG Description'].value_counts().head(10)  # Get top 10 defects
    cumulative_percentage = top_issues.cumsum() / top_issues.sum() * 100

    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(top_issues.index, top_issues.values, color='blue', alpha=0.7)
    ax1.set_ylabel('Frequency', color='blue')
    ax1.set_xticklabels(top_issues.index, rotation=45, ha='right', fontsize=12)

    ax2 = ax1.twinx()
    ax2.plot(top_issues.index, cumulative_percentage, color='red', marker='o', linestyle='dashed')
    ax2.set_ylabel('Cumulative Percentage', color='red')
    ax2.axhline(y=80, color='gray', linestyle='dotted')

    plt.title('Pareto Chart of Top 10 Rework Reasons')

    # 📌 Defect Trends by Day
    df['Rework Day'] = df['Rework Date'].dt.date
    daily_defects = df.groupby('Rework Day').size()

    fig2, ax3 = plt.subplots(figsize=(10, 5))
    sns.lineplot(x=daily_defects.index, y=daily_defects.values, marker='o', linestyle='-')
    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Number of Defects")
    plt.title("Defect Trends Over Time")
    plt.grid()

    # 📌 Rework Distribution by Model
    model_counts = df['Model'].value_counts().head(10)

    fig3, ax4 = plt.subplots(figsize=(8, 5))
    sns.barplot(x=model_counts.index, y=model_counts.values, palette="Blues_r")
    plt.xticks(rotation=45)
    plt.xlabel("Model")
    plt.ylabel("Rework Count")
    plt.title("Rework Count by Model")

    return df, fig1, fig2, fig3

# 📌 Streamlit Web App
st.title("🔍 Rework Data Analysis App")
st.write("Upload your **CSV file** containing rework data to analyze trends and generate insights.")

# 📌 File Upload
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)

    # Analyze the Data
    cleaned_df, pareto_chart, trend_chart, model_chart = analyze_rework_data(df)

    # Display Insights
    st.subheader("📊 Pareto Analysis of Top 10 Defects")
    st.pyplot(pareto_chart)

    st.subheader("📈 Rework Trends Over Time")
    st.pyplot(trend_chart)

    st.subheader("🚗 Rework Count by Model")
    st.pyplot(model_chart)

    # 📌 Download Cleaned Data
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        cleaned_df.to_excel(writer, index=False, sheet_name="Cleaned Data")
    output.seek(0)

    st.download_button(
        label="📥 Download Cleaned Data (Excel)",
        data=output,
        file_name="Cleaned_Rework_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
