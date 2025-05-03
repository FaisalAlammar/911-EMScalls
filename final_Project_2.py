import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="911 Emergency Analysis")

# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv('911.csv')
    df = df.dropna().copy()
    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
    df['Reason'] = df['title'].apply(lambda x: x.split(':')[0])
    df['hour'] = df['timeStamp'].dt.hour
    df['emergency_type'] = df['Reason']
    df['month'] = df['timeStamp'].dt.to_period('M').dt.to_timestamp()
    return df

df_clean = load_data()

# Overview Header
st.title("📞 911 Emergency Calls Analysis")

# Overview Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Calls", len(df_clean))
with col2:
    st.metric("Unique Townships", df_clean['twp'].nunique())
with col3:
    st.metric("Date Range", f"{df_clean['timeStamp'].min().date()} ➔ {df_clean['timeStamp'].max().date()}")

# Sidebar filters
st.sidebar.header("Filters")
analysis_type = st.sidebar.selectbox(
    "Select Analysis",
    ["All Visualizations", "Heatmap", "Accident Reasons", "Hourly Trends", 
     "Call Type Distribution", "Vehicle Accident Trends", "Fire", "Fall", "Top Addresses"]
)

# ===== 1. Incident Heatmap =====
if analysis_type in ["All Visualizations", "Heatmap"]:
    st.markdown("---")
    st.header("🗺️ Incident Heatmap")
    m = folium.Map(location=[df_clean['lat'].mean(), df_clean['lng'].mean()], zoom_start=11)
    HeatMap(data=df_clean[['lat', 'lng']].dropna().values, radius=10).add_to(m)
    st_folium(m, width=1500, height=600)

# ===== 2. Accident Reasons by Township =====
if analysis_type in ["All Visualizations", "Accident Reasons"]:
    st.markdown("---")
    st.header("📌 Accident Reasons by Township")
    df_grouped = df_clean.groupby(['twp', 'Reason']).size().unstack().fillna(0)
    fig, ax = plt.subplots(figsize=(15, 6))
    df_grouped.plot(kind='bar', stacked=True, ax=ax)
    plt.title('Accident Reasons by Township')
    plt.tight_layout()
    st.pyplot(fig)

# ===== 3. Hourly Emergency Trends =====
if analysis_type in ["All Visualizations", "Hourly Trends"]: 
    st.markdown("---")
    st.header("⏰ Hourly Emergency Trends")
    hourly = df_clean.groupby(['hour', 'emergency_type']).size().reset_index(name='count')
    fig2 = px.line(
        hourly,
        x='hour',
        y='count',
        color='emergency_type',
        title='Hourly Emergency Type Trends'
    )
    st.plotly_chart(fig2, use_container_width=True)

# ===== 4. Call Type Distribution =====
if analysis_type in ["All Visualizations", "Call Type Distribution"]:
    st.markdown("---")
    st.header("📊 Call Type Distribution")
    title_counts = df_clean['title'].value_counts().reset_index()
    title_counts.columns = ['Call Type', 'Frequency']
    fig1 = px.bar(title_counts.head(20),
                 x='Call Type',
                 y='Frequency',
                 title='Distribution of Calls (Top 20)',
                 labels={'Call Type': 'Call type', 'Frequency': 'Total count'},
                 template='plotly_white')
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

# ===== 5. Vehicle Accident Trends =====
if analysis_type in ["All Visualizations", "Vehicle Accident Trends"]:
    st.markdown("---")
    st.header("🚗 Vehicle Accident Trends")
    df_vehicle = df_clean[df_clean['title'].str.contains('VEHICLE ACCIDENT', case=False, na=False)].copy()
    twp_counts = df_vehicle['twp'].value_counts()
    selected_twp = pd.concat([twp_counts.head(5), twp_counts.tail(5)]).index
    filtered_df = df_vehicle[df_vehicle['twp'].isin(selected_twp)].copy()
    monthly_grouped = filtered_df.groupby(['month', 'twp']).size().reset_index(name='count')
    fig5 = px.line(
        monthly_grouped,
        x='month',
        y='count',
        color='twp',
        title='Monthly Vehicle Accident Trends - Top & Bottom 5 Townships'
    )
    st.plotly_chart(fig5, use_container_width=True)

# ===== 6. Fire Incidents =====
if analysis_type in ["All Visualizations", "Fire"]:
    st.markdown("---")
    st.header("🔥 Fire Incident Map")
    df_fire = df_clean[df_clean['title'].str.startswith('Fire')].copy()
    if not df_fire.empty:
        m_fire = folium.Map(location=[df_fire['lat'].mean(), df_fire['lng'].mean()], zoom_start=11)
        HeatMap(data=df_fire[['lat', 'lng']].dropna().values, radius=10).add_to(m_fire)
        st_folium(m_fire, width=1500, height=600)

# ===== 7. Fall Incidents =====
if analysis_type in ["All Visualizations", "Fall"]:
    st.markdown("---")
    st.header(" Fall Incident Analysis")
    df_fall = df_clean[df_clean['title'].str.contains('Fall', case=False, na=False)].copy()
    if not df_fall.empty:
        df_fall['Season'] = df_fall['timeStamp'].dt.month.apply(
            lambda x: 'Winter' if x in [12, 1, 2] else 'Rest of Year'
        )
        fall_season_counts = df_fall['Season'].value_counts().reset_index()
        fall_season_counts.columns = ['Season', 'Fall Incidents']
        fig4 = px.bar(fall_season_counts,
                     x='Season',
                     y='Fall Incidents',
                     color='Season',
                     title='Fall Incidents: Winter vs Rest of Year')
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ===== 8. Top Addresses =====
if analysis_type in ["All Visualizations", "Top Addresses"]:
    st.markdown("---")
    st.header("🏠 Top Addresses with Most Incidents")
    top_addr = df_clean['addr'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    top_addr.plot(kind='barh', color='skyblue', ax=ax)
    plt.title('Top 10 Addresses with Most Incidents')
    plt.xlabel('Number of Incidents')
    plt.ylabel('Address')
    plt.gca().invert_yaxis()
    plt.grid(True)
    st.pyplot(fig)
