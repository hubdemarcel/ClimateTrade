#!/usr/bin/env python3
"""
Unit Tests for Analysis Notebooks

Basic validation tests for analysis notebooks to ensure they exist
and have proper structure. Since these are Jupyter notebooks, we test
their basic integrity and can extract/test any utility functions.
"""

import pytest
import json
import os
from pathlib import Path


class TestAnalysisNotebooks:
    """Test cases for analysis notebooks"""

    def test_notebook_files_exist(self):
        """Test that analysis notebook files exist"""
        notebook_dir = Path(__file__).parent.parent

        expected_notebooks = [
            "01_trend_detection_temperature_market_correlation.ipynb",
            "04_statistical_correlation_analysis.ipynb"
        ]

        for notebook in expected_notebooks:
            notebook_path = notebook_dir / notebook
            assert notebook_path.exists(), f"Notebook {notebook} does not exist"
            assert notebook_path.is_file(), f"{notebook} is not a file"

    def test_notebook_structure(self):
        """Test that notebooks have valid JSON structure"""
        notebook_dir = Path(__file__).parent.parent

        notebooks = [
            "01_trend_detection_temperature_market_correlation.ipynb",
            "04_statistical_correlation_analysis.ipynb"
        ]

        for notebook in notebooks:
            notebook_path = notebook_dir / notebook

            with open(notebook_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Should be valid JSON
            try:
                notebook_data = json.loads(content)
            except json.JSONDecodeError as e:
                pytest.fail(f"Notebook {notebook} is not valid JSON: {e}")

            # Should have notebook structure
            assert 'cells' in notebook_data, f"Notebook {notebook} missing cells"
            assert 'metadata' in notebook_data, f"Notebook {notebook} missing metadata"
            assert 'nbformat' in notebook_data, f"Notebook {notebook} missing nbformat"
            assert 'nbformat_minor' in notebook_data, f"Notebook {notebook} missing nbformat_minor"

            # Should have at least one cell
            assert len(notebook_data['cells']) > 0, f"Notebook {notebook} has no cells"

    def test_notebook_metadata(self):
        """Test notebook metadata structure"""
        notebook_dir = Path(__file__).parent.parent

        notebooks = [
            "01_trend_detection_temperature_market_correlation.ipynb",
            "04_statistical_correlation_analysis.ipynb"
        ]

        for notebook in notebooks:
            notebook_path = notebook_dir / notebook

            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)

            metadata = notebook_data.get('metadata', {})

            # Check for kernel information
            if 'kernelspec' in metadata:
                kernelspec = metadata['kernelspec']
                assert 'name' in kernelspec or 'display_name' in kernelspec, \
                    f"Notebook {notebook} missing kernel information"

    def test_notebook_cells(self):
        """Test notebook cells structure"""
        notebook_dir = Path(__file__).parent.parent

        notebooks = [
            "01_trend_detection_temperature_market_correlation.ipynb",
            "04_statistical_correlation_analysis.ipynb"
        ]

        for notebook in notebooks:
            notebook_path = notebook_dir / notebook

            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)

            cells = notebook_data['cells']

            for i, cell in enumerate(cells):
                assert 'cell_type' in cell, f"Cell {i} in {notebook} missing cell_type"
                assert cell['cell_type'] in ['code', 'markdown', 'raw'], \
                    f"Cell {i} in {notebook} has invalid cell_type: {cell['cell_type']}"

                if cell['cell_type'] == 'code':
                    assert 'source' in cell, f"Code cell {i} in {notebook} missing source"
                    assert 'outputs' in cell, f"Code cell {i} in {notebook} missing outputs"
                    assert 'execution_count' in cell, f"Code cell {i} in {notebook} missing execution_count"

                elif cell['cell_type'] == 'markdown':
                    assert 'source' in cell, f"Markdown cell {i} in {notebook} missing source"

    def test_notebook_has_code_cells(self):
        """Test that notebooks contain code cells for analysis"""
        notebook_dir = Path(__file__).parent.parent

        notebooks = [
            "01_trend_detection_temperature_market_correlation.ipynb",
            "04_statistical_correlation_analysis.ipynb"
        ]

        for notebook in notebooks:
            notebook_path = notebook_dir / notebook

            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)

            cells = notebook_data['cells']
            code_cells = [cell for cell in cells if cell['cell_type'] == 'code']

            assert len(code_cells) > 0, f"Notebook {notebook} has no code cells"

            # Check that code cells have actual code content
            has_code_content = False
            for cell in code_cells:
                source = cell.get('source', [])
                if source and any(line.strip() for line in source):
                    has_code_content = True
                    break

            assert has_code_content, f"Notebook {notebook} has no substantive code content"


class TestAnalysisUtilities:
    """Test cases for any utility functions that might be extracted from notebooks"""

    def test_placeholder_for_future_utilities(self):
        """Placeholder test for utility functions that may be extracted from notebooks"""
        # This test serves as a placeholder for when utility functions
        # are extracted from notebooks into separate modules

        # For now, just verify the analysis directory structure
        analysis_dir = Path(__file__).parent.parent
        assert analysis_dir.exists()
        assert analysis_dir.is_dir()

        # Check for expected notebook files
        notebooks = list(analysis_dir.glob("*.ipynb"))
        assert len(notebooks) >= 2, "Expected at least 2 notebook files in analysis directory"


if __name__ == '__main__':
    pytest.main([__file__])