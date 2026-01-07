"""
Pytest configuration and fixtures for ETL Pipeline tests.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, DateType
)
from datetime import date

from src.config.settings import Config


@pytest.fixture(scope="session")
def spark():
    """
    Create a Spark session for testing.
    
    Returns:
        SparkSession instance configured for testing.
    """
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("ETL-Pipeline-Tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .getOrCreate()
    )
    
    yield spark
    
    spark.stop()


@pytest.fixture
def config():
    """
    Create a test configuration.
    
    Returns:
        Config instance for testing.
    """
    return Config()


@pytest.fixture
def sample_sales_schema():
    """
    Define the schema for sample sales data.
    
    Returns:
        StructType schema for sales data.
    """
    return StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", StringType(), False),
        StructField("product_name", StringType(), False),
        StructField("category", StringType(), False),
        StructField("quantity", IntegerType(), False),
        StructField("price", DoubleType(), False),
        StructField("order_date", DateType(), False),
        StructField("country", StringType(), False)
    ])


@pytest.fixture
def sample_sales_data(spark, sample_sales_schema):
    """
    Create sample sales data for testing.
    
    Args:
        spark: Spark session.
        sample_sales_schema: Schema for sales data.
    
    Returns:
        DataFrame with sample sales data.
    """
    data = [
        (1001, "C001", "Laptop", "Electronics", 1, 1200.5, date(2024, 1, 15), "Colombia"),
        (1002, "C002", "Mouse", "Electronics", 2, 25.99, date(2024, 1, 15), "Mexico"),
        (1003, "C001", "Keyboard", "Electronics", 1, 75.0, date(2024, 1, 16), "Colombia"),
        (1004, "C003", "Chair", "Furniture", 4, 150.0, date(2024, 1, 16), "USA"),
        (1005, "C002", "Monitor", "Electronics", 1, 300.0, date(2024, 1, 17), "Mexico"),
        (1006, "C004", "Desk", "Furniture", 12, 450.0, date(2024, 1, 17), "Canada"),
        (1007, "C005", "Phone", "Electronics", 6, 800.0, date(2024, 1, 18), "USA"),
        (1008, "C001", "Tablet", "Electronics", 3, 600.0, date(2024, 1, 18), "Colombia"),
        (1009, "C003", "Lamp", "Furniture", 8, 45.0, date(2024, 1, 19), "USA"),
        (1010, "C004", "Book", "Books", 15, 20.0, date(2024, 1, 19), "Canada")
    ]
    
    return spark.createDataFrame(data, sample_sales_schema)


@pytest.fixture
def sample_data_with_nulls(spark, sample_sales_schema):
    """
    Create sample sales data with null values.
    
    Args:
        spark: Spark session.
        sample_sales_schema: Schema for sales data.
    
    Returns:
        DataFrame with null values.
    """
    data = [
        (1001, "C001", "Laptop", "Electronics", 1, 1200.5, date(2024, 1, 15), "Colombia"),
        (1002, None, "Mouse", "Electronics", 2, 25.99, date(2024, 1, 15), "Mexico"),
        (1003, "C001", None, "Electronics", 1, 75.0, date(2024, 1, 16), "Colombia"),
        (1004, "C003", "Chair", None, 4, 150.0, date(2024, 1, 16), "USA"),
    ]
    
    return spark.createDataFrame(data, sample_sales_schema)


@pytest.fixture
def sample_data_with_negatives(spark, sample_sales_schema):
    """
    Create sample sales data with negative values.
    
    Args:
        spark: Spark session.
        sample_sales_schema: Schema for sales data.
    
    Returns:
        DataFrame with negative values.
    """
    data = [
        (1001, "C001", "Laptop", "Electronics", -1, 1200.5, date(2024, 1, 15), "Colombia"),
        (1002, "C002", "Mouse", "Electronics", 2, -25.99, date(2024, 1, 15), "Mexico"),
        (1003, "C001", "Keyboard", "Electronics", 1, 75.0, date(2024, 1, 16), "Colombia"),
    ]
    
    return spark.createDataFrame(data, sample_sales_schema)


@pytest.fixture
def sample_data_with_duplicates(spark, sample_sales_schema):
    """
    Create sample sales data with duplicate order IDs.
    
    Args:
        spark: Spark session.
        sample_sales_schema: Schema for sales data.
    
    Returns:
        DataFrame with duplicate order IDs.
    """
    data = [
        (1001, "C001", "Laptop", "Electronics", 1, 1200.5, date(2024, 1, 15), "Colombia"),
        (1001, "C002", "Mouse", "Electronics", 2, 25.99, date(2024, 1, 15), "Mexico"),
        (1003, "C001", "Keyboard", "Electronics", 1, 75.0, date(2024, 1, 16), "Colombia"),
    ]
    
    return spark.createDataFrame(data, sample_sales_schema)
