# Databricks ETL Pipeline

[![CI Pipeline](https://github.com/msosasoto/databricks-etl-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/msosasoto/databricks-etl-pipeline/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Production-ready ETL pipeline for processing sales data using PySpark and Delta Lake on Databricks, with comprehensive testing, data quality validation, and automated deployment.

##  Features

-  **Modular Architecture**: Clean separation of concerns with dedicated modules
-  **Error Handling**: Custom exceptions and comprehensive error management
-  **Structured Logging**: JSON-formatted logs with contextual information
-  **Data Quality**: Automated validation checks for nulls, negatives, duplicates
-  **Incremental Loads**: Delta merge (upsert) support for efficient updates
-  **Secure Configuration**: Environment-based config with no hardcoded secrets
-  **Well Tested**: 33 unit/integration tests with 61% coverage
-  **CI/CD Ready**: GitHub Actions pipeline for automated testing

##  Pipeline Overview

```
Source Data (Delta) → Extract → Validate → Transform → Load → Target (Delta)
                        ↓         ↓          ↓          ↓
                    DataLoader Quality  Transforms  Upsert/Merge
```

### Transformations Applied
-  Calculate total amount (`quantity × price`)
-  Extract temporal components (year, month, day of week)
-  Classify orders by size (Small/Medium/Large)
-  Categorize by price (Budget/Standard/Premium)
-  Add processing timestamps

### Data Quality Checks
-  Null value validation (configurable threshold)
-  Negative value detection (prices, quantities)
-  Duplicate order ID detection
-  Date range validation

##  Project Structure

```
databricks-etl-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── config/
│   └── config.yaml             # Business rules and configuration
├── data/
│   ├── raw/                    # Source data (CSV)
│   └── processed/              # Local processed data
├── docs/
│   ├── architecture.md         # Architecture documentation
│   └── deployment.md           # Deployment guide
├── resources/
│   └── notebooks/
│       └── etl_pipeline.ipynb  # Orchestration notebook
├── src/
│   ├── config/
│   │   └── settings.py         # Configuration management
│   ├── extract/
│   │   └── data_loader.py      # Data extraction
│   ├── transform/
│   │   └── transformations.py  # Business logic
│   ├── validation/
│   │   └── data_quality.py     # Quality checks
│   ├── load/
│   │   └── data_writer.py      # Delta merge/upsert
│   └── utils/
│       ├── logger.py            # Structured logging
│       └── spark_utils.py       # Spark utilities
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_transformations.py # Transformation tests
│   ├── test_data_quality.py    # Quality tests
│   └── test_integration.py     # Integration tests
├── .env.example                # Environment variables template
├── .gitignore
├── databricks.yml              # Databricks Asset Bundle config
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Databricks workspace
- Databricks CLI installed

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/msosasoto/databricks-etl-pipeline.git
   cd databricks-etl-pipeline
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Databricks settings
   ```

4. **Authenticate with Databricks**
   ```bash
   databricks auth login --host <YOUR_WORKSPACE_URL>
   ```

5. **Deploy to Databricks**
   ```bash
   databricks bundle validate
   databricks bundle deploy --target dev
   ```

6. **Run the pipeline**
   - Go to Databricks workspace → **Workflows**
   - Find `[dev] ETL Pipeline`
   - Click **Run Now**

##  Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_transformations.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Local Development

```python
# Example: Using the pipeline components
from src.config.settings import Config
from src.extract.data_loader import DataLoader
from src.transform.transformations import SalesTransformer
from src.validation.data_quality import DataQualityValidator

# Initialize
config = Config()
loader = DataLoader(spark, config)

# Extract
df_raw = loader.load_source_data()

# Validate
validator = DataQualityValidator(config)
report = validator.validate(df_raw)

# Transform
transformer = SalesTransformer(config)
df_transformed = transformer.transform(df_raw)
```

## ⚙️ Configuration

### Business Rules (`config/config.yaml`)

```yaml
business_rules:
  order_size:
    large_threshold: 10      # Orders with quantity >= 10
    medium_threshold: 5      # Orders with quantity >= 5
  price_category:
    premium_threshold: 500   # Prices >= 500
    standard_threshold: 100  # Prices >= 100
    
data_quality:
  max_null_percentage: 5     # Max % nulls allowed
  check_duplicates: true
  validate_negative_values: true
```

### Environment Variables (`.env`)

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
CATALOG_NAME=datasets_github_projects
SCHEMA_NAME=default
LOG_LEVEL=INFO
```

##  Documentation

- **[Architecture](docs/architecture.md)**: System design and technical details
- **[Deployment](docs/deployment.md)**: Complete deployment guide

##  Key Components

### Data Loader
```python
from src.extract.data_loader import DataLoader

loader = DataLoader(spark, config)
df = loader.load_source_data()
```

### Transformations
```python
from src.transform.transformations import SalesTransformer

transformer = SalesTransformer(config)
df_transformed = transformer.transform(df_raw)
```

### Data Quality
```python
from src.validation.data_quality import DataQualityValidator

validator = DataQualityValidator(config)
report = validator.validate(df)
print(validator.generate_quality_report(report))
```

### Delta Writer (Upsert)
```python
from src.load.data_writer import DeltaWriter

writer = DeltaWriter(spark, config)
stats = writer.upsert(df_transformed, merge_key="order_id")
```

##  Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Programming language |
| **PySpark** | 3.5.0 | Data processing engine |
| **Delta Lake** | 3.0.0 | Storage layer |
| **Databricks** | - | Cloud platform |
| **PyTest** | 7.4.3 | Testing framework |
| **Black** | 23.12.1 | Code formatting |
| **Flake8** | 7.0.0 | Linting |

##  Test Coverage

| Module | Coverage |
|--------|----------|
| `transformations.py` | 100% |
| `data_quality.py` | 92% |
| `settings.py` | 86% |
| **Overall** | **61%** |

##  Example Results

### Input Data (10 records)
```
order_id | customer_id | product_name | quantity | price  | country
---------|-------------|--------------|----------|--------|----------
1001     | C001        | Laptop       | 1        | 1200.5 | Colombia
1002     | C002        | Mouse        | 2        | 25.99  | Mexico
...
```

### Output Data (10 records + 7 new columns)
```
order_id | total_amount | order_size | price_category | year | month | ...
---------|--------------|------------|----------------|------|-------|----
1001     | 1200.50      | Small      | Premium        | 2024 | 1     | ...
1002     | 51.98        | Small      | Budget         | 2024 | 1     | ...
...
```

### Business Metrics
- **Total Revenue**: $3,654.88
- **Average Ticket**: $365.49
- **Top Category**: Electronics (60%)

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

##  License

This project is part of a data engineering portfolio.

##  Author

**Mariano Sosa**  
Data Engineer  
Stack: Python | PySpark | Databricks | Delta Lake

---

 *This is Project #1 of a series of incremental data engineering projects focusing on production-ready practices.*
