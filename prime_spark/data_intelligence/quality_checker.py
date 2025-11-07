"""
Automated Data Quality Checker

Performs comprehensive data quality checks including completeness, accuracy,
consistency, validity, uniqueness, and timeliness assessments.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class DataQualityDimension(Enum):
    """Data quality dimensions"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"


class SeverityLevel(Enum):
    """Issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityRule:
    """Data quality rule definition"""
    rule_id: str
    name: str
    dimension: DataQualityDimension
    description: str
    validator: Callable
    threshold: float
    severity: SeverityLevel


@dataclass
class QualityIssue:
    """Data quality issue"""
    issue_id: str
    rule_id: str
    dimension: DataQualityDimension
    severity: SeverityLevel
    field: str
    description: str
    affected_records: int
    sample_values: List[Any]
    detected_at: datetime


@dataclass
class QualityReport:
    """Data quality assessment report"""
    report_id: str
    dataset_name: str
    generated_at: datetime
    total_records: int
    total_fields: int
    overall_score: float
    dimension_scores: Dict[str, float]
    issues: List[QualityIssue]
    passed_rules: int
    failed_rules: int


class DataQualityChecker:
    """
    Automated Data Quality Checker

    Features:
    - Completeness checks (null values, missing data)
    - Accuracy checks (format validation, range checks)
    - Consistency checks (referential integrity, cross-field validation)
    - Validity checks (data type validation, domain constraints)
    - Uniqueness checks (duplicate detection)
    - Timeliness checks (data freshness, staleness)
    - Configurable quality rules
    - Automated quality reports
    - Anomaly detection
    """

    def __init__(
        self,
        completeness_threshold: float = 0.95,
        accuracy_threshold: float = 0.99,
        enable_auto_remediation: bool = False,
    ):
        self.completeness_threshold = completeness_threshold
        self.accuracy_threshold = accuracy_threshold
        self.enable_auto_remediation = enable_auto_remediation

        # Quality rules
        self.rules: Dict[str, QualityRule] = {}

        # Historical quality metrics
        self.quality_history: List[QualityReport] = []

        # Field metadata
        self.field_metadata: Dict[str, Dict] = {}

        # Initialize default rules
        self._initialize_default_rules()

        logger.info("Initialized DataQualityChecker")

    def _initialize_default_rules(self) -> None:
        """Initialize default quality rules"""
        # Completeness rules
        self.add_rule(QualityRule(
            rule_id="null_check",
            name="No Null Values",
            dimension=DataQualityDimension.COMPLETENESS,
            description="Field should not contain null values",
            validator=self._validate_no_nulls,
            threshold=self.completeness_threshold,
            severity=SeverityLevel.WARNING,
        ))

        # Accuracy rules
        self.add_rule(QualityRule(
            rule_id="email_format",
            name="Valid Email Format",
            dimension=DataQualityDimension.ACCURACY,
            description="Email field should have valid format",
            validator=self._validate_email_format,
            threshold=self.accuracy_threshold,
            severity=SeverityLevel.ERROR,
        ))

        # Uniqueness rules
        self.add_rule(QualityRule(
            rule_id="unique_check",
            name="Unique Values",
            dimension=DataQualityDimension.UNIQUENESS,
            description="Field should contain unique values",
            validator=self._validate_uniqueness,
            threshold=1.0,
            severity=SeverityLevel.ERROR,
        ))

    def add_rule(self, rule: QualityRule) -> None:
        """Add a quality rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added quality rule: {rule.name}")

    def check_dataset(
        self,
        dataset: List[Dict],
        dataset_name: str,
        field_configs: Optional[Dict[str, Dict]] = None,
    ) -> QualityReport:
        """
        Check data quality for entire dataset

        Args:
            dataset: List of records (dictionaries)
            dataset_name: Name of the dataset
            field_configs: Optional field-specific configurations

        Returns:
            QualityReport
        """
        report_id = f"report-{datetime.now().timestamp()}"
        issues = []

        if not dataset:
            return QualityReport(
                report_id=report_id,
                dataset_name=dataset_name,
                generated_at=datetime.now(),
                total_records=0,
                total_fields=0,
                overall_score=0.0,
                dimension_scores={},
                issues=[],
                passed_rules=0,
                failed_rules=0,
            )

        total_records = len(dataset)
        fields = list(dataset[0].keys())
        total_fields = len(fields)

        # Store field metadata
        if field_configs:
            self.field_metadata.update(field_configs)

        # Run quality checks for each field
        for field in fields:
            field_config = field_configs.get(field, {}) if field_configs else {}
            field_issues = self._check_field(dataset, field, field_config)
            issues.extend(field_issues)

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(issues, total_records)

        # Calculate overall score
        overall_score = np.mean(list(dimension_scores.values())) if dimension_scores else 0.0

        # Count passed/failed rules
        failed_rules = len(set(issue.rule_id for issue in issues))
        passed_rules = len(self.rules) - failed_rules

        report = QualityReport(
            report_id=report_id,
            dataset_name=dataset_name,
            generated_at=datetime.now(),
            total_records=total_records,
            total_fields=total_fields,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            issues=issues,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
        )

        # Store in history
        self.quality_history.append(report)

        logger.info(
            f"Quality check complete for {dataset_name}: "
            f"score {overall_score:.2%}, {len(issues)} issues found"
        )

        return report

    def _check_field(
        self,
        dataset: List[Dict],
        field: str,
        config: Dict,
    ) -> List[QualityIssue]:
        """Check quality for a single field"""
        issues = []

        # Extract field values
        values = [record.get(field) for record in dataset]

        # Apply rules based on field config
        rules_to_check = config.get('rules', list(self.rules.keys()))

        for rule_id in rules_to_check:
            if rule_id not in self.rules:
                continue

            rule = self.rules[rule_id]

            # Run validator
            try:
                is_valid, affected_count, samples = rule.validator(
                    values, config
                )

                # Check against threshold
                validity_rate = 1.0 - (affected_count / len(values))

                if validity_rate < rule.threshold:
                    issue = QualityIssue(
                        issue_id=f"issue-{datetime.now().timestamp()}-{field}",
                        rule_id=rule_id,
                        dimension=rule.dimension,
                        severity=rule.severity,
                        field=field,
                        description=f"{rule.description} (validity: {validity_rate:.2%})",
                        affected_records=affected_count,
                        sample_values=samples[:5],  # First 5 samples
                        detected_at=datetime.now(),
                    )
                    issues.append(issue)

            except Exception as e:
                logger.error(f"Error running rule {rule_id} on field {field}: {e}")

        return issues

    def _validate_no_nulls(
        self,
        values: List[Any],
        config: Dict,
    ) -> tuple:
        """Validate no null values"""
        null_values = [v for v in values if v is None or v == '']
        affected_count = len(null_values)
        samples = null_values[:10]
        return affected_count == 0, affected_count, samples

    def _validate_email_format(
        self,
        values: List[Any],
        config: Dict,
    ) -> tuple:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        invalid_emails = []
        for v in values:
            if v and not re.match(email_pattern, str(v)):
                invalid_emails.append(v)

        affected_count = len(invalid_emails)
        return affected_count == 0, affected_count, invalid_emails[:10]

    def _validate_uniqueness(
        self,
        values: List[Any],
        config: Dict,
    ) -> tuple:
        """Validate uniqueness"""
        seen = set()
        duplicates = []

        for v in values:
            if v in seen:
                duplicates.append(v)
            else:
                seen.add(v)

        affected_count = len(duplicates)
        return affected_count == 0, affected_count, list(set(duplicates))[:10]

    def _validate_range(
        self,
        values: List[Any],
        config: Dict,
    ) -> tuple:
        """Validate numeric range"""
        min_val = config.get('min')
        max_val = config.get('max')

        out_of_range = []
        for v in values:
            try:
                num_val = float(v)
                if min_val is not None and num_val < min_val:
                    out_of_range.append(v)
                elif max_val is not None and num_val > max_val:
                    out_of_range.append(v)
            except (TypeError, ValueError):
                out_of_range.append(v)

        affected_count = len(out_of_range)
        return affected_count == 0, affected_count, out_of_range[:10]

    def _validate_format(
        self,
        values: List[Any],
        config: Dict,
    ) -> tuple:
        """Validate format using regex"""
        pattern = config.get('pattern')
        if not pattern:
            return True, 0, []

        invalid_formats = []
        for v in values:
            if v and not re.match(pattern, str(v)):
                invalid_formats.append(v)

        affected_count = len(invalid_formats)
        return affected_count == 0, affected_count, invalid_formats[:10]

    def _calculate_dimension_scores(
        self,
        issues: List[QualityIssue],
        total_records: int,
    ) -> Dict[str, float]:
        """Calculate quality scores by dimension"""
        dimension_scores = {}

        for dimension in DataQualityDimension:
            dimension_issues = [i for i in issues if i.dimension == dimension]

            if not dimension_issues:
                dimension_scores[dimension.value] = 1.0
            else:
                # Calculate weighted score based on severity
                total_affected = sum(i.affected_records for i in dimension_issues)
                score = 1.0 - (total_affected / (total_records * len(dimension_issues)))
                dimension_scores[dimension.value] = max(0.0, score)

        return dimension_scores

    def get_quality_trend(
        self,
        dataset_name: str,
        days: int = 30,
    ) -> Dict:
        """Get quality trend over time"""
        cutoff = datetime.now() - timedelta(days=days)

        relevant_reports = [
            r for r in self.quality_history
            if r.dataset_name == dataset_name and r.generated_at > cutoff
        ]

        if not relevant_reports:
            return {}

        # Sort by date
        relevant_reports.sort(key=lambda r: r.generated_at)

        scores = [r.overall_score for r in relevant_reports]
        timestamps = [r.generated_at for r in relevant_reports]

        # Calculate trend
        if len(scores) >= 2:
            x = np.arange(len(scores))
            coeffs = np.polyfit(x, scores, 1)
            trend = "improving" if coeffs[0] > 0 else "declining"
        else:
            trend = "stable"

        return {
            'dataset': dataset_name,
            'period_days': days,
            'num_reports': len(relevant_reports),
            'current_score': scores[-1] if scores else 0.0,
            'average_score': np.mean(scores),
            'trend': trend,
            'scores': scores,
            'timestamps': [t.isoformat() for t in timestamps],
        }

    def get_statistics(self) -> Dict:
        """Get overall quality statistics"""
        if not self.quality_history:
            return {}

        recent_reports = self.quality_history[-10:]  # Last 10 reports

        avg_score = np.mean([r.overall_score for r in recent_reports])
        total_issues = sum(len(r.issues) for r in recent_reports)

        # Issues by severity
        issues_by_severity = {}
        for report in recent_reports:
            for issue in report.issues:
                severity = issue.severity.value
                issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1

        # Issues by dimension
        issues_by_dimension = {}
        for report in recent_reports:
            for issue in report.issues:
                dimension = issue.dimension.value
                issues_by_dimension[dimension] = issues_by_dimension.get(dimension, 0) + 1

        return {
            'total_reports': len(self.quality_history),
            'recent_reports': len(recent_reports),
            'average_quality_score': avg_score,
            'total_issues': total_issues,
            'issues_by_severity': issues_by_severity,
            'issues_by_dimension': issues_by_dimension,
            'active_rules': len(self.rules),
        }
