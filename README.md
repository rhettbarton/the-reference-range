# Lab Results Visualizer 🔬

A lightweight Python application built with Streamlit that helps patients visualize and understand their lab results over time. The app processes CSV files of lab data and creates interactive charts showing trends, reference ranges, and health insights.

## Features

- 📊 **Interactive Visualizations**: Time-series charts with reference range highlighting
- 🎯 **Trend Analysis**: Automatic detection of improving/worsening trends
- 🏷️ **Test Categorization**: Groups tests by category (Lipid Panel, Kidney Function, etc.)
- ⚠️ **Out-of-Range Flagging**: Visual indicators for abnormal results
- 📥 **Data Export**: Download enhanced CSV with standardized names and flags
- 🔄 **Test Name Standardization**: Maps variations of test names to standard terms

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository to your local machine

2. Navigate to the project directory:
```bash
cd lab-viz-app
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

Run the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your default web browser (usually at `http://localhost:8501`)

### Uploading Your Data

#### Required: Lab Results CSV

Your lab results CSV **must** contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| Date | Test date (YYYY-MM-DD preferred) | 2024-06-20 |
| Test | Name of the lab test | Cholesterol Total |
| Result | Numeric result value | 195 |
| Units | Measurement units | mg/dL |
| Reference Interval | Normal range as text | <200 or 50-100 |
| Interval Min | Minimum normal value | 0 |
| Interval Max | Maximum normal value | 200 |
| Provider | Lab or healthcare provider | Quest Diagnostics |
| Note | Additional notes (optional) | Fasting 12 hours |

**Sample data format:**
```csv
Date,Test,Result,Units,Reference Interval,Interval Min,Interval Max,Provider,Note
2024-01-15,Cholesterol Total,195,mg/dL,<200,0,200,Quest Diagnostics,
2024-01-15,HDL Cholesterol,52,mg/dL,>40,40,999,Quest Diagnostics,
2024-06-20,Glucose,98,mg/dL,70-100,70,100,LabCorp,Fasting
```

#### Optional: Test Crosswalk CSV

Upload a crosswalk file to standardize test names and assign categories. If not provided, the app will use basic auto-categorization.

**Crosswalk format:**
```csv
Original Test Name,Standardized Test Name,Test Category
Cholesterol Total,Total Cholesterol,Lipid Panel
CHOL,Total Cholesterol,Lipid Panel
HDL-C,HDL Cholesterol,Lipid Panel
Glucose; Fasting,Fasting Glucose,Metabolic
```

A sample crosswalk file (`sample_crosswalk.csv`) is included with common test name variations.

### Navigating the App

The app has four main tabs:

1. **📊 Overview**: 
   - Summary metrics (total tests, unique tests, out-of-range count)
   - Latest results for each test with trend indicators
   - Filter by test category

2. **📈 Trends**:
   - Interactive time-series charts for individual tests
   - Reference range visualization (shaded green area)
   - Out-of-range markers
   - Historical data table
   - Category comparison chart

3. **🔍 Detailed Data**:
   - Complete data table with filtering options
   - Filter by category and range status
   - Sort and search functionality

4. **📥 Export**:
   - Download enhanced CSV with standardized test names
   - Includes calculated fields (Out of Range flags, Trends)

## Test Categories

The app automatically categorizes tests into these groups:

- **Lipid Panel**: Cholesterol, HDL, LDL, Triglycerides
- **Metabolic**: Glucose, HbA1c, Blood Sugar
- **Kidney Function**: Creatinine, BUN, eGFR
- **Liver Function**: ALT, AST, Alkaline Phosphatase, Bilirubin
- **Thyroid**: TSH, T3, T4
- **Complete Blood Count**: WBC, RBC, Hemoglobin, Platelets
- **Electrolytes**: Sodium, Potassium, Chloride, Calcium
- **Vitamins**: Vitamin D, B12, Folate
- **Other**: Uncategorized tests

## Example Workflow

1. **Collect Your Data**:
   - Download lab results from your healthcare provider's portal
   - Ensure the CSV has all required columns
   - Or use the included `sample_lab_results.csv` to try the app

2. **Launch the App**:
   ```bash
   streamlit run app.py
   ```

3. **Upload Files**:
   - Upload your lab results CSV
   - Optionally upload a crosswalk file (or use the provided `sample_crosswalk.csv`)

4. **Explore Your Results**:
   - Check the Overview tab for your latest results
   - View trends for specific tests (e.g., Cholesterol, Glucose)
   - Identify out-of-range values marked in red
   - See if results are improving (↑), declining (↓), or stable (→)

5. **Export Enhanced Data**:
   - Download the processed CSV with standardized names
   - Share with your healthcare provider or keep for your records

## Understanding the Visualizations

### Trend Charts

- **Blue line**: Your test results over time
- **Green shaded area**: Normal reference range
- **Blue markers**: Results within normal range
- **Red markers**: Out-of-range results
- **⚠️ symbol**: Warning indicator for abnormal values

### Trend Indicators

- **↑ Increasing**: Latest result is >5% higher than previous
- **↓ Decreasing**: Latest result is >5% lower than previous
- **→ Stable**: Change is within ±5%

## Customization

### Adding Custom Test Mappings

Edit or create your own crosswalk CSV with additional test name variations:

```csv
Original Test Name,Standardized Test Name,Test Category
My Lab's Glucose Test,Fasting Glucose,Metabolic
Proprietary Test Name,Standard Name,Appropriate Category
```

### Modifying Auto-Categorization

Edit the `_auto_categorize()` method in `data_processor.py` to add custom categorization rules.

## File Structure

```
lab-viz-app/
├── app.py                      # Main Streamlit application
├── data_processor.py           # Data loading and enrichment logic
├── visualizations.py           # Chart generation functions
├── requirements.txt            # Python dependencies
├── sample_crosswalk.csv        # Sample test name mappings
├── sample_lab_results.csv      # Sample lab data for testing
└── README.md                   # This file
```

## Troubleshooting

### Common Issues

**"CSV missing required columns"**
- Ensure your CSV has all 9 required columns with exact names (case-sensitive)
- Check for extra spaces in column headers

**"No data found in uploaded file"**
- Verify the CSV has data rows (not just headers)
- Check that dates are in a recognizable format (YYYY-MM-DD preferred)

**"Module not found" errors**
- Run `pip install -r requirements.txt` to install dependencies
- Ensure you're using Python 3.9 or higher

**Charts not displaying**
- Check that Result, Interval Min, and Interval Max columns contain numeric values
- Some text results may not display in trend charts (this is expected)

### Data Privacy

This app runs **entirely locally** on your machine. No data is sent to external servers or stored in the cloud. Your health information remains private and under your control.

## Technical Details

- **Framework**: Streamlit (web UI)
- **Data Processing**: Pandas
- **Visualizations**: Plotly (interactive charts)
- **Language**: Python 3.9+

## Contributing

This is a lightweight tool designed for personal use. Feel free to modify and extend it for your needs:

- Add new visualization types in `visualizations.py`
- Extend categorization logic in `data_processor.py`
- Customize the UI in `app.py`

## License

This project is provided as-is for personal use. Modify and distribute freely.

## Disclaimer

This application is designed to help visualize lab results for personal understanding. It is **not** a medical diagnostic tool and should not replace professional medical advice. Always consult with qualified healthcare providers for medical decisions.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the sample files to ensure your data format matches
3. Verify all dependencies are installed correctly

---

**Created with ❤️ for patients who want to better understand their health data**
