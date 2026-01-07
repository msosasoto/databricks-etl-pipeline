"""
Configuration settings for ETL Pipeline.

This module handles loading configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Centralized configuration for the ETL pipeline."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config YAML file. If None, uses default location.
        """
        # Load environment variables
        load_dotenv()

        # Determine config path
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}

        # Load configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and apply environment variables."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # Use default configuration if file doesn't exist
            self._config = self._get_default_config()

        # Replace environment variable placeholders
        self._apply_env_vars(self._config)

    def _apply_env_vars(self, config: Dict[str, Any]) -> None:
        """
        Recursively replace ${VAR_NAME} placeholders with environment variables.

        Args:
            config: Configuration dictionary to process.
        """
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, value)
            elif isinstance(value, dict):
                self._apply_env_vars(value)

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration when config file doesn't exist.

        Returns:
            Default configuration dictionary.
        """
        return {
            "spark": {
                "app_name": "ETL Pipeline"
            },
            "catalog": {
                "name": os.getenv("CATALOG_NAME", "datasets_github_projects"),
                "schema": os.getenv("SCHEMA_NAME", "default")
            },
            "tables": {
                "source": "ventas_raw",
                "target": "ventas_transformed"
            },
            "business_rules": {
                "order_size": {
                    "large_threshold": 10,
                    "medium_threshold": 5
                },
                "price_category": {
                    "premium_threshold": 500,
                    "standard_threshold": 100
                }
            },
            "data_quality": {
                "max_null_percentage": 5,
                "check_duplicates": True,
                "validate_negative_values": True
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key using dot notation.

        Args:
            key: Configuration key (e.g., 'catalog.name').
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @property
    def spark_app_name(self) -> str:
        """Get Spark application name."""
        return self.get("spark.app_name", "ETL Pipeline")

    @property
    def catalog_name(self) -> str:
        """Get catalog name."""
        return self.get("catalog.name", "datasets_github_projects")

    @property
    def schema_name(self) -> str:
        """Get schema name."""
        return self.get("catalog.schema", "default")

    @property
    def source_table(self) -> str:
        """Get source table name."""
        return self.get("tables.source", "ventas_raw")

    @property
    def target_table(self) -> str:
        """Get target table name."""
        return self.get("tables.target", "ventas_transformed")

    @property
    def source_table_full(self) -> str:
        """Get fully qualified source table name."""
        return f"{self.catalog_name}.{self.schema_name}.{self.source_table}"

    @property
    def target_table_full(self) -> str:
        """Get fully qualified target table name."""
        return f"{self.catalog_name}.{self.schema_name}.{self.target_table}"

    @property
    def order_size_large_threshold(self) -> int:
        """Get large order size threshold."""
        return self.get("business_rules.order_size.large_threshold", 10)

    @property
    def order_size_medium_threshold(self) -> int:
        """Get medium order size threshold."""
        return self.get("business_rules.order_size.medium_threshold", 5)

    @property
    def price_premium_threshold(self) -> float:
        """Get premium price threshold."""
        return self.get("business_rules.price_category.premium_threshold", 500)

    @property
    def price_standard_threshold(self) -> float:
        """Get standard price threshold."""
        return self.get("business_rules.price_category.standard_threshold", 100)

    @property
    def max_null_percentage(self) -> float:
        """Get maximum allowed null percentage."""
        return self.get("data_quality.max_null_percentage", 5)

    @property
    def check_duplicates(self) -> bool:
        """Check if duplicate checking is enabled."""
        return self.get("data_quality.check_duplicates", True)

    @property
    def validate_negative_values(self) -> bool:
        """Check if negative value validation is enabled."""
        return self.get("data_quality.validate_negative_values", True)
