"""
Data transformation module.

Implements business logic transformations for sales data.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import logging
from datetime import datetime

from src.config.settings import Config

logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Custom exception for transformation errors."""
    pass


class SalesTransformer:
    """Handles sales data transformations."""

    def __init__(self, config: Config):
        """
        Initialize SalesTransformer.

        Args:
            config: Configuration object.
        """
        self.config = config
        logger.info("SalesTransformer initialized")

    def transform(self, df: DataFrame) -> DataFrame:
        """
        Apply all transformations to the input DataFrame.

        Args:
            df: Input DataFrame with raw sales data.

        Returns:
            Transformed DataFrame.

        Raises:
            TransformationError: If transformation fails.

        Example:
            >>> transformer = SalesTransformer(config)
            >>> df_transformed = transformer.transform(df_raw)
        """
        try:
            logger.info("Starting data transformations")
            
            # Validate input
            self._validate_input(df)
            
            # Apply transformations
            df_transformed = df
            df_transformed = self._add_total_amount(df_transformed)
            df_transformed = self._add_date_components(df_transformed)
            df_transformed = self._add_order_size_classification(df_transformed)
            df_transformed = self._add_price_category(df_transformed)
            df_transformed = self._add_processing_timestamp(df_transformed)
            
            logger.info(f"Transformations completed. Output columns: {df_transformed.columns}")
            return df_transformed
            
        except Exception as e:
            error_msg = f"Transformation failed: {str(e)}"
            logger.error(error_msg)
            raise TransformationError(error_msg) from e

    def _validate_input(self, df: DataFrame) -> None:
        """
        Validate input DataFrame has required columns.

        Args:
            df: Input DataFrame to validate.

        Raises:
            TransformationError: If required columns are missing.
        """
        required_columns = ["order_id", "quantity", "price", "order_date"]
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            raise TransformationError(
                f"Missing required columns for transformation: {missing_columns}"
            )
        
        logger.debug("Input validation passed")

    def _add_total_amount(self, df: DataFrame) -> DataFrame:
        """
        Calculate total amount (quantity × price).

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with total_amount column.
        """
        logger.debug("Adding total_amount column")
        return df.withColumn(
            "total_amount",
            (F.col("quantity") * F.col("price")).cast(DoubleType())
        )

    def _add_date_components(self, df: DataFrame) -> DataFrame:
        """
        Extract date components (year, month, day_of_week).

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with date component columns.
        """
        logger.debug("Adding date component columns")
        return df \
            .withColumn("year", F.year("order_date")) \
            .withColumn("month", F.month("order_date")) \
            .withColumn("day_of_week", F.dayofweek("order_date"))

    def _add_order_size_classification(self, df: DataFrame) -> DataFrame:
        """
        Classify orders by size (Large/Medium/Small).

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with order_size column.
        """
        logger.debug("Adding order_size classification")
        
        large_threshold = self.config.order_size_large_threshold
        medium_threshold = self.config.order_size_medium_threshold
        
        return df.withColumn(
            "order_size",
            F.when(F.col("quantity") >= large_threshold, "Large")
            .when(F.col("quantity") >= medium_threshold, "Medium")
            .otherwise("Small")
        )

    def _add_price_category(self, df: DataFrame) -> DataFrame:
        """
        Categorize by price (Premium/Standard/Budget).

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with price_category column.
        """
        logger.debug("Adding price_category column")
        
        premium_threshold = self.config.price_premium_threshold
        standard_threshold = self.config.price_standard_threshold
        
        return df.withColumn(
            "price_category",
            F.when(F.col("price") >= premium_threshold, "Premium")
            .when(F.col("price") >= standard_threshold, "Standard")
            .otherwise("Budget")
        )

    def _add_processing_timestamp(self, df: DataFrame) -> DataFrame:
        """
        Add processing timestamp.

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with processed_at column.
        """
        logger.debug("Adding processing timestamp")
        return df.withColumn(
            "processed_at",
            F.lit(datetime.now()).cast("timestamp")
        )

    def calculate_total_amount(self, quantity: float, price: float) -> float:
        """
        Calculate total amount for a single order.

        Args:
            quantity: Order quantity.
            price: Unit price.

        Returns:
            Total amount.

        Example:
            >>> transformer = SalesTransformer(config)
            >>> total = transformer.calculate_total_amount(5, 100.0)
            >>> assert total == 500.0
        """
        return float(quantity * price)

    def classify_order_size(self, quantity: int) -> str:
        """
        Classify order size based on quantity.

        Args:
            quantity: Order quantity.

        Returns:
            Size classification (Large/Medium/Small).

        Example:
            >>> transformer = SalesTransformer(config)
            >>> size = transformer.classify_order_size(15)
            >>> assert size == "Large"
        """
        if quantity >= self.config.order_size_large_threshold:
            return "Large"
        elif quantity >= self.config.order_size_medium_threshold:
            return "Medium"
        else:
            return "Small"

    def classify_price_category(self, price: float) -> str:
        """
        Classify price category.

        Args:
            price: Unit price.

        Returns:
            Price category (Premium/Standard/Budget).

        Example:
            >>> transformer = SalesTransformer(config)
            >>> category = transformer.classify_price_category(600.0)
            >>> assert category == "Premium"
        """
        if price >= self.config.price_premium_threshold:
            return "Premium"
        elif price >= self.config.price_standard_threshold:
            return "Standard"
        else:
            return "Budget"
