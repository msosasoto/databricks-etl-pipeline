"""
Data loading/writing module.

Handles writing data to Delta tables with merge (upsert) support.
"""

from typing import Optional, List, Dict
from pyspark.sql import SparkSession, DataFrame
from delta.tables import DeltaTable
import logging

from src.config.settings import Config

logger = logging.getLogger(__name__)


class DataWriteError(Exception):
    """Custom exception for data writing errors."""
    pass


class DeltaWriter:
    """Handles writing data to Delta tables with upsert support."""

    def __init__(self, spark: SparkSession, config: Config):
        """
        Initialize DeltaWriter.

        Args:
            spark: SparkSession instance.
            config: Configuration object.
        """
        self.spark = spark
        self.config = config
        logger.info("DeltaWriter initialized")

    def upsert(
        self,
        df: DataFrame,
        merge_key: str = "order_id",
        target_table: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Perform upsert (merge) operation on Delta table.

        Args:
            df: DataFrame to write.
            merge_key: Column name to use for merge condition.
            target_table: Optional target table name (uses config if not provided).

        Returns:
            Dictionary with merge statistics (inserted, updated).

        Raises:
            DataWriteError: If write operation fails.

        Example:
            >>> writer = DeltaWriter(spark, config)
            >>> stats = writer.upsert(df, merge_key="order_id")
            >>> print(f"Inserted: {stats['inserted']}, Updated: {stats['updated']}")
        """
        table_name = target_table or self.config.target_table_full
        
        try:
            logger.info(f"Starting upsert operation to: {table_name}")
            logger.info(f"Merge key: {merge_key}")
            
            # Validate merge key exists
            if merge_key not in df.columns:
                raise DataWriteError(f"Merge key '{merge_key}' not found in DataFrame")
            
            # Check if table exists
            if self._table_exists(table_name):
                # Perform merge
                stats = self._merge_data(df, table_name, merge_key)
                logger.info(f"Upsert completed: {stats}")
            else:
                # Create new table
                stats = self._create_table(df, table_name)
                logger.info(f"New table created: {stats}")
            
            return stats
            
        except DataWriteError:
            raise
        except Exception as e:
            error_msg = f"Upsert operation failed: {str(e)}"
            logger.error(error_msg)
            raise DataWriteError(error_msg) from e

    def _table_exists(self, table_name: str) -> bool:
        """
        Check if Delta table exists.

        Args:
            table_name: Fully qualified table name.

        Returns:
            True if table exists.
        """
        try:
            self.spark.table(table_name)
            return True
        except Exception:
            return False

    def _merge_data(
        self,
        df: DataFrame,
        table_name: str,
        merge_key: str
    ) -> Dict[str, int]:
        """
        Merge data into existing Delta table.

        Args:
            df: Source DataFrame.
            table_name: Target table name.
            merge_key: Column for merge condition.

        Returns:
            Dictionary with merge statistics.
        """
        logger.info("Performing Delta merge operation")
        
        # Load Delta table
        delta_table = DeltaTable.forName(self.spark, table_name)
        
        # Build merge condition
        merge_condition = f"target.{merge_key} = source.{merge_key}"
        
        # Get column list for update/insert
        columns = df.columns
        update_set = {col: f"source.{col}" for col in columns}
        insert_values = {col: f"source.{col}" for col in columns}
        
        # Execute merge
        merge_builder = delta_table.alias("target").merge(
            df.alias("source"),
            merge_condition
        )
        
        # When matched, update
        merge_builder = merge_builder.whenMatchedUpdate(set=update_set)
        
        # When not matched, insert
        merge_builder = merge_builder.whenNotMatchedInsert(values=insert_values)
        
        # Execute merge
        merge_builder.execute()
        
        # Get statistics (approximate)
        # Note: Actual stats would require tracking before/after counts
        stats = {
            "operation": "merge",
            "table": table_name,
            "source_records": df.count(),
            "merge_key": merge_key
        }
        
        return stats

    def _create_table(self, df: DataFrame, table_name: str) -> Dict[str, int]:
        """
        Create new Delta table.

        Args:
            df: DataFrame to write.
            table_name: Target table name.

        Returns:
            Dictionary with creation statistics.
        """
        logger.info(f"Creating new Delta table: {table_name}")
        
        record_count = df.count()
        
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(table_name)
        
        stats = {
            "operation": "create",
            "table": table_name,
            "inserted": record_count
        }
        
        return stats

    def overwrite(
        self,
        df: DataFrame,
        target_table: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Overwrite entire Delta table.

        Args:
            df: DataFrame to write.
            target_table: Optional target table name.

        Returns:
            Dictionary with write statistics.

        Raises:
            DataWriteError: If write operation fails.

        Example:
            >>> writer = DeltaWriter(spark, config)
            >>> stats = writer.overwrite(df)
        """
        table_name = target_table or self.config.target_table_full
        
        try:
            logger.info(f"Overwriting table: {table_name}")
            
            record_count = df.count()
            
            df.write \
                .format("delta") \
                .mode("overwrite") \
                .option("overwriteSchema", "true") \
                .saveAsTable(table_name)
            
            stats = {
                "operation": "overwrite",
                "table": table_name,
                "records_written": record_count
            }
            
            logger.info(f"Overwrite completed: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Overwrite operation failed: {str(e)}"
            logger.error(error_msg)
            raise DataWriteError(error_msg) from e

    def append(
        self,
        df: DataFrame,
        target_table: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Append data to Delta table.

        Args:
            df: DataFrame to append.
            target_table: Optional target table name.

        Returns:
            Dictionary with append statistics.

        Raises:
            DataWriteError: If append operation fails.

        Example:
            >>> writer = DeltaWriter(spark, config)
            >>> stats = writer.append(df)
        """
        table_name = target_table or self.config.target_table_full
        
        try:
            logger.info(f"Appending to table: {table_name}")
            
            record_count = df.count()
            
            df.write \
                .format("delta") \
                .mode("append") \
                .saveAsTable(table_name)
            
            stats = {
                "operation": "append",
                "table": table_name,
                "records_appended": record_count
            }
            
            logger.info(f"Append completed: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"Append operation failed: {str(e)}"
            logger.error(error_msg)
            raise DataWriteError(error_msg) from e
