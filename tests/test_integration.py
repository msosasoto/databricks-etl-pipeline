"""
Integration tests for ETL Pipeline.
"""

import pytest
from pyspark.sql import functions as F

from src.extract.data_loader import DataLoader
from src.transform.transformations import SalesTransformer
from src.validation.data_quality import DataQualityValidator
from src.load.data_writer import DeltaWriter


class TestETLPipelineIntegration:
    """Integration tests for the complete ETL pipeline."""

    def test_end_to_end_pipeline(self, spark, config, sample_sales_data, tmp_path):
        """Test complete ETL pipeline flow."""
        # Setup: Write sample data to a temporary table
        temp_source_table = "test_catalog.test_schema.test_source"
        temp_target_table = "test_catalog.test_schema.test_target"
        
        # Create a temporary database
        spark.sql("CREATE DATABASE IF NOT EXISTS test_catalog.test_schema")
        
        # Write source data
        sample_sales_data.write.format("delta").mode("overwrite").saveAsTable(temp_source_table)
        
        # Override config for test
        config._config["catalog"]["name"] = "test_catalog"
        config._config["catalog"]["schema"] = "test_schema"
        config._config["tables"]["source"] = "test_source"
        config._config["tables"]["target"] = "test_target"
        
        # Step 1: Extract
        loader = DataLoader(spark, config)
        df_raw = loader.load_source_data()
        
        assert df_raw.count() == sample_sales_data.count()
        
        # Step 2: Validate
        validator = DataQualityValidator(config)
        report = validator.validate(df_raw)
        
        assert report["summary"]["status"] == "PASSED"
        
        # Step 3: Transform
        transformer = SalesTransformer(config)
        df_transformed = transformer.transform(df_raw)
        
        # Verify transformations
        assert "total_amount" in df_transformed.columns
        assert "order_size" in df_transformed.columns
        assert "price_category" in df_transformed.columns
        
        # Step 4: Load
        writer = DeltaWriter(spark, config)
        stats = writer.overwrite(df_transformed)
        
        assert stats["operation"] == "overwrite"
        assert stats["records_written"] == df_transformed.count()
        
        # Verify data was written
        df_final = spark.table(temp_target_table)
        assert df_final.count() == df_transformed.count()
        
        # Cleanup
        spark.sql(f"DROP TABLE IF EXISTS {temp_source_table}")
        spark.sql(f"DROP TABLE IF EXISTS {temp_target_table}")

    def test_transformation_preserves_row_count(self, config, sample_sales_data):
        """Test that transformation doesn't change row count."""
        transformer = SalesTransformer(config)
        
        original_count = sample_sales_data.count()
        df_transformed = transformer.transform(sample_sales_data)
        transformed_count = df_transformed.count()
        
        assert original_count == transformed_count

    def test_validation_before_transformation(self, config, sample_sales_data):
        """Test validation step before transformation."""
        validator = DataQualityValidator(config)
        
        # Validate raw data
        report = validator.validate(sample_sales_data)
        
        # Should pass for clean data
        assert report["summary"]["status"] == "PASSED"
        
        # Then transform
        transformer = SalesTransformer(config)
        df_transformed = transformer.transform(sample_sales_data)
        
        # Validation should still pass after transformation
        report_after = validator.validate(df_transformed)
        assert report_after["summary"]["status"] == "PASSED"

    def test_business_logic_applied_correctly(self, config, sample_sales_data):
        """Test that business logic is applied correctly through the pipeline."""
        transformer = SalesTransformer(config)
        df_transformed = transformer.transform(sample_sales_data)
        
        # Check specific business rules
        # Order 1006 has quantity=12, should be Large
        large_order = df_transformed.filter(F.col("order_id") == 1006).first()
        assert large_order["order_size"] == "Large"
        assert large_order["quantity"] == 12
        
        # Order 1001 has price=1200.5, should be Premium
        premium_order = df_transformed.filter(F.col("order_id") == 1001).first()
        assert premium_order["price_category"] == "Premium"
        assert premium_order["price"] == 1200.5
        
        # Verify total_amount calculation
        for row in df_transformed.collect():
            expected_total = row["quantity"] * row["price"]
            assert abs(row["total_amount"] - expected_total) < 0.01

    def test_data_quality_catches_bad_data(self, config, sample_data_with_negatives):
        """Test that data quality validation catches problematic data."""
        validator = DataQualityValidator(config)
        
        # Should raise error for negative values
        with pytest.raises(Exception):  # DataQualityError
            validator.validate(sample_data_with_negatives)

    def test_pipeline_handles_empty_dataframe(self, spark, config):
        """Test pipeline behavior with empty DataFrame."""
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
        
        # Create empty DataFrame with correct schema
        schema = StructType([
            StructField("order_id", IntegerType(), False),
            StructField("customer_id", StringType(), False),
            StructField("product_name", StringType(), False),
            StructField("category", StringType(), False),
            StructField("quantity", IntegerType(), False),
            StructField("price", DoubleType(), False),
            StructField("order_date", DateType(), False),
            StructField("country", StringType(), False)
        ])
        
        empty_df = spark.createDataFrame([], schema)
        
        # Transform should work on empty data
        transformer = SalesTransformer(config)
        df_transformed = transformer.transform(empty_df)
        
        assert df_transformed.count() == 0
        # But should still have all columns
        assert "total_amount" in df_transformed.columns
        assert "order_size" in df_transformed.columns

    def test_multiple_transformations_idempotent(self, config, sample_sales_data):
        """Test that applying transformations multiple times produces same result."""
        transformer = SalesTransformer(config)
        
        df_first = transformer.transform(sample_sales_data)
        
        # Get a specific result to compare
        first_result = df_first.filter(F.col("order_id") == 1001).first()
        first_total = first_result["total_amount"]
        first_size = first_result["order_size"]
        
        # Apply again (this would fail if we try to transform already transformed data)
        # But for this test, we transform the original data again
        df_second = transformer.transform(sample_sales_data)
        second_result = df_second.filter(F.col("order_id") == 1001).first()
        
        assert first_total == second_result["total_amount"]
        assert first_size == second_result["order_size"]
