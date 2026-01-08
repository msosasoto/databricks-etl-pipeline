"""
Spark utility functions.

Provides helper functions for Spark session management and common operations.
"""

from typing import Optional, Dict, Any
from pyspark.sql import SparkSession
import logging

logger = logging.getLogger(__name__)


def get_spark_session(
    app_name: str = "ETL Pipeline", config: Optional[Dict[str, Any]] = None
) -> SparkSession:
    """
    Get or create Spark session with Delta Lake support.

    Args:
        app_name: Name of the Spark application.
        config: Additional Spark configuration options.

    Returns:
        SparkSession instance.

    Example:
        >>> spark = get_spark_session("MyApp", {"spark.sql.shuffle.partitions": "200"})
    """
    builder = SparkSession.builder.appName(app_name)

    # Add Delta Lake support
    builder = builder.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    builder = builder.config(
        "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    )

    # Add additional config if provided
    if config:
        for key, value in config.items():
            builder = builder.config(key, value)

    # Get or create session
    try:
        spark = builder.getOrCreate()
        logger.info(f"Spark session created/retrieved: {app_name}")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise


def optimize_delta_table(
    spark: SparkSession, table_name: str, zorder_columns: Optional[list] = None
) -> None:
    """
    Optimize Delta table with optional Z-ordering.

    Args:
        spark: SparkSession instance.
        table_name: Fully qualified table name.
        zorder_columns: Optional list of columns for Z-ordering.

    Example:
        >>> optimize_delta_table(spark, "catalog.schema.table", ["date", "country"])
    """
    try:
        logger.info(f"Optimizing Delta table: {table_name}")

        if zorder_columns:
            zorder_clause = ", ".join(zorder_columns)
            spark.sql(f"OPTIMIZE {table_name} ZORDER BY ({zorder_clause})")
            logger.info(f"Table optimized with Z-ordering on: {zorder_columns}")
        else:
            spark.sql(f"OPTIMIZE {table_name}")
            logger.info("Table optimized without Z-ordering")

    except Exception as e:
        logger.error(f"Failed to optimize table {table_name}: {str(e)}")
        raise


def vacuum_delta_table(spark: SparkSession, table_name: str, retention_hours: int = 168) -> None:
    """
    Vacuum Delta table to remove old files.

    Args:
        spark: SparkSession instance.
        table_name: Fully qualified table name.
        retention_hours: Retention period in hours (default: 7 days).

    Example:
        >>> vacuum_delta_table(spark, "catalog.schema.table", retention_hours=168)
    """
    try:
        logger.info(f"Vacuuming Delta table: {table_name} (retention: {retention_hours}h)")
        spark.sql(f"VACUUM {table_name} RETAIN {retention_hours} HOURS")
        logger.info("Table vacuumed successfully")
    except Exception as e:
        logger.error(f"Failed to vacuum table {table_name}: {str(e)}")
        raise


def get_table_stats(spark: SparkSession, table_name: str) -> Dict[str, Any]:
    """
    Get statistics about a Delta table.

    Args:
        spark: SparkSession instance.
        table_name: Fully qualified table name.

    Returns:
        Dictionary containing table statistics.

    Example:
        >>> stats = get_table_stats(spark, "catalog.schema.table")
        >>> print(f"Row count: {stats['row_count']}")
    """
    try:
        df = spark.table(table_name)
        row_count = df.count()
        column_count = len(df.columns)

        stats = {
            "table_name": table_name,
            "row_count": row_count,
            "column_count": column_count,
            "columns": df.columns,
        }

        logger.info(f"Table stats retrieved: {row_count} rows, {column_count} columns")
        return stats

    except Exception as e:
        logger.error(f"Failed to get stats for table {table_name}: {str(e)}")
        raise


def check_table_exists(spark: SparkSession, table_name: str) -> bool:
    """
    Check if a table exists.

    Args:
        spark: SparkSession instance.
        table_name: Fully qualified table name.

    Returns:
        True if table exists, False otherwise.

    Example:
        >>> if check_table_exists(spark, "catalog.schema.table"):
        ...     print("Table exists")
    """
    try:
        spark.table(table_name)
        return True
    except Exception:
        return False
