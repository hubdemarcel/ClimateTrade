#!/usr/bin/env python3
"""
Test Coverage Verification

This module verifies that test coverage meets the required thresholds
and provides detailed coverage analysis.
"""

import pytest
import coverage
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


class CoverageVerifier:
    """Verify test coverage requirements"""

    def __init__(self, coverage_threshold: float = 80.0):
        self.coverage_threshold = coverage_threshold
        self.coverage_data = {}

    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis and return results"""
        try:
            # Run pytest with coverage
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                '--cov=backtesting_framework',
                '--cov=data_pipeline',
                '--cov=scripts',
                '--cov-report=json',
                '--cov-report=term-missing',
                'tests/',
                'backtesting_framework/core/tests/',
                'backtesting_framework/data/tests/',
                'backtesting_framework/strategies/tests/',
                'analysis/tests/',
                'web/tests/',
                'data_pipeline/tests/',
                'scripts/tests/',
                'scripts/meteostat-python/tests/'
            ], capture_output=True, text=True, timeout=300)

            # Parse coverage results
            coverage_file = Path('coverage.json')
            if coverage_file.exists():
                import json
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)

                return self._analyze_coverage(coverage_data)
            else:
                return {
                    'success': False,
                    'error': 'Coverage file not found',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Coverage analysis timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Coverage analysis failed: {str(e)}'
            }

    def _analyze_coverage(self, coverage_data: Dict) -> Dict[str, Any]:
        """Analyze coverage data"""
        analysis = {
            'success': True,
            'overall_coverage': 0.0,
            'module_coverage': {},
            'missing_lines': {},
            'files_below_threshold': []
        }

        totals = coverage_data.get('totals', {})
        if 'percent_covered' in totals:
            analysis['overall_coverage'] = totals['percent_covered']

        # Analyze per-file coverage
        files = coverage_data.get('files', {})
        for file_path, file_data in files.items():
            if self._is_relevant_file(file_path):
                coverage_pct = file_data.get('summary', {}).get('percent_covered', 0)
                analysis['module_coverage'][file_path] = coverage_pct

                if coverage_pct < self.coverage_threshold:
                    analysis['files_below_threshold'].append({
                        'file': file_path,
                        'coverage': coverage_pct,
                        'missing_lines': file_data.get('missing_lines', [])
                    })

        # Check overall threshold
        if analysis['overall_coverage'] < self.coverage_threshold:
            analysis['success'] = False

        return analysis

    def _is_relevant_file(self, file_path: str) -> bool:
        """Check if file is relevant for coverage analysis"""
        # Exclude test files and non-source files
        exclude_patterns = [
            '/tests/',
            '/test_',
            '__pycache__',
            '.pytest_cache',
            'conftest.py'
        ]

        for pattern in exclude_patterns:
            if pattern in file_path:
                return False

        # Only include Python files in our source directories
        source_dirs = ['backtesting_framework', 'data_pipeline', 'scripts']
        return any(src_dir in file_path for src_dir in source_dirs) and file_path.endswith('.py')

    def generate_coverage_report(self, analysis: Dict) -> str:
        """Generate a detailed coverage report"""
        report = []
        report.append("=" * 60)
        report.append("TEST COVERAGE ANALYSIS REPORT")
        report.append("=" * 60)

        if analysis['success']:
            report.append(f"✅ OVERALL COVERAGE: {analysis['overall_coverage']:.1f}%")
            report.append(f"   Threshold: {self.coverage_threshold}%")
        else:
            report.append(f"❌ OVERALL COVERAGE: {analysis['overall_coverage']:.1f}%")
            report.append(f"   Threshold: {self.coverage_threshold}% - NOT MET")

        report.append("")

        # Module coverage
        if analysis['module_coverage']:
            report.append("MODULE COVERAGE:")
            for module, coverage_pct in sorted(analysis['module_coverage'].items()):
                status = "✅" if coverage_pct >= self.coverage_threshold else "❌"
                report.append(f"  {status} {module}: {coverage_pct:.1f}%")

        report.append("")

        # Files below threshold
        if analysis['files_below_threshold']:
            report.append("FILES BELOW THRESHOLD:")
            for file_info in analysis['files_below_threshold']:
                report.append(f"  ❌ {file_info['file']}: {file_info['coverage']:.1f}%")
                if file_info['missing_lines']:
                    report.append(f"     Missing lines: {file_info['missing_lines'][:10]}...")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


def test_coverage_threshold():
    """Test that coverage meets the required threshold"""
    verifier = CoverageVerifier(coverage_threshold=80.0)
    analysis = verifier.run_coverage_analysis()

    # Generate and print report
    report = verifier.generate_coverage_report(analysis)
    print(report)

    # Assert coverage requirements
    assert analysis['success'], f"Coverage threshold not met. See report above."

    # Additional assertions
    assert analysis['overall_coverage'] >= 80.0, f"Overall coverage {analysis['overall_coverage']:.1f}% below 80%"

    # Check that no critical files are below threshold
    critical_files = [f for f in analysis['files_below_threshold']
                     if any(critical in f['file'] for critical in ['engine', 'loader', 'strategy'])]

    assert len(critical_files) == 0, f"Critical files below threshold: {critical_files}"


def test_coverage_completeness():
    """Test that coverage analysis is complete"""
    verifier = CoverageVerifier()

    # Check that we have coverage data
    analysis = verifier.run_coverage_analysis()

    assert 'overall_coverage' in analysis
    assert 'module_coverage' in analysis
    assert isinstance(analysis['module_coverage'], dict)

    # Should have coverage data for our main modules
    modules_with_coverage = list(analysis['module_coverage'].keys())
    assert len(modules_with_coverage) > 0, "No modules found with coverage data"

    # Check for expected modules
    expected_modules = ['backtesting_framework', 'data_pipeline']
    found_expected = any(any(expected in module for expected in expected_modules)
                        for module in modules_with_coverage)
    assert found_expected, f"Expected modules not found in coverage: {expected_modules}"


def test_coverage_report_generation():
    """Test that coverage reports are generated properly"""
    verifier = CoverageVerifier()

    # Mock analysis data
    mock_analysis = {
        'success': True,
        'overall_coverage': 85.5,
        'module_coverage': {
            'backtesting_framework/core/backtesting_engine.py': 90.0,
            'backtesting_framework/data/data_loader.py': 85.0,
            'data_pipeline/data_validation.py': 80.0
        },
        'files_below_threshold': []
    }

    report = verifier.generate_coverage_report(mock_analysis)

    assert "OVERALL COVERAGE" in report
    assert "85.5%" in report
    assert "✅" in report  # Success indicator
    assert "backtesting_framework/core/backtesting_engine.py" in report


if __name__ == '__main__':
    # Run coverage verification
    print("Running test coverage verification...")

    try:
        test_coverage_threshold()
        print("✅ Coverage threshold test passed")
    except AssertionError as e:
        print(f"❌ Coverage threshold test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Coverage analysis failed: {e}")
        sys.exit(1)

    try:
        test_coverage_completeness()
        print("✅ Coverage completeness test passed")
    except Exception as e:
        print(f"❌ Coverage completeness test failed: {e}")
        sys.exit(1)

    try:
        test_coverage_report_generation()
        print("✅ Coverage report generation test passed")
    except Exception as e:
        print(f"❌ Coverage report generation test failed: {e}")
        sys.exit(1)

    print("\n🎉 All coverage verification tests passed!")