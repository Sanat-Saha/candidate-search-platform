# 🔍 Candidate Search Platform

A Streamlit web application for searching and filtering candidates for junior analyst positions. This platform provides an interactive interface to browse, filter, and analyze candidate resumes with powerful filtering options and visualizations.

## ✨ Features

- **Advanced Filtering**: Filter candidates by geographic market, investment approach, sectors, years of experience, skills, and certifications
- **Interactive Visualizations**: View candidate distributions with charts including:
  - Geographic market distribution (pie chart)
  - Investment approach distribution (bar chart)
  - Years of experience histogram
  - Top sectors analysis
- **Candidate Search**: Search for specific skills across all resumes
- **Detailed Candidate View**: View comprehensive candidate profiles including education, work experience, skills, and certifications
- **Export Functionality**: Export filtered results to CSV format
- **Real-time Statistics**: View total candidates, filtered results, and key metrics

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- SQLite database file (`parsed_resumes.db`) with parsed resume data

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

1. Ensure the `parsed_resumes.db` file is in the same directory as `streamlit_app.py`

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

5. **Important**: You'll need to include the `parsed_resumes.db` file in your repository for the app to work. Make sure it's committed to GitHub:
```bash
git add parsed_resumes.db
git commit -m "Add database file"
git push
```

6. Click "Deploy!"

### Database Setup Note

The application requires a SQLite database file (`parsed_resumes.db`) containing parsed resume data. The database should have a `resumes` table with the following structure:
- Standard fields: `name`, `location`, `email`, `phone`, `geographic_market`, `investment_approach`, `years_experience`, `current_role`, `current_company`, `filename`
- JSON fields: `education`, `work_experience`, `skills`, `sectors`, `certifications`, `languages`

If you need to generate this database, run your resume parsing notebook first to create the `parsed_resumes.db` file.

## 📦 Dependencies

- `streamlit==1.53.0` - Web framework
- `pandas==2.3.3` - Data manipulation
- `plotly==6.5.2` - Interactive visualizations

All dependencies are listed in `requirements.txt`.

---

**Built with ❤️ using Streamlit**
