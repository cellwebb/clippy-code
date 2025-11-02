# Data Analysis Pipeline Example

## 🎯 Scenario

Create a complete data analysis pipeline for sales data that includes:
- Data cleaning and preprocessing
- Exploratory data analysis (EDA)
- Statistical analysis
- Data visualization with multiple chart types
- Automated report generation
- Jupyter notebook integration
- Reproducible results with seeds

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/data_science/analysis_pipeline

# Create the complete analysis pipeline
clippy "Create a complete data analysis pipeline for sales data with cleaning, EDA, visualization, and automated reporting. Use pandas, numpy, matplotlib, seaborn, and include both Python scripts and a Jupyter notebook."
```

## 📁 Expected Project Structure

```
analysis_pipeline/
├── data/
│   ├── raw/
│   │   └── sales_data.csv          # Raw sales data
│   ├── processed/
│   │   ├── clean_sales.csv         # Cleaned data
│   │   └── analysis_results.csv    # Analysis results
│   └── reports/
│       └── sales_report.html       # Generated report
├── notebooks/
│   ├── exploratory_analysis.ipynb  # Jupyter notebook
│   └── interactive_dashboard.ipynb # Interactive dashboard
├── src/
│   ├── data_cleaning.py          # Data preprocessing utilities
│   ├── analysis.py               # Statistical analysis functions
│   ├── visualization.py          # Plotting and chart creation
│   ├── report_generator.py       # Automated report generation
│   └── pipeline.py               # Main pipeline orchestrator
├── tests/
│   ├── test_data_cleaning.py
│   ├── test_analysis.py
│   └── test_visualization.py
├── pyproject.toml                # Modern Python packaging with uv
├── config.yaml                   # Analysis configuration
├── README.md                     # This file
└── run_pipeline.py               # Pipeline entry point
```

## 🛠️ Step-by-Step Commands

### 1. Create Project Structure and Dependencies
```bash
clippy "Create the complete project structure for data analysis pipeline including data/, notebooks/, src/, tests/ directories and pyproject.toml with modern uv dependencies for pandas, numpy, matplotlib, seaborn, jupyter, scipy, and plotly"
```

### 2. Generate Sample Sales Data
```bash
clippy "Create a sample sales_data.csv with 1000 rows of realistic sales data including date, product, category, quantity, price, customer_id, region, and sales_rep columns with some missing values and outliers"
```

### 3. Build Data Cleaning Module
```bash
clippy "Create data_cleaning.py with functions to handle missing values, remove outliers, standardize dates, and validate data integrity with comprehensive logging"
```

### 4. Implement Exploratory Data Analysis
```bash
clippy "Create analysis.py with functions for descriptive statistics, correlation analysis, trend analysis, and seasonal pattern detection using pandas and scipy"
```

### 5. Create Visualizations Module
```bash
clippy "Create visualization.py with matplotlib and seaborn functions for sales trends, geographic distribution, product performance charts, and interactive plots with plotly"
```

### 6. Build Report Generator
```bash
clippy "Create report_generator.py that generates HTML reports with embedded charts, statistical summaries, and insights using jinja2 templates and plotly for interactive elements"
```

### 7. Create Jupyter Notebook for Exploratory Analysis
```bash
clippy "Create exploratory_analysis.ipynb with markdown cells explaining the analysis process, interactive visualizations, and statistical explanations for data exploration"
```

### 8. Implement Pipeline Orchestrator
```bash
clippy "Create pipeline.py that orchestrates the entire analysis workflow with proper error handling, logging, and progress tracking using argparse for configuration"
```

## 💡 Advanced Features

### Add Machine Learning Model
```bash
clippy "Add sales forecasting model using sklearn with time series analysis, feature engineering, and model evaluation with MAE, MSE, and R² metrics"
```

### Add Interactive Dashboard
```bash
clippy "Create interactive_dashboard.ipynb with plotly dash components for filtering, real-time analysis, and interactive visual exploration"
```

### Add Data Validation
```bash
clippy "Add comprehensive data validation in src/data_validation.py with pytest fixtures and automated quality checks"
```

## 🔍 Validation Examples

clippy-code will ensure all your analysis files are properly structured:

```bash
# ✅ Statistical analysis validated
clippy "Create correlation analysis with proper p-value calculations"

# ✅ CSV files validated for structure
clippy "Generate sample sales data with proper headers"

# ✅ Jupyter notebooks validated for syntax
clippy "Create notebook with pandas analysis and markdown explanations"

# ✅ YAML config files validated
clippy "Create configuration file with analysis parameters"
```

## 📝 Example Session

```
$ clippy
> Create a data analysis pipeline for sales data with cleaning and visualization

🤖 I'll create a complete data analysis pipeline for your sales data.

📋 Plan:
1. Set up project structure and dependencies
2. Generate realistic sample sales data
3. Build data cleaning and preprocessing utilities
4. Implement statistical analysis functions
5. Create visualization modules
6. Generate automated reports
7. Create Jupyter notebook for exploration

🎯 Starting with project structure...

✅ Successfully wrote to requirements.txt
✅ Created directory structure: data/, notebooks/, src/, tests/

🤖 Now generating sample sales data...

✅ Successfully wrote to data/raw/sales_data.csv
Generated 1,000 sales records with realistic distribution

🤖 Building data cleaning utilities...

✅ Successfully wrote to src/data_cleaning.py
Functions: clean_data(), remove_outliers(), validate_data()

🤖 Implementing statistical analysis...

✅ Successfully wrote to src/analysis.py
Added correlation analysis, trend detection, seasonal patterns

🤖 Creating visualization modules...

✅ Successfully wrote to src/visualization.py
Generated 8 chart types with matplotlib, seaborn, and plotly

🤖 Building report generator...

✅ Successfully wrote to src/report_generator.py
HTML reports with interactive charts and insights

🎉 Data analysis pipeline created successfully!
Run: `python run_pipeline.py` to execute the complete analysis
Open: `notebooks/exploratory_analysis.ipynb` for interactive exploration
```

## 🧪 Running the Pipeline

```bash
# Install dependencies with uv
uv sync

# Or with traditional pip if needed
pip install -e .

# Run the complete pipeline
python run_pipeline.py

# Or run specific components
python src/data_cleaning.py
python src/analysis.py
python src/pipeline.py --stage cleaning --config config.yaml

# Start Jupyter for interactive analysis
jupyter notebook notebooks/

# Run tests
pytest tests/ -v
```

## 📊 Expected Outputs

### Data Cleaning Results
- Missing value handling summary
- Outlier detection report
- Data quality metrics

### Statistical Analysis
- Descriptive statistics table
- Correlation matrix heatmaps
- Trend analysis results
- Seasonal pattern identification

### Visualizations
- Sales time series plots
- Regional performance maps
- Product category breakdowns
- Customer behavior charts
- Interactive dashboard

### Automated Report
- Executive summary with key insights
- Statistical findings with interpretations
- Interactive charts and tables
- Methodology explanations

## 🎯 Customization Ideas

- Add real-time data integration with APIs
- Implement advanced forecasting with ARIMA/LSTM
- Add anomaly detection algorithms
- Create automated alerting system
- Add database integration for larger datasets
- Implement parallel processing for big data

## 🔧 Analysis Configuration

Create `config.yaml` for pipeline customization:

```yaml
data:
  input_file: "data/raw/sales_data.csv"
  output_dir: "data/processed/"
  
cleaning:
  handle_missing: "forward_fill"
  outlier_method: "iqr"
  outlier_threshold: 1.5

analysis:
  correlation_threshold: 0.7
  trend_period: "monthly"
  confidence_level: 0.95

visualization:
  chart_style: "seaborn"
  color_palette: "viridis"
  interactive: true

reporting:
  template: "templates/sales_report.html"
  include_raw_data: false
  charts_per_page: 6
```

## 🧮 Key Analysis Techniques Demonstrated

### Data Cleaning
- Missing value imputation strategies
- Outlier detection using IQR and Z-score methods
- Data type validation and conversion
- Duplicate detection and removal

### Statistical Analysis
- Descriptive statistics and distributions
- Correlation analysis with significance testing
- Time series decomposition
- Seasonality detection using FFT

### Visualization Techniques
- Time series plotting with trend lines
- Geographic data visualization
- Statistical distributions and box plots
- Interactive dashboards with filtering

### Machine Learning Integration
- Feature engineering for time series
- Model evaluation and validation
- Hyperparameter tuning
- Performance metrics calculation

## 🔍 Advanced Analysis Options

### Clustering Analysis
```bash
clippy "Add customer segmentation using K-means clustering with optimal cluster selection using elbow method"
```

### A/B Testing Framework
```bash
clippy "Create A/B testing framework with statistical significance testing and confidence intervals"
```

### Time Series Forecasting
```bash
clippy "Implement ARIMA and Prophet models for sales forecasting with cross-validation"
```

## 💡 Best Practices Demonstrated

- **Reproducibility**: Fixed random seeds and configuration files
- **Modularity**: Separate modules for each analysis component
- **Testing**: Comprehensive tests for data processing and analysis
- **Documentation**: Code documentation and Jupyter notebooks
- **Error Handling**: Graceful failure handling with logging
- **Performance**: Efficient pandas operations and memory management

## 🔧 Troubleshooting

### Common Issues:
```bash
# Memory issues with large datasets
clippy "Optimize data processing for large CSV files using chunking"

# Plotting issues in different environments
clippy "Fix matplotlib backend issues for headless environments"

# Statistical analysis errors
clippy "Debug correlation analysis with non-numeric data types"
```