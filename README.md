# 🔍 Candidate Search Platform

A Streamlit web application for searching and filtering candidates for junior analyst positions. This platform provides an interactive interface to browse, filter, and analyze candidate resumes with powerful filtering options and visualizations.

## ✨ Features

- **Database Selection**: Switch between different datasets (Original: 10 resumes, Large Dataset: scaled version)
- **Advanced Filtering**: Filter candidates by geographic market, investment approach, sectors, skills, degrees, certifications, current roles, and years of experience range
- **Interactive Visualizations**: View candidate distributions with 6 comprehensive charts:
  - Geographic market distribution (pie chart)
  - Investment approach distribution (bar chart)
  - Years of experience histogram
  - Top 10 sectors analysis
  - Top 10 skills analysis
  - Top 10 current roles/titles analysis
- **Pagination**: Navigate through large result sets with customizable page sizes (25, 50, 100 results per page) and intuitive navigation controls (First, Previous, Next, Last buttons and direct page input)
- **Detailed Candidate View**: View comprehensive candidate profiles including professional summary, location, contact information, work experience, education, skills, sectors, degrees, and certifications
- **Resume Download**: Download original resume files (PDF, DOCX) directly from candidate details
- **Export Functionality**: Export all filtered results to CSV format for external analysis
- **Real-time Statistics**: View total candidates, filtered results count, unique geographic markets, and average experience metrics

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- SQLite database files:
  - `parsed_resumes.db` - Original dataset (10 resumes)
  - `parsed_resumes_large.db` - Large dataset (scaled version)
- `resumes/` folder containing original resume files (PDF, DOCX) for download functionality

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd candidate-search-platform
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Running Locally

1. Ensure the following files are in the same directory as `streamlit_app.py`:
   - `parsed_resumes.db` - Original dataset (10 resumes)
   - `parsed_resumes_large.db` - Large dataset (scaled version)
   - `resumes/` folder containing original resume files

2. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

3. Open your browser and navigate to `http://localhost:8501`


### Database Setup Note

The application requires SQLite database files containing parsed resume data:

- `parsed_resumes.db` - Original dataset with 10 resumes
- `parsed_resumes_large.db` - Large dataset with scaled data

Both databases should have a `resumes` table with the following structure:
- Standard fields: `name`, `location`, `email`, `phone`, `geographic_market`, `investment_approach`, `years_experience`, `current_role`, `current_company`, `filename`, `professional_summary`
- JSON & List fields: `education`, `work_experience`, `skills`, `sectors`, `degrees`, `certifications`

Additionally, a `resumes/` folder should contain the original resume files (PDF, DOCX) that correspond to the `filename` field in the database for the download functionality.

If you need to generate these databases, run your resume parsing notebook first to create the database files and ensure the resume files are in the `resumes/` folder.

## 📦 Dependencies

- `streamlit==1.53.0` - Web framework for the interactive application
- `pandas==2.3.3` - Data manipulation and analysis
- `plotly==6.5.2` - Interactive visualizations and charts
