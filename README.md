# 🔍 Candidate Search Platform

A Streamlit web application for searching and filtering candidates for junior analyst positions. This platform provides an interactive interface to browse, filter, and analyze candidate resumes with powerful filtering options and visualizations.

## ✨ Features

- **Database Selection**: Switch between different datasets (Original: 10 resumes, Large Dataset: scaled version)
- **Advanced Filtering**: Filter candidates by geographic market, investment approach, sectors, years of experience, skills, and certifications
- **Interactive Visualizations**: View candidate distributions with charts including:
  - Geographic market distribution (pie chart)
  - Investment approach distribution (bar chart)
  - Years of experience histogram
  - Top sectors analysis
- **Pagination**: Navigate through large result sets with customizable page sizes (25, 50, 100 results per page)
- **Detailed Candidate View**: View comprehensive candidate profiles including education, work experience, skills, sectors, and certifications
- **Resume Download**: Download original resume files (PDF, DOCX, DOC) directly from candidate details
- **Export Functionality**: Export filtered results to CSV format
- **Real-time Statistics**: View total candidates, filtered results, and key metrics

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- SQLite database files:
  - `parsed_resumes.db` - Original dataset (10 resumes)
  - `parsed_resumes_large.db` - Large dataset (scaled version)
- `resumes/` folder containing original resume files (PDF, DOCX, DOC) for download functionality

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

## ☁️ Deploying to Streamlit Cloud

### Step 1: Push to GitHub

1. Make sure your code is committed and pushed to a GitHub repository:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account

2. Click "New app"

3. Select your repository and branch

4. Set the main file path to `streamlit_app.py`

5. **Important**: You'll need to include the database files and resumes folder in your repository for the app to work. Make sure they're committed to GitHub:
```bash
git add parsed_resumes.db parsed_resumes_large.db resumes/
git commit -m "Add database files and resumes folder"
git push
```

6. Click "Deploy!"

### Database Setup Note

The application requires SQLite database files containing parsed resume data:

- `parsed_resumes.db` - Original dataset with 10 resumes
- `parsed_resumes_large.db` - Large dataset with scaled data

Both databases should have a `resumes` table with the following structure:
- Standard fields: `name`, `location`, `email`, `phone`, `geographic_market`, `investment_approach`, `years_experience`, `current_role`, `current_company`, `filename`
- JSON fields: `education`, `work_experience`, `skills`, `sectors`, `certifications`, `languages`

Additionally, a `resumes/` folder should contain the original resume files (PDF, DOCX, DOC) that correspond to the `filename` field in the database for the download functionality.

If you need to generate these databases, run your resume parsing notebook first to create the database files and ensure the resume files are in the `resumes/` folder.

## 📦 Dependencies

- `streamlit==1.53.0` - Web framework for the interactive application
- `pandas==2.3.3` - Data manipulation and analysis
- `plotly==6.5.2` - Interactive visualizations and charts

All dependencies are listed in `requirements.txt`. The application also uses Python's built-in `sqlite3`, `json`, and `pathlib` modules.

---

**Built with ❤️ using Streamlit**
