import streamlit as st
import pandas as pd
import json
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Candidate Search Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data from SQLite
@st.cache_data
def load_resume_data_from_db():
    """Load parsed resume data from SQLite database."""
    db_path = Path("parsed_resumes.db")
    if not db_path.exists():
        st.error("Error: parsed_resumes.db not found. Please run the parsing cells first to create the database.")
        return pd.DataFrame(), []
    
    conn = sqlite3.connect(db_path)
    
    # Load all resumes into DataFrame
    df = pd.read_sql_query("SELECT * FROM resumes", conn)
    
    # Convert JSON strings back to Python objects for nested fields
    json_columns = ['education', 'work_experience', 'skills', 'sectors', 'certifications', 'languages']
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) and x != '' and x != '[]' else [])
    
    conn.close()
    
    # Convert to list of dicts for compatibility with existing code
    resumes = df.to_dict('records')
    
    return df, resumes

# Load data
df, resumes = load_resume_data_from_db()

if df.empty or not resumes:
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Candidates")

# Build SQL query for efficient filtering
@st.cache_data
def query_resumes(geographic_market=None, investment_approach=None, 
                   min_exp=None, max_exp=None, skill_search=None):
    """Query resumes from SQLite database with filters."""
    db_path = Path("parsed_resumes.db")
    conn = sqlite3.connect(db_path)
    
    query = "SELECT * FROM resumes WHERE 1=1"
    params = []
    
    if geographic_market and geographic_market != "All":
        query += " AND geographic_market = ?"
        params.append(geographic_market)
    
    if investment_approach and investment_approach != "All":
        query += " AND investment_approach = ?"
        params.append(investment_approach)
    
    if min_exp is not None:
        query += " AND years_experience >= ?"
        params.append(min_exp)
    
    if max_exp is not None:
        query += " AND years_experience <= ?"
        params.append(max_exp)
    
    if skill_search:
        query += " AND skills LIKE ?"
        params.append(f"%{skill_search}%")
    
    filtered_df = pd.read_sql_query(query, conn, params=params)
    
    # Convert JSON strings back to Python objects
    json_columns = ['education', 'work_experience', 'skills', 'sectors', 'certifications', 'languages']
    for col in json_columns:
        if col in filtered_df.columns:
            filtered_df[col] = filtered_df[col].apply(lambda x: json.loads(x) if pd.notna(x) and x != '' and x != '[]' else [])
    
    conn.close()
    return filtered_df

# Filters
geographic_markets = ["All"] + sorted(df["geographic_market"].dropna().unique().tolist())
selected_market = st.sidebar.selectbox("Geographic Market", geographic_markets)

investment_approaches = ["All"] + sorted(df["investment_approach"].dropna().unique().tolist())
selected_approach = st.sidebar.selectbox("Investment Approach", investment_approaches)

# Sector filter (multi-select)
all_sectors = set()
for resume in resumes:
    sectors = resume.get("sectors", [])
    if isinstance(sectors, list):
        all_sectors.update(sectors)
all_sectors = sorted(list(all_sectors))
selected_sectors = st.sidebar.multiselect("Sectors", all_sectors)

# Experience range
min_exp = int(df["years_experience"].min())
max_exp = int(df["years_experience"].max())
exp_range = st.sidebar.slider("Years of Experience", min_exp, max_exp, (min_exp, max_exp))

# Skills search
skill_search = st.sidebar.text_input("Search Skills", "")

# Certifications filter
all_certs = set()
for resume in resumes:
    certs = resume.get("certifications", [])
    if isinstance(certs, list):
        all_certs.update(certs)
all_certs = sorted(list(all_certs))
selected_certs = st.sidebar.multiselect("Certifications", all_certs)

# Apply filters using SQLite query
filtered_df = query_resumes(
    geographic_market=selected_market,
    investment_approach=selected_approach,
    min_exp=exp_range[0],
    max_exp=exp_range[1],
    skill_search=skill_search if skill_search else None
)

# Additional filters for sectors and certifications (applied in pandas since they're in JSON)
if selected_sectors:
    filtered_df = filtered_df[filtered_df["sectors"].apply(
        lambda x: isinstance(x, list) and any(sector in x for sector in selected_sectors)
    )]

if selected_certs:
    filtered_df = filtered_df[filtered_df["certifications"].apply(
        lambda x: isinstance(x, list) and any(cert in x for cert in selected_certs)
    )]

# Create display DataFrame with formatted columns
display_data = []
for _, row in filtered_df.iterrows():
    display_data.append({
        "Name": row.get("name", "Unknown"),
        "Location": row.get("location", ""),
        "Geographic Market": row.get("geographic_market", ""),
        "Years Experience": row.get("years_experience", 0),
        "Current Role": row.get("current_role", ""),
        "Current Company": row.get("current_company", ""),
        "Investment Approach": row.get("investment_approach", ""),
        "Skills": ", ".join(row.get("skills", [])) if isinstance(row.get("skills"), list) else "",
        "Sectors": ", ".join(row.get("sectors", [])) if isinstance(row.get("sectors"), list) else "",
        "Certifications": ", ".join(row.get("certifications", [])) if isinstance(row.get("certifications"), list) else "",
        "Email": row.get("email", ""),
        "Phone": row.get("phone", ""),
        "Education": ", ".join([f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}" 
                               for edu in (row.get("education", [])[:2] if isinstance(row.get("education"), list) else [])]),
        "Filename": row.get("filename", ""),
        "_full_data": row.to_dict()  # Store full data for detail view
    })

display_df = pd.DataFrame(display_data)

# Main content
st.title("🔍 Candidate Search Platform")
st.markdown("**Search and filter candidates for junior analyst positions**")

# Statistics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Candidates", len(df))
col2.metric("Filtered Results", len(display_df))
col3.metric("Geographic Markets", len(df["geographic_market"].dropna().unique()))
col4.metric("Avg Experience (years)", f"{df['years_experience'].mean():.1f}")

# Visualizations
st.header("📊 Candidate Insights")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # Geographic distribution
    if not filtered_df.empty:
        geo_counts = filtered_df["geographic_market"].value_counts()
        if len(geo_counts) > 0:
            fig_geo = px.pie(
                values=geo_counts.values,
                names=geo_counts.index,
                title="Distribution by Geographic Market",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_geo.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_geo, use_container_width=True)

with viz_col2:
    # Investment approach distribution
    if not filtered_df.empty:
        approach_counts = filtered_df["investment_approach"].value_counts()
        if len(approach_counts) > 0:
            fig_approach = px.bar(
                x=approach_counts.index,
                y=approach_counts.values,
                title="Distribution by Investment Approach",
                labels={"x": "Approach", "y": "Count"}
            )
            st.plotly_chart(fig_approach, use_container_width=True)

# Experience distribution
st.subheader("Experience Distribution")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    if not filtered_df.empty:
        fig_exp = px.histogram(
            filtered_df,
            x="years_experience",
            nbins=10,
            title="Years of Experience Distribution",
            labels={"years_experience": "Years of Experience", "count": "Number of Candidates"}
        )
        st.plotly_chart(fig_exp, use_container_width=True)

with exp_col2:
    # Top sectors
    if not filtered_df.empty:
        sector_counts = {}
        for sectors_list in filtered_df["sectors"]:
            if isinstance(sectors_list, list):
                for sector in sectors_list:
                    if sector.strip():
                        sector_counts[sector.strip()] = sector_counts.get(sector.strip(), 0) + 1
        
        if sector_counts:
            top_sectors = pd.DataFrame(list(sector_counts.items()), columns=["Sector", "Count"])
            top_sectors = top_sectors.sort_values("Count", ascending=False).head(10)
            fig_sectors = px.bar(
                top_sectors,
                x="Count",
                y="Sector",
                orientation='h',
                title="Top 10 Sectors",
                labels={"Count": "Number of Candidates"}
            )
            st.plotly_chart(fig_sectors, use_container_width=True)

# Results table
st.header("👥 Candidate Results")

# Display filtered results
results_display_df = display_df.drop(columns=["_full_data"])

if len(display_df) > 0:
    st.dataframe(
        results_display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Detail view
    st.subheader("Candidate Details")
    selected_name = st.selectbox("Select candidate for detailed view", display_df["Name"].tolist())
    
    if selected_name:
        selected_resume = display_df[display_df["Name"] == selected_name]["_full_data"].iloc[0]
        
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown(f"### {selected_resume.get('name', 'Unknown')}")
            st.markdown(f"**Location:** {selected_resume.get('location', 'N/A')}")
            st.markdown(f"**Geographic Market:** {selected_resume.get('geographic_market', 'N/A')}")
            st.markdown(f"**Email:** {selected_resume.get('email', 'N/A')}")
            st.markdown(f"**Phone:** {selected_resume.get('phone', 'N/A')}")
            st.markdown(f"**Years Experience:** {selected_resume.get('years_experience', 0)}")
            st.markdown(f"**Investment Approach:** {selected_resume.get('investment_approach', 'N/A')}")
        
        with detail_col2:
            st.markdown("### Education")
            education_list = selected_resume.get("education", [])
            if isinstance(education_list, list):
                for edu in education_list[:3]:
                    if isinstance(edu, dict):
                        st.markdown(f"- **{edu.get('degree', '')}** in {edu.get('field', '')}")
                        st.markdown(f"  {edu.get('institution', '')} ({edu.get('graduation_year', 'N/A')})")
            
            st.markdown("### Skills")
            skills = selected_resume.get("skills", [])
            if isinstance(skills, list) and skills:
                st.markdown(", ".join(skills[:10]))
            
            st.markdown("### Certifications")
            certs = selected_resume.get("certifications", [])
            if isinstance(certs, list) and certs:
                st.markdown(", ".join(certs))
            else:
                st.markdown("None")
        
        st.markdown("### Work Experience")
        work_exp_list = selected_resume.get("work_experience", [])
        if isinstance(work_exp_list, list):
            for exp in work_exp_list[:5]:
                if isinstance(exp, dict):
                    st.markdown(f"**{exp.get('title', 'N/A')}** at {exp.get('company', 'N/A')}")
                    st.markdown(f"*{exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')}*")
                    st.markdown(f"{exp.get('description', '')[:200]}...")
                    st.markdown("---")
        
        st.markdown("### Sectors")
        sectors = selected_resume.get("sectors", [])
        if isinstance(sectors, list) and sectors:
            st.markdown(", ".join(sectors))
        
else:
    st.info("No candidates match the selected filters. Please adjust your search criteria.")

# Export functionality
st.sidebar.markdown("---")
st.sidebar.header("📥 Export")
if st.sidebar.button("Export Filtered Results to CSV"):
    csv_string = results_display_df.to_csv(index=False)
    st.sidebar.download_button(
        label="Download CSV",
        data=csv_string,
        file_name="filtered_candidates.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("**Candidate Search Platform** | Built with Streamlit | Powered by SQLite")
