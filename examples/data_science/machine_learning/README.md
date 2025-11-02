# Machine Learning Model Development Example

## 🎯 Scenario

Create a complete machine learning workflow for customer churn prediction:
- Feature engineering and preprocessing
- Model training and evaluation
- Hyperparameter optimization
- Model explainability with SHAP
- Model persistence and serving
- Automated ML pipeline
- Experiment tracking

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/data_science/machine_learning

# Create the complete ML pipeline
clippy "Create a complete machine learning pipeline for customer churn prediction with feature engineering, model training, hyperparameter optimization, SHAP explainability, and model persistence using sklearn, xgboost, and mlflow"
```

## 📁 Expected Project Structure

```
machine_learning/
├── data/
│   ├── raw/
│   │   └── customer_data.csv     # Raw customer dataset
│   ├── processed/
│   │   ├── features.csv          # Engineered features
│   │   └── splits/               # Train/validation/test splits
│   └── models/
│       ├── model.pkl             # Trained model
│       ├── scaler.pkl            # Fitted scaler
│       └── feature_importance.json # Feature importance data
├── src/
│   ├── feature_engineering.py    # Feature creation and selection
│   ├── model_training.py         # Model training utilities
│   ├── evaluation.py             # Model evaluation metrics
│   ├── explainability.py         # SHAP and interpretability
│   ├── inference.py              # Model serving and prediction
│   └── pipeline.py               # ML pipeline orchestrator
├── notebooks/
│   ├── 01_exploration.ipynb      # Data exploration
│   ├── 02_feature_engineering.ipynb # Feature analysis
│   ├── 03_model_training.ipynb   # Model development
│   └── 04_explainability.ipynb   # Model interpretation
├── experiments/                  # MLflow experiment logs
├── tests/
│   ├── test_feature_engineering.py
│   ├── test_model_training.py
│   └── test_inference.py
├── config/
│   ├── model_config.yaml         # Model hyperparameters
│   └── pipeline_config.yaml      # Pipeline configuration
├── pyproject.toml                # Modern ML packaging with uv
├── setup.py                      # Package setup
└── run_experiment.py             # Experiment runner
```

## 🛠️ Step-by-Step Commands

### 1. Setup ML Environment and Data
```bash
clippy "Create ML project structure with pyproject.toml for uv dependency management including scikit-learn, xgboost, lightgbm, shap, mlflow, pandas, numpy, and jupyter. Also generate synthetic customer churn dataset with realistic features"
```

### 2. Feature Engineering Pipeline
```bash
clippy "Create feature_engineering.py with feature creation, encoding, scaling, selection, and automated feature importance analysis using sklearn pipelines"
```

### 3. Model Training Framework
```bash
clippy "Create model_training.py with support for multiple algorithms (Logistic Regression, Random Forest, XGBoost), cross-validation, and hyperparameter optimization using Optuna"
```

### 4. Model Evaluation and Metrics
```bash
clippy "Create evaluation.py with comprehensive metrics including AUC-ROC, precision-recall, confusion matrix, calibration plots, and business metrics like lift charts"
```

### 5. Model Explainability
```bash
clippy "Create explainability.py with SHAP values, feature importance plots, partial dependence plots, and individual prediction explanations"
```

### 6. Model Inference System
```bash
clippy "Create inference.py with batch prediction, real-time API endpoints, model versioning, and A/B testing support"
```

### 7. ML Pipeline Orchestration
```bash
clippy "Create pipeline.py with MLflow integration for experiment tracking, model registry, and automated pipeline execution"
```

### 8. Jupyter Notebooks for Exploration
```bash
clippy "Create comprehensive Jupyter notebooks for data exploration, feature analysis, model development, and interpretability with detailed explanations"
```

## 💡 Advanced Features

### Deep Learning Integration
```bash
clippy "Add PyTorch neural network models with hyperparameter tuning using Ray Tune for comparison with traditional ML algorithms"
```

### AutoML Integration
```bash
clippy "Integrate AutoML library (TPOT or AutoKeras) for automated model selection and hyperparameter optimization"
```

### Model Monitoring
```bash
clippy "Add model monitoring with data drift detection, performance tracking, and automated retraining triggers"
```

## 🔍 ML-Specific Validation

```bash
# ✅ ML pipelines validated for proper sklearn usage
clippy "Create sklearn Pipeline with custom transformers and model selection"

# ✅ Model files validated for proper serialization
clippy "Save trained models with pickle and joblib with versioning"

# ✅ MLflow config files validated
clippy "Create MLflow experiment configuration with proper tracking settings"
```

## 📝 Example ML Session

```
$ clippy
> Create a complete ML pipeline for customer churn prediction with XGBoost and SHAP

🤖 I'll create a comprehensive machine learning pipeline for churn prediction.

📋 Plan:
1. Generate realistic customer dataset
2. Build feature engineering pipeline
3. Train multiple models with hyperparameter optimization
4. Evaluate models with comprehensive metrics
5. Add SHAP explainability
6. Create inference system
7. Set up MLflow experiment tracking

🎯 Generating customer data...

✅ Successfully wrote to data/raw/customer_data.csv
10,000 customers with 30 features and target variable

🤖 Building feature engineering...

✅ Successfully wrote to src/feature_engineering.py
Created 15 engineered features, automatic encoding, and scaling

🤖 Training models with optimization...

✅ Successfully wrote to src/model_training.py
Models: XGBoost (AUC: 0.89), Random Forest (AUC: 0.86), Logistic Regression (AUC: 0.82)

🤖 Adding model explainability...

✅ Successfully wrote to src/explainability.py
SHAP values, feature importance charts, individual explanations

🎯 Best model: XGBoost with AUC 0.89, precision 0.87, recall 0.91
Top features: tenure, monthly_charges, contract_type, online_security
```

## 🧪 Running the ML Pipeline

```bash
# Install ML dependencies with uv
uv sync

# Or develop install
pip install -e .

# Run complete experiment
python run_experiment.py --config config/model_config.yaml

# Run specific pipeline stages
python src/pipeline.py --stage feature_engineering
python src/pipeline.py --stage model_training --optimize
python src/pipeline.py --stage explanation

# Start MLflow UI for experiment tracking
mlflow ui --port 5000

# Run inference on new data
python src/inference.py --model data/models/model.pkl --input new_customers.csv

# Run tests
pytest tests/ -v --tb=short
```

## 📊 Model Evaluation Results

### Performance Metrics
| Model | AUC-ROC | Precision | Recall | F1-Score | Accuracy |
|-------|---------|-----------|--------|----------|----------|
| XGBoost | 0.89 | 0.87 | 0.91 | 0.89 | 0.86 |
| Random Forest | 0.86 | 0.84 | 0.88 | 0.86 | 0.83 |
| Logistic Regression | 0.82 | 0.79 | 0.85 | 0.82 | 0.78 |

### Feature Importance (Top 10)
1. tenure (0.18)
2. monthly_charges (0.15)
3. contract_type_month-to-month (0.12)
4. online_security_no (0.09)
5. tech_support_no (0.08)
6. total_charges (0.07)
7. internet_service_fiber_optic (0.06)
8. payment_method_electronic_check (0.05)
9. senior_citizen (0.04)
10. streaming_movies_no (0.03)

## 🎯 Model Explainability Insights

### SHAP Summary Plot
- Longer tenure customers have lower churn probability
- Higher monthly charges increase churn risk
- Month-to-month contracts have highest churn rate
- Lack of online security and tech support increases churn

### Individual Predictions
```
Customer 12345 (Churn Probability: 0.78)
- Key Factors:
  * Month-to-month contract (+0.25)
  * No online security (+0.18)
  * High monthly charges (+0.15)
  * Short tenure (+0.12)
```

## 🚀 Deployment Options

### FastAPI Inference Service
```bash
clippy "Create FastAPI service for real-time churn prediction with model loading, input validation, and health endpoints"
```

### Batch Processing
```bash
clippy "Create batch scoring script for processing large datasets with parallel processing and progress tracking"
```

### Docker Containerization
```bash
clippy "Create Dockerfile and docker-compose.yml for containerized model serving with volume mounting and environment configuration"
```

## 📈 Monitoring and Maintenance

### Model Performance Monitoring
```bash
clippy "Add performance monitoring with data drift detection, prediction distribution tracking, and automated alerting"
```

### Automated Retraining
```bash
clippy "Implement scheduled retraining pipeline with new data ingestion, feature engineering, and model comparison"
```

## 🔧 Configuration Files

### Model Configuration (config/model_config.yaml)
```yaml
models:
  xgboost:
    max_depth: [3, 5, 7]
    learning_rate: [0.01, 0.1, 0.2]
    n_estimators: [100, 200, 300]
    subsample: [0.8, 0.9, 1.0]
    colsample_bytree: [0.8, 0.9, 1.0]

  random_forest:
    n_estimators: [100, 200, 300]
    max_depth: [10, 15, 20]
    min_samples_split: [2, 5, 10]

feature_engineering:
  categorical_encoding: "target"
  numerical_scaling: "robust"
  feature_selection: "rfe"
  n_features_to_select: 20

evaluation:
  cv_folds: 5
  test_size: 0.2
  random_state: 42
  scoring_metric: "roc_auc"
```

## 🧮 Advanced ML Techniques Demonstrated

### Feature Engineering
- Automatic categorical encoding
- Missing value imputation strategies
- Feature scaling and normalization
- Feature selection methods
- Polynomial feature creation
- Interaction terms

### Model Optimization
- Hyperparameter search with Optuna
- Cross-validation strategies
- Ensemble methods (stacking, blending)
- Calibration techniques
- Class imbalance handling

### Explainability
- Global feature importance
- Local prediction explanations
- Partial dependence plots
- SHAP force plots
- Decision boundaries visualization

### ML Operations
- Model versioning with MLflow
- Experiment tracking
- Automated pipelines
- Model monitoring
- A/B testing framework

## 🔧 Common ML Issues and Solutions

### Data Quality Issues
```bash
# Handle missing values in training data
clippy "Fix missing value handling in feature pipeline with multiple imputation strategies"

# Address data leakage
clippy "Identify and fix data leakage issues in feature engineering pipeline"
```

### Model Performance Issues
```bash
# Improve model accuracy
clippy "Evaluate and improve model performance through feature engineering and hyperparameter tuning"

# Handle class imbalance
clippy "Implement techniques for handling imbalanced datasets with SMOTE and class weighting"
```

### Deployment Issues
```bash
# Optimize model inference speed
clippy "Optimize model inference with batch processing and model quantization"

# Handle production data drift
clippy "Implement data drift detection and model monitoring system"
```

## 📚 Best Practices Demonstrated

- **Reproducible ML**: Fixed seeds, configurations, and experiment tracking
- **Modular Design**: Separate components for each ML workflow stage
- **Comprehensive Testing**: Unit tests for all ML components
- **Model Explainability**: SHAP and interpretability techniques
- **Version Control**: Model and data versioning with MLflow
- **Production Ready**: API endpoints, monitoring, and deployment scripts

## 🎯 Business Value and Insights

### Customer Churn Insights
- Customers with <6 months tenure have 3x higher churn risk
- Month-to-month contracts show 40% higher churn rate
- Customers with multiple services have 25% lower churn
- Recent price increases correlate with increased churn

### Model Impact
- 89% accuracy in predicting at-risk customers
- $2.5M projected annual savings through proactive retention
- 85% reduction in false positives vs rule-based system
- Real-time scoring enables immediate intervention