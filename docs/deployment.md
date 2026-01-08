# Deployment Guide

This guide covers deploying the ETL pipeline to Databricks using Asset Bundles.

## Prerequisites

### Required Tools
- **Databricks CLI** (v0.275+)
- **Python** 3.10+
- **Git** for version control
- **Databricks Workspace** (Free Tier or higher)

### Installation

1. **Install Databricks CLI**
   ```bash
   pip install databricks-cli
   ```

2. **Install Project Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/msosasoto/databricks-etl-pipeline.git
cd databricks-etl-pipeline
```

### 2. Configure Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
CATALOG_NAME=datasets_github_projects
SCHEMA_NAME=default
LOG_LEVEL=INFO
```

### 3. Authenticate with Databricks

```bash
databricks auth login --host $DATABRICKS_HOST
```

Follow the prompts to authenticate.

### 4. Prepare Source Data

Upload your source data to Databricks:

**Option A: Using Databricks UI**
1. Go to **Data** → **Create Table**
2. Upload `data/raw/ventas_raw.csv`
3. Create as: `datasets_github_projects.default.ventas_raw`

**Option B: Using Spark**
```python
# In a Databricks notebook
df = spark.read.csv("/path/to/ventas_raw.csv", header=True, inferSchema=True)
df.write.format("delta").mode("overwrite").saveAsTable("datasets_github_projects.default.ventas_raw")
```

## Deployment Workflow

### Development Environment

1. **Validate Bundle Configuration**
   ```bash
   databricks bundle validate
   ```

2. **Deploy to Dev**
   ```bash
   databricks bundle deploy --target dev
   ```

3. **Run the Job**
   
   **Option A: Via CLI**
   ```bash
   databricks jobs run-now --job-id <job-id>
   ```
   
   **Option B: Via Web UI**
   - Navigate to **Workflows** → `[dev] ETL Pipeline`
   - Click **Run Now**

4. **View Logs**
   ```bash
   databricks jobs get-run --run-id <run-id>
   ```

### Production Deployment

1. **Update Configuration**
   
   Edit `databricks.yml` to add production target:
   
   ```yaml
   targets:
     prod:
       mode: production
       workspace:
         host: ${DATABRICKS_HOST}
         root_path: /.bundle/${bundle.name}/prod
   ```

2. **Deploy to Production**
   ```bash
   databricks bundle deploy --target prod
   ```

3. **Schedule the Job**
   
   Add scheduling to `databricks.yml`:
   
   ```yaml
   resources:
     jobs:
       etl_pipeline_job:
         schedule:
           quartz_cron_expression: "0 0 2 * * ?"  # Daily at 2 AM
           timezone_id: "America/Bogota"
           pause_status: "UNPAUSED"
   ```

4. **Redeploy with Schedule**
   ```bash
   databricks bundle deploy --target prod
   ```

## Configuration Management

### Environment-Specific Configuration

**Development (`dev` target)**
- Uses `${DATABRICKS_HOST}` from environment
- Workspace path: `/.bundle/databricks-etl-pipeline/dev`
- Manual execution

**Production (`prod` target)**
- Same host, different workspace path
- Scheduled execution
- Additional monitoring

### Business Rules Configuration

Edit `config/config.yaml` to adjust business logic:

```yaml
business_rules:
  order_size:
    large_threshold: 10    # Change thresholds
    medium_threshold: 5
  price_category:
    premium_threshold: 500
    standard_threshold: 100
```

Redeploy after changes:
```bash
databricks bundle deploy
```

## Monitoring Deployments

### Check Job Status

```bash
# List all jobs
databricks jobs list

# Get specific job details
databricks jobs get --job-id <job-id>

# Get run history
databricks runs list --job-id <job-id>
```

### View Logs

```bash
# Get run output
databricks runs get-output --run-id <run-id>

# View specific notebook run
databricks jobs get-run --run-id <run-id>
```

### Access Delta Tables

```sql
-- Check target table
SELECT * FROM datasets_github_projects.default.ventas_transformed LIMIT 10;

-- View table history
DESCRIBE HISTORY datasets_github_projects.default.ventas_transformed;

-- Table statistics
DESCRIBE EXTENDED datasets_github_projects.default.ventas_transformed;
```

## Rollback Strategy

### Roll Back to Previous Version

1. **Find Previous Version**
   ```sql
   DESCRIBE HISTORY datasets_github_projects.default.ventas_transformed;
   ```

2. **Time Travel to Previous Version**
   ```sql
   SELECT * FROM datasets_github_projects.default.ventas_transformed 
   VERSION AS OF 2;
   ```

3. **Restore Previous Version**
   ```sql
   RESTORE TABLE datasets_github_projects.default.ventas_transformed 
   TO VERSION AS OF 2;
   ```

### Roll Back Code Deployment

1. **Checkout Previous Commit**
   ```bash
   git log --oneline
   git checkout <commit-hash>
   ```

2. **Redeploy**
   ```bash
   databricks bundle deploy --target prod
   ```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: `Error: authentication required`

**Solution**:
```bash
databricks auth login --host $DATABRICKS_HOST
```

#### 2. Bundle Validation Errors

**Problem**: `Error: invalid configuration`

**Solution**:
```bash
# Check YAML syntax
databricks bundle validate

# Verify environment variables
echo $DATABRICKS_HOST
```

#### 3. Source Table Not Found

**Problem**: `Table not found: datasets_github_projects.default.ventas_raw`

**Solution**:
- Verify table exists in Databricks UI
- Check catalog/schema names in `.env`
- Ensure data is loaded

#### 4. Permission Errors

**Problem**: `Error: access denied`

**Solution**:
- Verify workspace permissions
- Check catalog/schema access rights
- Contact Databricks admin

#### 5. Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
- Ensure `src/` directory is included in deployment
- Verify Databricks notebook can access workspace files
- Check Asset Bundle sync settings

### Debug Mode

Enable verbose logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Redeploy
databricks bundle deploy --target dev
```

View detailed logs in notebook execution.

## Best Practices

### 1. Development Workflow

```
Local Dev → Test → Commit → Deploy Dev → Test → Deploy Prod
```

1. Develop locally with unit tests
2. Run full test suite
3. Commit to feature branch
4. Deploy to dev environment
5. Validate in dev
6. Merge to main
7. Deploy to production

### 2. Configuration Management

- **Never commit secrets**: Use `.env` and `.gitignore`
- **Use environment variables**: For environment-specific values
- **Version control config**: Track `config.yaml` changes
- **Document changes**: Update CHANGELOG

### 3. Testing Before Deployment

```bash
# Run tests locally
pytest tests/ -v --cov=src

# Validate bundle
databricks bundle validate

# Deploy to dev first
databricks bundle deploy --target dev
```

### 4. Monitoring Post-Deployment

- Check job execution status
- Verify data quality reports
- Monitor record counts
- Review logs for errors
- Validate business metrics

### 5. Scheduled Jobs

- Set appropriate schedules (avoid peak hours)
- Configure retries for transient failures
- Set up email notifications
- Monitor SLA compliance

## CI/CD Integration

### GitHub Actions Workflow

The project includes a CI pipeline (`.github/workflows/ci.yml`):

- Runs on push/PR to main branch
- Executes linting checks
- Runs full test suite
- Reports code coverage

### Manual Deployment After CI

```bash
# After CI passes
git pull origin main

# Deploy to production
databricks bundle deploy --target prod
```

### Automated Deployment (Future)

Add deployment step to GitHub Actions:

```yaml
- name: Deploy to Databricks
  run: |
    databricks auth login --host ${{ secrets.DATABRICKS_HOST }}
    databricks bundle deploy --target prod
  env:
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## Performance Tuning

### Cluster Configuration

For production workloads, consider:

```yaml
tasks:
  - task_key: etl_transform
    new_cluster:
      spark_version: "13.3.x-scala2.12"
      node_type_id: "i3.xlarge"
      num_workers: 2
      spark_conf:
        "spark.sql.adaptive.enabled": "true"
        "spark.sql.adaptive.coalescePartitions.enabled": "true"
```

### Delta Optimizations

Run regularly in production:

```sql
-- Optimize for better read performance
OPTIMIZE datasets_github_projects.default.ventas_transformed
ZORDER BY (order_date, country);

-- Clean up old files (after 7 days retention)
VACUUM datasets_github_projects.default.ventas_transformed RETAIN 168 HOURS;
```

## Security Checklist

- [ ] Secrets stored in Databricks Secrets
- [ ] `.env` file in `.gitignore`
- [ ] Minimum required permissions for service accounts
- [ ] Data encryption at rest enabled
- [ ] Network security groups configured
- [ ] Audit logging enabled
- [ ] Regular security reviews scheduled

## Support and Resources

- **Documentation**: `/docs/architecture.md`
- **Issues**: GitHub Issues
- **Databricks Docs**: [docs.databricks.com](https://docs.databricks.com)
- **Delta Lake Docs**: [delta.io](https://delta.io)

## Maintenance

### Regular Tasks

**Weekly**:
- Review job execution logs
- Check data quality reports
- Monitor cluster costs

**Monthly**:
- Update dependencies
- Review and optimize queries
- Vacuum old Delta versions
- Security audit

**Quarterly**:
- Performance review
- Cost optimization
- Architecture review
- Dependency updates
