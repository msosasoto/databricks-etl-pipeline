"""
Data extraction/loading module.

Handles reading data from various sources including Delta tables.
"""

from typing import Optional
from pyspark.sql import SparkSession, DataFrame
import logging

from src.config.settings import Config
from src.utils.spark_utils import check_table_exists

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


class DataLoader:
    """Handles data extraction from sources."""

    def __init__(self, spark: SparkSession, config: Config):
        """
        Initialize DataLoader.

        Args:
            spark: SparkSession instance.
            config: Configuration object.
        """
        self.spark = spark
        self.config = config
        logger.info("DataLoader initialized")

    def load_source_data(self) -> DataFrame:
        """
        Load data from source table.

        Returns:
            DataFrame containing source data.

        Raises:
            DataLoadError: If source table doesn't exist or loading fails.

        Example:
            >>> loader = DataLoader(spark, config)
            >>> df = loader.load_source_data()
        """
        table_name = self.config.source_table_full
        
        try:
            logger.info(f"Loading data from: {table_name}")
            
            # Check if table exists
            if not check_table_exists(self.spark, table_name):
                raise DataLoadError(f"Source table does not exist: {table_name}")
            
            # Load data
            df = self.spark.table(table_name)
            row_count = df.count()
            
            logger.info(f"Successfully loaded {row_count} records from {table_name}")
            
            # Log schema info
            logger.debug(f"Schema columns: {df.columns}")
            
            return df
            
        except DataLoadError:
            raise
        except Exception as e:
            error_msg = f"Failed to load data from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise DataLoadError(error_msg) from e

    def load_table(self, table_name: str) -> DataFrame:
        """
        Load data from a specific table.

        Args:
            table_name: Fully qualified table name.

        Returns:
            DataFrame containing table data.

        Raises:
            DataLoadError: If table doesn't exist or loading fails.

        Example:
            >>> loader = DataLoader(spark, config)
            >>> df = loader.load_table("catalog.schema.my_table")
        """
        try:
            logger.info(f"Loading data from custom table: {table_name}")
            
            # Check if table exists
            if not check_table_exists(self.spark, table_name):
                raise DataLoadError(f"Table does not exist: {table_name}")
            
            # Load data
            df = self.spark.table(table_name)
            row_count = df.count()
            
            logger.info(f"Successfully loaded {row_count} records from {table_name}")
            return df
            
        except DataLoadError:
            raise
        except Exception as e:
            error_msg = f"Failed to load data from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise DataLoadError(error_msg) from e

    def validate_schema(
        self,
        df: DataFrame,
        required_columns: list
    ) -> bool:
        """
        Validate that DataFrame contains required columns.

        Args:
            df: DataFrame to validate.
            required_columns: List of required column names.

        Returns:
            True if all required columns exist.

        Raises:
            DataLoadError: If required columns are missing.

        Example:
            >>> loader.validate_schema(df, ["order_id", "price", "quantity"])
        """
        df_columns = set(df.columns)
        required_set = set(required_columns)
        missing_columns = required_set - df_columns
        
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise DataLoadError(error_msg)
        
        logger.info("Schema validation passed")
        return True
