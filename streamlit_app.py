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

# Database selector at the top
st.header("📊 Data Source Selection")
database_options = {
    "parsed_resumes.db": "Original (10 resumes)",
    "parsed_resumes_large.db": "Large Dataset (scaled version)"
}

# Initialize database selection in session state
if 'selected_database' not in st.session_state:
    st.session_state.selected_database = "parsed_resumes.db"

# Database selector
selected_db = st.selectbox(
    "Select Database",
    options=list(database_options.keys()),
    format_func=lambda x: database_options[x]
)

# Update session state and clear cache when database changes
if st.session_state.selected_database != selected_db:
    st.session_state.selected_database = selected_db
    # Reset pagination when switching databases
    st.session_state.current_page = 0
    # Clear all cached data when switching databases
    st.cache_data.clear()

# Database connection helper
def get_db_connection(db_name=None):
    """Get SQLite database connection."""
    db_path = Path(db_name or st.session_state.selected_database)
    if not db_path.exists():
        if db_name is None:
            st.error(f"Error: {st.session_state.selected_database} not found. Please ensure the database file exists.")
        return None
    return sqlite3.connect(db_path)

# Helper function to execute database queries safely
def execute_db_query(db_name, query_func, default_return):
    """Execute a database query with proper error handling."""
    db_path = Path(db_name)
    if not db_path.exists():
        return default_return
    
    conn = sqlite3.connect(db_path)
    try:
        result = query_func(conn)
        conn.close()
        return result
    except Exception as e:
        conn.close()
        return default_return

# Get unique values for filters without loading all data
@st.cache_data # Cache for future calls
def get_unique_values(column_name, db_name):
    """Get unique values for a specific column from the database."""
    def query_func(conn):
        query = f"SELECT DISTINCT {column_name} FROM resumes WHERE {column_name} IS NOT NULL AND {column_name} != ''"
        result = pd.read_sql_query(query, conn)
        return sorted(result[column_name].dropna().unique().tolist())
    
    return execute_db_query(db_name, query_func, [])

# Get total count and statistics without loading all data
@st.cache_data
def get_database_stats(db_name):
    """Get database statistics without loading all data."""
    def query_func(conn):
        cursor = conn.cursor()
        total_count = cursor.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
        avg_exp = cursor.execute("SELECT AVG(years_experience) FROM resumes WHERE years_experience IS NOT NULL").fetchone()[0] or 0
        unique_markets = cursor.execute("SELECT COUNT(DISTINCT geographic_market) FROM resumes WHERE geographic_market IS NOT NULL").fetchone()[0]
        return {
            "total_count": total_count,
            "avg_exp": float(avg_exp),
            "unique_markets": unique_markets
        }
    
    return execute_db_query(db_name, query_func, {"total_count": 0, "avg_exp": 0, "unique_markets": 0})

# Get min/max experience range
@st.cache_data
def get_experience_range(db_name):
    """Get min and max years of experience from database."""
    def query_func(conn):
        cursor = conn.cursor()
        result = cursor.execute("SELECT MIN(years_experience), MAX(years_experience) FROM resumes WHERE years_experience IS NOT NULL").fetchone()
        min_exp = result[0] if result[0] is not None else 0
        max_exp = result[1] if result[1] is not None else 0
        return int(min_exp), int(max_exp)
    
    return execute_db_query(db_name, query_func, (0, 0))

# Get all unique values for list fields (requires parsing JSON)
@st.cache_data
def get_json_field_values(field_name, db_name):
    """Get all unique values from a JSON field (like sectors, certifications)."""
    def query_func(conn):
        query = f"SELECT {field_name} FROM resumes WHERE {field_name} IS NOT NULL AND {field_name} != '' AND {field_name} != '[]'"
        result = pd.read_sql_query(query, conn)
        
        all_values = set()
        for json_str in result[field_name]:
            try:
                values = json.loads(json_str)
                if isinstance(values, list):
                    all_values.update([v.strip() for v in values if v and v.strip()])
            except:
                continue
        
        return sorted(list(all_values))
    
    return execute_db_query(db_name, query_func, [])

# Sidebar filters
st.sidebar.header("🔍 Filter Candidates")

# Helper function to build JSON field filtering conditions
def build_json_field_filter(field_name, selected_values, where_clause, params):
    """Build SQL LIKE conditions for JSON field filtering."""
    if selected_values:
        conditions = []
        for value in selected_values:
            conditions.append(f"{field_name} LIKE ?")
            params.append(f'%"{value}"%')
        where_clause += " AND (" + " OR ".join(conditions) + ")"
    return where_clause

# Build SQL query for efficient filtering with pagination
def query_resumes(geographic_market=None, investment_approach=None,
                   min_exp=None, max_exp=None,
                   selected_skills=None, selected_sectors=None, selected_degrees=None,
                   selected_roles=None, selected_certs=None,
                   limit=50, offset=0):
    """Query resumes from SQLite database with filters and pagination."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(), 0

    # Build WHERE clause conditions
    where_clause = "WHERE 1=1"
    params = []

    if geographic_market and geographic_market != "All":
        where_clause += " AND geographic_market = ?"
        params.append(geographic_market)

    if investment_approach and investment_approach != "All":
        where_clause += " AND investment_approach = ?"
        params.append(investment_approach)

    if min_exp:
        where_clause += " AND years_experience >= ?"
        params.append(min_exp)

    if max_exp:
        where_clause += " AND years_experience <= ?"
        params.append(max_exp)

    # Filter by current role
    if selected_roles:
        placeholders = ','.join(['?'] * len(selected_roles))
        where_clause += f" AND current_role IN ({placeholders})"
        params.extend(selected_roles)

    # SQL filtering for JSON fields (skills, sectors, certifications)
    where_clause = build_json_field_filter("skills", selected_skills, where_clause, params)
    where_clause = build_json_field_filter("sectors", selected_sectors, where_clause, params)
    where_clause = build_json_field_filter("degrees", selected_degrees, where_clause, params)
    where_clause = build_json_field_filter("certifications", selected_certs, where_clause, params)
    
    # Get total count before pagination
    count_query = f"SELECT COUNT(*) FROM resumes {where_clause}"
    cursor = conn.cursor()
    total_count = cursor.execute(count_query, params).fetchone()[0]
    
    # Build main query with pagination
    query = f"SELECT * FROM resumes {where_clause} LIMIT ? OFFSET ?"
    query_params = params + [limit, offset]
    
    filtered_df = pd.read_sql_query(query, conn, params=query_params)
    
    # Convert JSON strings/lists back to Python objects
    json_columns = ['education', 'work_experience', 'skills', 'sectors', 'degrees', 'certifications']
    for col in json_columns:
        if col in filtered_df.columns:
            filtered_df[col] = filtered_df[col].apply(lambda x: json.loads(x) if pd.notna(x) and x != '' and x != '[]' else [])
    
    conn.close()
    return filtered_df, total_count

# Helper function to format list fields for display
def format_list_field(value, default=""):
    """Format a list field for display."""
    if isinstance(value, list) and value:
        return ", ".join(value)
    return default

# Create display DataFrame from filtered results
def create_display_dataframe(filtered_df, include_full_data=True):
    """Create a formatted display DataFrame from filtered results."""
    display_data = []
    for _, row in filtered_df.iterrows():
        display_row = {
            "ID": row.get("index", "Unknown"),
            "Name": row.get("name", "Unknown"),
            "Location": row.get("location", ""),
            "Geographic Market": row.get("geographic_market", ""),
            "Years Experience": row.get("years_experience", "N/A"),
            "Current Role": row.get("current_role", ""),
            "Current Company": row.get("current_company", ""),
            "Investment Approach": row.get("investment_approach", ""),
            "Skills": format_list_field(row.get("skills", [])),
            "Sectors": format_list_field(row.get("sectors", [])),
            "Degrees": format_list_field(row.get("degrees", [])),
            "Certifications": format_list_field(row.get("certifications", [])),
            "Email": row.get("email", ""),
            "Phone": row.get("phone", ""),
        }
        if include_full_data:
            display_row["_full_data"] = row.to_dict()
        display_data.append(display_row)
    
    return pd.DataFrame(display_data)

# Get database stats for display
db_stats = get_database_stats(st.session_state.selected_database)
exp_range_min, exp_range_max = get_experience_range(st.session_state.selected_database)

# Filters
geographic_markets = ["All"] + get_unique_values("geographic_market", st.session_state.selected_database)
selected_market = st.sidebar.selectbox("Geographic Market", geographic_markets)

investment_approaches = ["All"] + get_unique_values("investment_approach", st.session_state.selected_database)
selected_approach = st.sidebar.selectbox("Investment Approach", investment_approaches)

# Sector filter (multi-select)
all_sectors = get_json_field_values("sectors", st.session_state.selected_database)
selected_sectors = st.sidebar.multiselect("Sectors", all_sectors)

# Skills filter (multi-select)
all_skills = get_json_field_values("skills", st.session_state.selected_database)
selected_skills = st.sidebar.multiselect("Skills", all_skills)

# Degrees filter (multi-select)
all_degrees = get_json_field_values("degrees", st.session_state.selected_database)
selected_degrees = st.sidebar.multiselect("Degrees", all_degrees)

# Roles filter (multi-select)
all_roles = get_unique_values("current_role", st.session_state.selected_database)
selected_roles = st.sidebar.multiselect("Roles", all_roles)

# Certifications filter (multi-select)
all_certs = get_json_field_values("certifications", st.session_state.selected_database)
selected_certs = st.sidebar.multiselect("Certifications", all_certs)

# Experience range
if exp_range_min < exp_range_max:
    exp_range = st.sidebar.slider("Years of Experience", exp_range_min, exp_range_max, (exp_range_min, exp_range_max))
else:
    exp_range = (exp_range_min, exp_range_max)

# Pagination controls
st.sidebar.markdown("---")
st.sidebar.header("📄 Pagination")
page_size = st.sidebar.selectbox("Results per page", [25, 50, 100], index=1)  # Default to 50

# Initialize pagination state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

# Reset to first page when filters change (track filter state)
filter_key = f"{st.session_state.selected_database}_{selected_market}_{selected_approach}_{exp_range}_{selected_skills}_{selected_sectors}_{selected_certs}_{page_size}"
if 'last_filter_key' not in st.session_state:
    st.session_state.last_filter_key = filter_key

if st.session_state.last_filter_key != filter_key:
    st.session_state.current_page = 0
    st.session_state.last_filter_key = filter_key

# Apply filters using SQLite query with pagination
filtered_df, total_filtered_count = query_resumes(
    geographic_market=selected_market,
    investment_approach=selected_approach,
    min_exp=exp_range[0],
    max_exp=exp_range[1],
    selected_skills=selected_skills if selected_skills else None,
    selected_sectors=selected_sectors if selected_sectors else None,
    selected_degrees=selected_degrees if selected_degrees else None,
    selected_roles=selected_roles if selected_roles else None,
    selected_certs=selected_certs if selected_certs else None,
    limit=page_size,
    offset=st.session_state.current_page * page_size
)

# Calculate total pages
total_pages = (total_filtered_count + page_size - 1) // page_size if total_filtered_count > 0 else 1

# Ensure current_page is within valid bounds
if st.session_state.current_page < 0:
    st.session_state.current_page = 0
elif st.session_state.current_page >= total_pages and total_pages > 0:
    st.session_state.current_page = total_pages - 1

# Main content
st.title("🔍 Candidate Search Platform")
st.markdown("**Search and filter candidates for junior analyst positions**")

# Overall Statistics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Filtered Candidates", total_filtered_count)
col2.metric("Total Candidates", db_stats["total_count"])
col3.metric("Total Geographic Markets", db_stats["unique_markets"])
col4.metric("Avg Experience (years)", f"{db_stats['avg_exp']:.1f}")


# Get all filtered results for visualizations (without pagination, but limit to 10000 for performance)
viz_df, _ = query_resumes(
    geographic_market=selected_market,
    investment_approach=selected_approach,
    min_exp=exp_range[0],
    max_exp=exp_range[1],
    selected_skills=selected_skills if selected_skills else None,
    selected_sectors=selected_sectors if selected_sectors else None,
    selected_degrees=selected_degrees if selected_degrees else None,
    selected_roles=selected_roles if selected_roles else None,
    selected_certs=selected_certs if selected_certs else None,
    limit=10000,  # Limit to 10k for visualization performance
    offset=0
)

# Visualizations
st.header("📊 Candidate Insights")
st.caption(f"Visualizations based on up to 10,000 filtered results (showing {min(total_filtered_count, 10000)} candidates)")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # Geographic distribution
    if not viz_df.empty:
        geo_counts = viz_df["geographic_market"].value_counts()
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
    if not viz_df.empty:
        approach_counts = viz_df["investment_approach"].value_counts()
        if len(approach_counts) > 0:
            fig_approach = px.bar(
                x=approach_counts.index,
                y=approach_counts.values,
                title="Distribution by Investment Approach",
                labels={"x": "Approach", "y": "Count"}
            )
            st.plotly_chart(fig_approach, use_container_width=True)


viz_col3, viz_col4 = st.columns(2)

with viz_col3:
    if not viz_df.empty:
        fig_exp = px.histogram(
            viz_df,
            x="years_experience",
            nbins=10,
            title="Years of Experience Distribution",
            labels={"years_experience": "Years of Experience", "count": "Number of Candidates"}
        )
        st.plotly_chart(fig_exp, use_container_width=True)

with viz_col4:
    # Top sectors
    if not viz_df.empty:
        sector_counts = viz_df["sectors"].explode().value_counts()
        if len(sector_counts) > 0:
            top_sectors = sector_counts.sort_values(ascending=False).head(10)
            fig_sectors = px.bar(
                x=top_sectors.values,
                y=top_sectors.index,
                orientation='h',
                title="Top 10 Sectors",
                labels={"Count": "Number of Candidates"}
            )
            st.plotly_chart(fig_sectors, use_container_width=True)


viz_col5, viz_col6 = st.columns(2)

with viz_col5:
    if not viz_df.empty:
        skill_counts = viz_df["skills"].explode().value_counts()
        if len(skill_counts) > 0:
            top_skills = skill_counts.sort_values(ascending=False).head(10)
            fig_skills = px.bar(
                x=top_skills.values,
                y=top_skills.index,
                orientation='h',
                title="Top 10 Skills",
                labels={"Count": "Number of Candidates"}
            )
            st.plotly_chart(fig_skills, use_container_width=True)

with viz_col6:
    # Top sectors
    if not viz_df.empty:
        roles_counts = viz_df["current_role"].value_counts()
        if len(roles_counts) > 0:
            top_roles = roles_counts.sort_values(ascending=False).head(10)
            fig_roles = px.bar(
                x=top_roles.values,
                y=top_roles.index,
                orientation='h',
                title="Top 10 Roles/Titles",
                labels={"Count": "Number of Candidates"}
            )
            st.plotly_chart(fig_roles, use_container_width=True)

# Results table
st.header("👥 Candidate Results")

# Display pagination info
if total_filtered_count > 0:
    start_idx = st.session_state.current_page * page_size + 1
    end_idx = min((st.session_state.current_page + 1) * page_size, total_filtered_count)
    st.caption(f"Showing {start_idx}-{end_idx} of {total_filtered_count} candidates (Page {st.session_state.current_page + 1} of {total_pages})")

# Create display DataFrame with formatted columns
display_df = create_display_dataframe(filtered_df, include_full_data=True)

# Display filtered results
results_display_df = display_df.drop(columns=["_full_data"])

if len(display_df) > 0:
    st.dataframe(
        results_display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Pagination controls
    if total_pages > 1:
        pagination_col1, pagination_col2, pagination_col3, pagination_col4, pagination_col5 = st.columns([1, 1, 2, 1, 1])
        
        def go_to_first():
            st.session_state.current_page = 0
        
        def go_to_previous():
            if st.session_state.current_page > 0:
                st.session_state.current_page -= 1
        
        def go_to_next():
            if st.session_state.current_page < total_pages - 1:
                st.session_state.current_page += 1
        
        def go_to_last():
            st.session_state.current_page = total_pages - 1
        
        def go_to_page():
            if 'page_input_value' in st.session_state:
                new_page = st.session_state.page_input_value - 1
                if 0 <= new_page < total_pages:
                    st.session_state.current_page = new_page
        
        with pagination_col1:
            st.button("⏮️ First", disabled=(st.session_state.current_page == 0), on_click=go_to_first, use_container_width=True)
        
        with pagination_col2:
            st.button("◀️ Previous", disabled=(st.session_state.current_page == 0), on_click=go_to_previous, use_container_width=True)
        
        with pagination_col3:
            page_input = st.number_input(
                "Go to page",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page + 1,
                key="page_input_value",
                on_change=go_to_page
            )
        
        with pagination_col4:
            st.button("Next ▶️", disabled=(st.session_state.current_page >= total_pages - 1), on_click=go_to_next, use_container_width=True)
        
        with pagination_col5:
            st.button("Last ⏭️", disabled=(st.session_state.current_page >= total_pages - 1), on_click=go_to_last, use_container_width=True)
    
    # Detail view
    st.subheader("Candidate Details")
    selected_name = st.selectbox("Select candidate for detailed view", display_df.apply(lambda r: str(r['ID']) + ':' + r['Name'], axis=1).tolist())
    
    if selected_name:
        selected_resume = display_df[display_df["ID"] == int(selected_name.split(':')[0])]["_full_data"].iloc[0]
        
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown(f"### {selected_resume.get('name', 'Unknown')}")
            st.markdown(f"**Professional Summary:** {selected_resume.get('professional_summary', 'N/A')}")
            st.markdown(f"**Location:** {selected_resume.get('location', 'N/A')}")
            st.markdown(f"**Geographic Market:** {selected_resume.get('geographic_market', 'N/A')}")
            st.markdown(f"**Email:** {selected_resume.get('email', 'N/A')}")
            st.markdown(f"**Phone:** {selected_resume.get('phone', 'N/A')}")
            st.markdown(f"**Years Experience:** {selected_resume.get('years_experience', 'N/A')}")
            st.markdown(f"**Investment Approach:** {selected_resume.get('investment_approach', 'N/A')}")
            st.markdown(f"**Current Role:** {selected_resume.get('current_role', 'N/A')}")
            st.markdown(f"**Current Company:** {selected_resume.get('current_company', 'N/A')}")
        
        with detail_col2:
            # Display list fields (skills, sectors, certifications)
            list_fields = [
                ("Skills", "skills"),
                ("Sectors", "sectors"),
                ("Degress", "degrees"),
                ("Certifications", "certifications")
            ]
            for field_title, field_key in list_fields:
                st.markdown(f"**{field_title}**")
                field_value = selected_resume.get(field_key, [])
                if isinstance(field_value, list) and field_value:
                    st.markdown(", ".join(field_value))
                else:
                    st.markdown("None")

        # Download Resume Button
        resume_filename = selected_resume.get('filename')
        if resume_filename:
            resume_path = Path("resumes") / resume_filename
            if resume_path.exists():
                # Read the resume file
                with open(resume_path, "rb") as file:
                    resume_data = file.read()
                
                # Create download button
                file_extension = resume_path.suffix.lower()
                mime_type = {
                    '.pdf': 'application/pdf',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.doc': 'application/msword'
                }.get(file_extension, 'application/octet-stream')
                
                st.download_button(
                    label="📄 Download Resume",
                    data=resume_data,
                    file_name=resume_filename,
                    mime=mime_type,
                    key=f"download_{selected_resume.get('name', 'unknown')}"
                )
            else:
                st.warning(f"Resume file '{resume_filename}' not found in resumes folder.")
        else:
            st.info("No resume file available for this candidate.")
        
else:
    st.info("No candidates match the selected filters. Please adjust your search criteria.")

# Export functionality
st.sidebar.markdown("---")
st.sidebar.header("📥 Export")
if st.sidebar.button("Export All Filtered Results to CSV"):
    # Get all filtered results for export (without pagination)
    export_df, _ = query_resumes(
        geographic_market=selected_market,
        investment_approach=selected_approach,
        min_exp=exp_range[0],
        max_exp=exp_range[1],
        selected_skills=selected_skills if selected_skills else None,
        selected_sectors=selected_sectors if selected_sectors else None,
        selected_degrees=selected_degrees if selected_degrees else None,
        selected_roles=selected_roles if selected_roles else None,
        selected_certs=selected_certs if selected_certs else None,
        limit=1000000,  # Large limit to get all results
        offset=0
    )
    
    # Create export display DataFrame
    export_display_df = create_display_dataframe(export_df, include_full_data=False)
    csv_string = export_display_df.to_csv(index=False)
    st.sidebar.download_button(
        label=f"Download CSV ({len(export_display_df)} rows)",
        data=csv_string,
        file_name="filtered_candidates.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("**Candidate Search Platform** | Built with Streamlit | Powered by SQLite")
