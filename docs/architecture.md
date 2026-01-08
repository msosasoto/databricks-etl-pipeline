# ETL Pipeline Architecture

## Overview

This project implements a modular, production-ready ETL pipeline for processing sales data using PySpark and Delta Lake on Databricks. The architecture follows software engineering best practices with clear separation of concerns, comprehensive testing, and robust error handling.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Databricks Workspace                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           ETL Pipeline Orchestration (Notebook)        │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Extract   │→ │  Validate    │→ │   Transform      │   │
│  │ DataLoader  │  │ DataQuality  │  │ SalesTransformer │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                              │                │
│                                              ▼                │
│                                     ┌──────────────┐          │
│                                     │     Load     │          │
│                                     │ DeltaWriter  │          │
│                                     └──────────────┘          │
│                                              │                │
└──────────────────────────────────────────────│────────────────┘
                                               ▼
                                    ┌──────────────────┐
                                    │  Delta Lake      │
                                    │  (Target Table)  │
                                    └──────────────────┘
```

## Module Structure

### `src/config/` - Configuration Management

**`settings.py`**: Centralized configuration handler
- Loads YAML configuration files
- Handles environment variable substitution
- Provides convenient property accessors
- Supports default values and validation

**Key Features:**
- Environment-based configuration (dev/prod)
- Business rules centralization
- Data quality thresholds

### `src/extract/` - Data Extraction

**`data_loader.py`**: Data loading from sources
- Reads from Delta tables
- Schema validation
- Error handling for missing tables
- Supports custom table loading

**Responsibilities:**
- Load raw data from source tables
- Validate table existence
- Check schema requirements

### `src/transform/` - Data Transformation

**`transformations.py`**: Business logic transformations
- Calculate derived fields (`total_amount`)
- Extract temporal components (year, month, day)
- Classify orders by size (Large/Medium/Small)
- Categorize by price (Premium/Standard/Budget)
- Add processing timestamps

**Transformation Rules:**
- **Order Size**: Based on quantity thresholds (configurable)
- **Price Category**: Based on price thresholds (configurable)
- **Total Amount**: `quantity × price`

### `src/validation/` - Data Quality

**`data_quality.py`**: Comprehensive data quality checks
- Null value validation
- Negative value detection
- Duplicate record identification
- Date range validation
- Configurable quality thresholds
- Detailed quality reports

**Quality Checks:**
1. **Null Check**: Validates null percentage within threshold
2. **Negative Values**: Detects invalid negative prices/quantities
3. **Duplicates**: Identifies duplicate order IDs
4. **Date Range**: Validates date ranges and detects future dates

### `src/load/` - Data Loading

**`data_writer.py`**: Delta Lake write operations
- Upsert (merge) support for incremental loads
- Overwrite mode for full refreshes
- Append mode for incremental data
- Delta table management

**Write Modes:**
- **Upsert**: Merge based on primary key (order_id)
- **Overwrite**: Full table replacement
- **Append**: Add new records only

### `src/utils/` - Utilities

**`logger.py`**: Structured logging
- JSON format support for production
- Configurable log levels
- Context-aware logging
- File and console handlers

**`spark_utils.py`**: Spark session management
- Session creation with Delta support
- Table optimization (OPTIMIZE, VACUUM)
- Table statistics and metadata
- Helper functions for common operations

## Data Flow

1. **Extract Phase**
   - DataLoader reads from source Delta table
   - Schema validation ensures required columns exist
   - Raw data passed to validation

2. **Validation Phase**
   - DataQualityValidator runs comprehensive checks
   - Quality report generated
   - Critical failures halt pipeline
   - Non-critical issues logged as warnings

3. **Transform Phase**
   - SalesTransformer applies business logic
   - Derived columns calculated
   - Classification rules applied
   - Timestamps added

4. **Load Phase**
   - DeltaWriter performs upsert operation
   - Existing records updated by order_id
   - New records inserted
   - Delta versioning maintained

## Error Handling Strategy

### Custom Exceptions
- `DataLoadError`: Issues loading source data
- `TransformationError`: Transformation failures
- `DataQualityError`: Critical quality issues
- `DataWriteError`: Write operation failures

### Error Flow
```python
try:
    # Operation
except SpecificError:
    logger.error("Detailed error message")
    raise CustomException("User-friendly message") from e
```

### Rollback Strategy
- Delta Lake provides automatic versioning
- Failed writes don't corrupt existing data
- Time travel capability for recovery
- Transaction log ensures ACID properties

## Configuration Management

### Configuration Hierarchy
1. **config.yaml**: Base configuration
2. **Environment Variables**: Override specific values
3. **Runtime Parameters**: Job-specific overrides

### Configuration Files

**`config/config.yaml`**
```yaml
spark:
  app_name: "ETL Pipeline"

catalog:
  name: ${CATALOG_NAME}
  schema: ${SCHEMA_NAME}

business_rules:
  order_size:
    large_threshold: 10
    medium_threshold: 5
```

**`.env`** (not committed)
```
CATALOG_NAME=datasets_github_projects
SCHEMA_NAME=default
DATABRICKS_HOST=https://...
```

## Testing Strategy

### Test Types
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: End-to-end pipeline flow
3. **Quality Tests**: Data validation logic

### Test Coverage
- Transformations: 100%
- Data Quality: 92%
- Overall: 61%

### Test Fixtures
- Sample sales data
- Data with nulls
- Data with negatives
- Data with duplicates
- Empty datasets

## Deployment

The pipeline uses **Databricks Asset Bundles** for deployment:

```bash
# Validate configuration
databricks bundle validate

# Deploy to dev environment
databricks bundle deploy --target dev

# Deploy to production
databricks bundle deploy --target prod
```

## Security Considerations

1. **No Hardcoded Credentials**
   - All sensitive values in environment variables
   - Databricks secrets for production

2. **Environment Isolation**
   - Separate dev/prod configurations
   - Different catalogs/schemas per environment

3. **Data Validation**
   - Input validation prevents injection
   - Schema enforcement
   - Type checking

## Performance Optimization

1. **Spark Optimizations**
   - Broadcast joins for small tables
   - Partition pruning
   - Column pruning

2. **Delta Optimizations**
   - OPTIMIZE for file compaction
   - ZORDER for data skipping
   - VACUUM for cleanup

3. **Pipeline Optimizations**
   - Early filtering
   - Lazy evaluation
   - Minimal shuffles

## Monitoring and Observability

### Logging
- Structured JSON logs in production
- Log levels: DEBUG, INFO, WARNING, ERROR
- Contextual information (job_id, timestamps)

### Metrics
- Record counts at each stage
- Processing time tracking
- Data quality scores
- Error rates

### Alerts
- Critical quality check failures
- Pipeline execution failures
- SLA violations

## Future Enhancements

1. **Advanced Features**
   - Streaming support
   - Complex event processing
   - Machine learning integration

2. **Operational Improvements**
   - Auto-scaling
   - Cost optimization
   - Advanced monitoring

3. **Data Quality**
   - Statistical anomaly detection
   - Schema evolution handling
   - Data lineage tracking
