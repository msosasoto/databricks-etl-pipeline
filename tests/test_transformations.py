"""
Unit tests for transformation module.
"""

import pytest
from pyspark.sql import functions as F

from src.transform.transformations import SalesTransformer, TransformationError


class TestSalesTransformer:
    """Test suite for SalesTransformer."""

    def test_calculate_total_amount(self, config):
        """Test total_amount calculation."""
        transformer = SalesTransformer(config)

        # Test valid calculation
        assert transformer.calculate_total_amount(5, 100.0) == 500.0
        assert transformer.calculate_total_amount(1, 1200.5) == 1200.5
        assert transformer.calculate_total_amount(10, 50.0) == 500.0

        # Test with decimals
        assert transformer.calculate_total_amount(2.5, 40.0) == 100.0

    def test_classify_order_size(self, config):
        """Test order size classification."""
        transformer = SalesTransformer(config)

        # Test Large orders (>= 10)
        assert transformer.classify_order_size(10) == "Large"
        assert transformer.classify_order_size(15) == "Large"
        assert transformer.classify_order_size(100) == "Large"

        # Test Medium orders (>= 5 and < 10)
        assert transformer.classify_order_size(5) == "Medium"
        assert transformer.classify_order_size(7) == "Medium"
        assert transformer.classify_order_size(9) == "Medium"

        # Test Small orders (< 5)
        assert transformer.classify_order_size(1) == "Small"
        assert transformer.classify_order_size(3) == "Small"
        assert transformer.classify_order_size(4) == "Small"

    def test_classify_price_category(self, config):
        """Test price category classification."""
        transformer = SalesTransformer(config)

        # Test Premium prices (>= 500)
        assert transformer.classify_price_category(500.0) == "Premium"
        assert transformer.classify_price_category(600.0) == "Premium"
        assert transformer.classify_price_category(1200.5) == "Premium"

        # Test Standard prices (>= 100 and < 500)
        assert transformer.classify_price_category(100.0) == "Standard"
        assert transformer.classify_price_category(300.0) == "Standard"
        assert transformer.classify_price_category(499.99) == "Standard"

        # Test Budget prices (< 100)
        assert transformer.classify_price_category(25.99) == "Budget"
        assert transformer.classify_price_category(75.0) == "Budget"
        assert transformer.classify_price_category(99.99) == "Budget"

    def test_transform_adds_all_columns(self, spark, config, sample_sales_data):
        """Test that transform adds all expected columns."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Check new columns exist
        expected_new_columns = [
            "total_amount",
            "year",
            "month",
            "day_of_week",
            "order_size",
            "price_category",
            "processed_at",
        ]

        for column in expected_new_columns:
            assert column in df_transformed.columns, f"Column {column} missing"

    def test_transform_total_amount_calculation(self, spark, config, sample_sales_data):
        """Test that total_amount is calculated correctly in DataFrame."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Get first row and verify calculation
        first_row = df_transformed.filter(F.col("order_id") == 1001).first()
        assert first_row["quantity"] == 1
        assert first_row["price"] == 1200.5
        assert first_row["total_amount"] == 1200.5

        # Check another row
        second_row = df_transformed.filter(F.col("order_id") == 1002).first()
        assert second_row["quantity"] == 2
        assert second_row["price"] == 25.99
        assert abs(second_row["total_amount"] - 51.98) < 0.01

    def test_transform_order_size_classification_in_df(self, spark, config, sample_sales_data):
        """Test order_size classification in DataFrame."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Check Large order (quantity=12)
        large_order = df_transformed.filter(F.col("order_id") == 1006).first()
        assert large_order["quantity"] == 12
        assert large_order["order_size"] == "Large"

        # Check Medium order (quantity=6)
        medium_order = df_transformed.filter(F.col("order_id") == 1007).first()
        assert medium_order["quantity"] == 6
        assert medium_order["order_size"] == "Medium"

        # Check Small order (quantity=1)
        small_order = df_transformed.filter(F.col("order_id") == 1001).first()
        assert small_order["quantity"] == 1
        assert small_order["order_size"] == "Small"

    def test_transform_price_category_in_df(self, spark, config, sample_sales_data):
        """Test price_category classification in DataFrame."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Check Premium price (1200.5)
        premium_item = df_transformed.filter(F.col("order_id") == 1001).first()
        assert premium_item["price"] == 1200.5
        assert premium_item["price_category"] == "Premium"

        # Check Standard price (300.0)
        standard_item = df_transformed.filter(F.col("order_id") == 1005).first()
        assert standard_item["price"] == 300.0
        assert standard_item["price_category"] == "Standard"

        # Check Budget price (25.99)
        budget_item = df_transformed.filter(F.col("order_id") == 1002).first()
        assert budget_item["price"] == 25.99
        assert budget_item["price_category"] == "Budget"

    def test_transform_date_components(self, spark, config, sample_sales_data):
        """Test date component extraction."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Check date components for a known date (2024-01-15)
        first_row = df_transformed.filter(F.col("order_id") == 1001).first()
        assert first_row["year"] == 2024
        assert first_row["month"] == 1
        # day_of_week varies by implementation, just check it exists
        assert first_row["day_of_week"] is not None

    def test_transform_preserves_original_data(self, spark, config, sample_sales_data):
        """Test that original columns and data are preserved."""
        transformer = SalesTransformer(config)

        original_count = sample_sales_data.count()
        df_transformed = transformer.transform(sample_sales_data)

        # Check row count unchanged
        assert df_transformed.count() == original_count

        # Check original columns exist
        original_columns = sample_sales_data.columns
        for column in original_columns:
            assert column in df_transformed.columns

    def test_transform_with_missing_columns_raises_error(self, spark, config):
        """Test that transform raises error when required columns are missing."""
        transformer = SalesTransformer(config)

        # Create DataFrame with missing columns
        incomplete_data = spark.createDataFrame(
            [(1, "Product A", 100.0)], ["order_id", "product_name", "price"]
        )

        with pytest.raises(TransformationError) as exc_info:
            transformer.transform(incomplete_data)

        assert "Missing required columns" in str(exc_info.value)

    def test_transform_processing_timestamp_added(self, spark, config, sample_sales_data):
        """Test that processed_at timestamp is added."""
        transformer = SalesTransformer(config)

        df_transformed = transformer.transform(sample_sales_data)

        # Check processed_at column exists
        assert "processed_at" in df_transformed.columns

        # Check it's not null
        null_count = df_transformed.filter(F.col("processed_at").isNull()).count()
        assert null_count == 0
