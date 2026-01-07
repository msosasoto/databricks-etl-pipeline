"""
Data quality validation module.

Implements data quality checks and validations.
"""

from typing import Dict, Any, List
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import logging

from src.config.settings import Config

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Custom exception for data quality errors."""
    pass


class DataQualityValidator:
    """Handles data quality validation checks."""

    def __init__(self, config: Config):
        """
        Initialize DataQualityValidator.

        Args:
            config: Configuration object.
        """
        self.config = config
        logger.info("DataQualityValidator initialized")

    def validate(self, df: DataFrame) -> Dict[str, Any]:
        """
        Run all data quality validations.

        Args:
            df: DataFrame to validate.

        Returns:
            Dictionary containing validation results.

        Raises:
            DataQualityError: If critical validations fail.

        Example:
            >>> validator = DataQualityValidator(config)
            >>> report = validator.validate(df)
            >>> print(report['summary'])
        """
        logger.info("Starting data quality validation")
        
        report = {
            "timestamp": F.current_timestamp(),
            "total_records": df.count(),
            "checks": {}
        }
        
        try:
            # Run all checks
            report["checks"]["null_check"] = self._check_nulls(df)
            report["checks"]["negative_values"] = self._check_negative_values(df)
            report["checks"]["duplicates"] = self._check_duplicates(df)
            report["checks"]["date_range"] = self._check_date_range(df)
            
            # Determine overall status
            failed_checks = [
                name for name, result in report["checks"].items()
                if not result.get("passed", True)
            ]
            
            report["summary"] = {
                "total_checks": len(report["checks"]),
                "passed_checks": len(report["checks"]) - len(failed_checks),
                "failed_checks": len(failed_checks),
                "status": "PASSED" if not failed_checks else "FAILED"
            }
            
            logger.info(f"Validation completed: {report['summary']['status']}")
            
            # Raise error if critical checks failed
            if failed_checks and self._has_critical_failures(report["checks"]):
                raise DataQualityError(
                    f"Critical data quality checks failed: {failed_checks}"
                )
            
            return report
            
        except DataQualityError:
            raise
        except Exception as e:
            error_msg = f"Validation failed with error: {str(e)}"
            logger.error(error_msg)
            raise DataQualityError(error_msg) from e

    def _check_nulls(self, df: DataFrame) -> Dict[str, Any]:
        """
        Check for null values in critical columns.

        Args:
            df: DataFrame to check.

        Returns:
            Dictionary with null check results.
        """
        logger.debug("Checking for null values")
        
        total_rows = df.count()
        null_counts = {}
        
        for column in df.columns:
            null_count = df.filter(F.col(column).isNull()).count()
            null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
            null_counts[column] = {
                "count": null_count,
                "percentage": round(null_percentage, 2)
            }
        
        # Check if null percentage exceeds threshold
        max_null_pct = self.config.max_null_percentage
        violations = {
            col: data for col, data in null_counts.items()
            if data["percentage"] > max_null_pct
        }
        
        passed = len(violations) == 0
        
        result = {
            "passed": passed,
            "null_counts": null_counts,
            "violations": violations,
            "threshold": max_null_pct
        }
        
        if not passed:
            logger.warning(f"Null check failed: {len(violations)} columns exceed threshold")
        else:
            logger.debug("Null check passed")
        
        return result

    def _check_negative_values(self, df: DataFrame) -> Dict[str, Any]:
        """
        Check for negative values in numeric columns.

        Args:
            df: DataFrame to check.

        Returns:
            Dictionary with negative value check results.
        """
        if not self.config.validate_negative_values:
            return {"passed": True, "skipped": True}
        
        logger.debug("Checking for negative values")
        
        columns_to_check = ["price", "quantity"]
        violations = {}
        
        for column in columns_to_check:
            if column in df.columns:
                negative_count = df.filter(F.col(column) < 0).count()
                if negative_count > 0:
                    violations[column] = negative_count
        
        passed = len(violations) == 0
        
        result = {
            "passed": passed,
            "violations": violations,
            "checked_columns": columns_to_check
        }
        
        if not passed:
            logger.warning(f"Negative value check failed: {violations}")
        else:
            logger.debug("Negative value check passed")
        
        return result

    def _check_duplicates(self, df: DataFrame) -> Dict[str, Any]:
        """
        Check for duplicate order IDs.

        Args:
            df: DataFrame to check.

        Returns:
            Dictionary with duplicate check results.
        """
        if not self.config.check_duplicates:
            return {"passed": True, "skipped": True}
        
        logger.debug("Checking for duplicates")
        
        if "order_id" not in df.columns:
            return {"passed": True, "skipped": True, "reason": "order_id column not found"}
        
        total_records = df.count()
        distinct_records = df.select("order_id").distinct().count()
        duplicate_count = total_records - distinct_records
        
        passed = duplicate_count == 0
        
        result = {
            "passed": passed,
            "total_records": total_records,
            "distinct_records": distinct_records,
            "duplicate_count": duplicate_count
        }
        
        if not passed:
            logger.warning(f"Duplicate check failed: {duplicate_count} duplicates found")
        else:
            logger.debug("Duplicate check passed")
        
        return result

    def _check_date_range(self, df: DataFrame) -> Dict[str, Any]:
        """
        Check if dates are within valid range.

        Args:
            df: DataFrame to check.

        Returns:
            Dictionary with date range check results.
        """
        logger.debug("Checking date ranges")
        
        if "order_date" not in df.columns:
            return {"passed": True, "skipped": True, "reason": "order_date column not found"}
        
        # Get min and max dates
        date_stats = df.select(
            F.min("order_date").alias("min_date"),
            F.max("order_date").alias("max_date")
        ).collect()[0]
        
        min_date = date_stats["min_date"]
        max_date = date_stats["max_date"]
        
        # Check for future dates
        future_dates = df.filter(F.col("order_date") > F.current_date()).count()
        
        passed = future_dates == 0
        
        result = {
            "passed": passed,
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None,
            "future_dates_count": future_dates
        }
        
        if not passed:
            logger.warning(f"Date range check failed: {future_dates} future dates found")
        else:
            logger.debug("Date range check passed")
        
        return result

    def _has_critical_failures(self, checks: Dict[str, Any]) -> bool:
        """
        Determine if any critical checks failed.

        Args:
            checks: Dictionary of check results.

        Returns:
            True if critical checks failed.
        """
        critical_checks = ["negative_values", "duplicates"]
        
        for check_name in critical_checks:
            if check_name in checks and not checks[check_name].get("passed", True):
                return True
        
        return False

    def generate_quality_report(self, report: Dict[str, Any]) -> List[str]:
        """
        Generate human-readable quality report.

        Args:
            report: Validation report dictionary.

        Returns:
            List of report lines.

        Example:
            >>> validator = DataQualityValidator(config)
            >>> report = validator.validate(df)
            >>> lines = validator.generate_quality_report(report)
            >>> for line in lines:
            ...     print(line)
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DATA QUALITY REPORT")
        lines.append("=" * 60)
        lines.append(f"Total Records: {report['total_records']}")
        lines.append(f"Status: {report['summary']['status']}")
        lines.append(f"Checks Passed: {report['summary']['passed_checks']}/{report['summary']['total_checks']}")
        lines.append("")
        
        for check_name, check_result in report["checks"].items():
            status = "✓ PASSED" if check_result.get("passed", True) else "✗ FAILED"
            lines.append(f"{check_name.upper()}: {status}")
            
            if not check_result.get("passed", True) and "violations" in check_result:
                lines.append(f"  Violations: {check_result['violations']}")
        
        lines.append("=" * 60)
        return lines
