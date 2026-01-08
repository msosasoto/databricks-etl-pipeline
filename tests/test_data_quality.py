"""
Unit tests for data quality validation module.
"""

import pytest
from pyspark.sql import functions as F

from src.validation.data_quality import DataQualityValidator, DataQualityError


class TestDataQualityValidator:
    """Test suite for DataQualityValidator."""

    def test_validate_clean_data_passes(self, config, sample_sales_data):
        """Test that clean data passes all validations."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)

        assert report["summary"]["status"] == "PASSED"
        assert report["summary"]["failed_checks"] == 0
        assert report["total_records"] == sample_sales_data.count()

    def test_check_nulls_with_clean_data(self, config, sample_sales_data):
        """Test null check with clean data."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)
        null_check = report["checks"]["null_check"]

        assert null_check["passed"] is True
        assert len(null_check["violations"]) == 0

    def test_check_nulls_with_null_data(self, config, sample_data_with_nulls):
        """Test null check with data containing nulls."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_data_with_nulls)
        null_check = report["checks"]["null_check"]

        # Check that nulls were detected
        assert "customer_id" in null_check["null_counts"]
        assert null_check["null_counts"]["customer_id"]["count"] > 0

    def test_check_negative_values_clean_data(self, config, sample_sales_data):
        """Test negative value check with clean data."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)
        negative_check = report["checks"]["negative_values"]

        assert negative_check["passed"] is True
        assert len(negative_check["violations"]) == 0

    def test_check_negative_values_with_negatives(self, config, sample_data_with_negatives):
        """Test negative value check with negative values."""
        validator = DataQualityValidator(config)

        # This should raise an error because negative values are critical
        with pytest.raises(DataQualityError) as exc_info:
            validator.validate(sample_data_with_negatives)

        assert "Critical data quality checks failed" in str(exc_info.value)

    def test_negative_values_detection_details(self, config, sample_data_with_negatives):
        """Test that negative values are properly detected."""
        validator = DataQualityValidator(config)

        try:
            report = validator.validate(sample_data_with_negatives)
        except DataQualityError:
            # Expected, but we want to check the report structure
            pass

        # Run the check directly to inspect results
        negative_check = validator._check_negative_values(sample_data_with_negatives)

        assert negative_check["passed"] is False
        assert len(negative_check["violations"]) > 0
        # Should detect negatives in quantity or price
        assert "quantity" in negative_check["violations"] or "price" in negative_check["violations"]

    def test_check_duplicates_clean_data(self, config, sample_sales_data):
        """Test duplicate check with clean data."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)
        duplicate_check = report["checks"]["duplicates"]

        assert duplicate_check["passed"] is True
        assert duplicate_check["duplicate_count"] == 0

    def test_check_duplicates_with_duplicates(self, config, sample_data_with_duplicates):
        """Test duplicate check with duplicate order IDs."""
        validator = DataQualityValidator(config)

        # This should raise an error because duplicates are critical
        with pytest.raises(DataQualityError) as exc_info:
            validator.validate(sample_data_with_duplicates)

        assert "Critical data quality checks failed" in str(exc_info.value)

    def test_duplicates_detection_details(self, config, sample_data_with_duplicates):
        """Test that duplicates are properly detected."""
        validator = DataQualityValidator(config)

        duplicate_check = validator._check_duplicates(sample_data_with_duplicates)

        assert duplicate_check["passed"] is False
        assert duplicate_check["duplicate_count"] == 1  # One duplicate order_id
        assert duplicate_check["total_records"] == 3
        assert duplicate_check["distinct_records"] == 2

    def test_check_date_range_valid(self, config, sample_sales_data):
        """Test date range check with valid dates."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)
        date_check = report["checks"]["date_range"]

        assert date_check["passed"] is True
        assert date_check["future_dates_count"] == 0
        assert date_check["min_date"] is not None
        assert date_check["max_date"] is not None

    def test_generate_quality_report(self, config, sample_sales_data):
        """Test quality report generation."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)
        report_lines = validator.generate_quality_report(report)

        assert len(report_lines) > 0
        assert any("DATA QUALITY REPORT" in line for line in report_lines)
        assert any("PASSED" in line for line in report_lines)

    def test_validation_report_structure(self, config, sample_sales_data):
        """Test that validation report has expected structure."""
        validator = DataQualityValidator(config)

        report = validator.validate(sample_sales_data)

        # Check top-level keys
        assert "timestamp" in report
        assert "total_records" in report
        assert "checks" in report
        assert "summary" in report

        # Check summary structure
        assert "total_checks" in report["summary"]
        assert "passed_checks" in report["summary"]
        assert "failed_checks" in report["summary"]
        assert "status" in report["summary"]

        # Check that all expected checks are present
        expected_checks = ["null_check", "negative_values", "duplicates", "date_range"]
        for check in expected_checks:
            assert check in report["checks"]

    def test_validation_with_disabled_checks(self, config, sample_data_with_duplicates):
        """Test validation when certain checks are disabled in config."""
        # Modify config to disable duplicate checking
        config._config["data_quality"]["check_duplicates"] = False

        validator = DataQualityValidator(config)

        # Should not raise error even with duplicates
        report = validator.validate(sample_data_with_duplicates)

        # Duplicate check should be skipped
        assert report["checks"]["duplicates"].get("skipped", False) is True

    def test_has_critical_failures(self, config):
        """Test critical failure detection."""
        validator = DataQualityValidator(config)

        # Test with critical failures
        checks_with_failures = {
            "null_check": {"passed": True},
            "negative_values": {"passed": False},
            "duplicates": {"passed": True},
            "date_range": {"passed": True},
        }

        assert validator._has_critical_failures(checks_with_failures) is True

        # Test without critical failures
        checks_without_failures = {
            "null_check": {"passed": False},  # Not critical
            "negative_values": {"passed": True},
            "duplicates": {"passed": True},
            "date_range": {"passed": True},
        }

        assert validator._has_critical_failures(checks_without_failures) is False

    def test_null_percentage_calculation(self, config, sample_data_with_nulls):
        """Test that null percentages are calculated correctly."""
        validator = DataQualityValidator(config)

        null_check = validator._check_nulls(sample_data_with_nulls)

        total_rows = sample_data_with_nulls.count()

        # Verify percentage calculation
        for column, data in null_check["null_counts"].items():
            expected_pct = (data["count"] / total_rows * 100) if total_rows > 0 else 0
            assert abs(data["percentage"] - expected_pct) < 0.01
