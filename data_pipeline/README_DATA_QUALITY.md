# Data Quality Pipeline

This document describes the comprehensive data validation and cleaning system implemented for the ClimateTrade data pipeline. The system ensures data integrity, consistency, and quality for both Polymarket and weather data sources.

## Overview

The data quality pipeline consists of three main components:

1. **Data Validation** (`data_validation.py`) - Validates data integrity and format compliance
2. **Data Cleaning** (`data_cleaning.py`) - Handles missing values, normalization, and outlier detection
3. **Quality Pipeline** (`data_quality_pipeline.py`) - Orchestrates the complete data quality process

## Features

### Data Validation

- **Required Field Validation**: Ensures all mandatory fields are present
- **Data Type Validation**: Validates field types and formats
- **Range Validation**: Checks numeric values against realistic ranges
- **Timestamp Validation**: Validates and normalizes timestamp formats
- **Cross-field Consistency**: Validates relationships between related fields

### Data Cleaning

- **Missing Value Handling**: Multiple strategies (drop, mean, median, forward/backward fill, interpolate)
- **Outlier Detection**: IQR, Z-score, and percentile-based methods
- **Data Normalization**: Standardizes formats, timestamps, and numeric values
- **Text Normalization**: Cleans and standardizes text fields

### Quality Pipeline

- **Automated Processing**: End-to-end data quality workflow
- **Configurable Rules**: Customizable validation and cleaning rules
- **Quality Scoring**: Comprehensive quality metrics and scoring
- **Reporting**: Detailed quality reports and statistics

## Usage

### Basic Usage

```python
from data_quality_pipeline import process_polymarket_data, process_weather_data

# Process Polymarket data
polymarket_result = process_polymarket_data(your_polymarket_data)

# Process weather data
weather_result = process_weather_data(your_weather_data)

# Check results
if polymarket_result['success']:
    print(f"Quality Score: {polymarket_result['quality_score']}%")
    cleaned_data = polymarket_result['cleaned_data']
```

### Advanced Configuration

```python
from data_quality_pipeline import DataQualityPipeline, DataSource

# Create custom pipeline configuration
config = {
    'fail_on_validation_error': False,
    'fail_on_cleaning_error': False,
    'generate_reports': True,
    'quality_threshold': 80.0,
    'cleaning_config': {
        'handle_missing': True,
        'missing_strategy': 'interpolate',
        'detect_outliers': True,
        'outlier_method': 'zscore',
        'remove_outliers': False
    }
}

# Create and use pipeline
pipeline = DataQualityPipeline(DataSource.WEATHER, config)
result = pipeline.process_data(weather_data)
```

### Integration with Ingestion Scripts

The data quality pipeline is automatically integrated with the existing ingestion scripts:

```bash
# Polymarket ingestion with quality pipeline (default enabled)
python data_pipeline/ingest_polymarket.py data/polymarket_data.csv

# Weather ingestion with quality pipeline
python data_pipeline/ingest_weather.py sample_weather.json --source met_office --location "London, UK"

# Disable quality pipeline if needed
python data_pipeline/ingest_polymarket.py data/polymarket_data.csv --disable-quality-pipeline

# Use custom quality configuration
python data_pipeline/ingest_polymarket.py data/polymarket_data.csv --quality-config quality_config.json
```

## Configuration Options

### Pipeline Configuration

```json
{
  "fail_on_validation_error": false,
  "fail_on_cleaning_error": false,
  "generate_reports": true,
  "report_format": "json",
  "quality_threshold": 80.0,
  "save_reports": false,
  "report_dir": "reports",
  "cleaning_config": {
    "handle_missing": true,
    "missing_strategy": "mean",
    "missing_fields": ["probability", "volume"],
    "detect_outliers": true,
    "outlier_method": "iqr",
    "outlier_fields": ["probability", "volume"],
    "remove_outliers": false
  }
}
```

### Validation Rules

#### Polymarket Data Validation

- **Required Fields**: `event_title`, `market_id`, `outcome_name`, `timestamp`, `scraped_at`
- **Probability Range**: 0.0 - 1.0
- **Volume Range**: ≥ 0.0
- **Timestamp Format**: ISO 8601 UTC
- **Market ID Format**: Alphanumeric with hyphens

#### Weather Data Validation

- **Required Fields**: `location_name`, `timestamp`
- **Latitude Range**: -90.0 - 90.0
- **Longitude Range**: -180.0 - 180.0
- **Temperature Range**: -100.0°C - 60.0°C
- **Humidity Range**: 0.0% - 100.0%
- **Pressure Range**: 800.0 hPa - 1200.0 hPa
- **Wind Speed Range**: 0.0 m/s - 150.0 m/s

### Cleaning Strategies

#### Missing Value Handling

- **drop**: Remove records with missing values
- **mean**: Fill with field mean
- **median**: Fill with field median
- **mode**: Fill with most frequent value
- **forward_fill**: Use last known value
- **backward_fill**: Use next known value
- **interpolate**: Linear interpolation
- **constant**: Fill with specified constant

#### Outlier Detection Methods

- **iqr**: Interquartile Range (default multiplier: 1.5)
- **zscore**: Z-score method (default threshold: 3.0)
- **percentile**: Percentile method (default: 5th-95th percentile)

## Quality Metrics

The pipeline generates comprehensive quality metrics:

- **Completeness Score**: Percentage of non-null values
- **Consistency Score**: Data type consistency across records
- **Accuracy Score**: Realistic value ranges and relationships
- **Timeliness Score**: Data freshness and temporal consistency
- **Overall Quality Score**: Weighted combination of all metrics

## Output and Reporting

### Processing Results

```python
{
  "success": true,
  "source": "polymarket",
  "original_records": 1000,
  "processed_records": 950,
  "quality_score": 87.5,
  "processing_time": 2.34,
  "pipeline_stages": ["validation", "cleaning", "quality_check", "reporting"],
  "validation_result": {
    "total_records": 1000,
    "valid_records": 980,
    "invalid_records": 20,
    "results": [...]
  },
  "cleaning_result": {
    "original_count": 980,
    "cleaned_count": 950,
    "cleaning_steps": ["format_normalization", "missing_values_mean"],
    "config": {...}
  },
  "quality_result": {
    "completeness_score": 92.3,
    "consistency_score": 98.1,
    "accuracy_score": 89.7,
    "timeliness_score": 95.2,
    "overall_quality_score": 93.8
  },
  "cleaned_data": [...]
}
```

### Quality Reports

Quality reports are automatically generated and can be saved to files:

```python
# Access latest report
report = pipeline.get_latest_report()
print(f"Quality Score: {report.quality_score}%")
print(f"Processing Time: {report.processing_time}s")

# Save report to file
with open('quality_report.json', 'w') as f:
    f.write(report.to_json())
```

## Error Handling

The pipeline includes comprehensive error handling:

- **Validation Errors**: Data that fails validation rules
- **Cleaning Errors**: Issues during data cleaning operations
- **Processing Errors**: Pipeline execution failures
- **Configuration Errors**: Invalid configuration parameters

Errors are logged with detailed information and don't stop processing unless configured to do so.

## Testing

Comprehensive unit tests are provided in `test_data_quality.py`:

```bash
# Run all tests
python -m pytest data_pipeline/test_data_quality.py -v

# Run specific test class
python -m pytest data_pipeline/test_data_quality.py::TestPolymarketDataValidator -v

# Run with coverage
python -m pytest data_pipeline/test_data_quality.py --cov=data_quality_pipeline
```

## Performance Considerations

- **Batch Processing**: Efficiently handles large datasets
- **Memory Management**: Processes data in chunks for large files
- **Caching**: Reuses computed values where possible
- **Parallel Processing**: Can be extended for parallel execution

## Integration Points

The data quality system integrates with:

- **Database Layer**: Validates data before insertion
- **API Endpoints**: Ensures incoming data quality
- **ETL Processes**: Quality gates in data pipelines
- **Monitoring Systems**: Quality metrics and alerts
- **Reporting Systems**: Quality dashboards and reports

## Best Practices

1. **Configure Appropriate Thresholds**: Set quality thresholds based on your use case
2. **Monitor Quality Metrics**: Track quality trends over time
3. **Handle Edge Cases**: Test with various data scenarios
4. **Version Configuration**: Keep quality rules versioned with your data schema
5. **Log Quality Issues**: Maintain detailed logs for troubleshooting
6. **Regular Validation**: Run quality checks on regular intervals

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all modules are in the Python path
2. **Configuration Errors**: Validate JSON configuration files
3. **Memory Issues**: Process large files in smaller chunks
4. **Performance Issues**: Adjust batch sizes and processing parameters

### Debug Mode

Enable debug logging for detailed processing information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Process with debug output
result = process_polymarket_data(data)
```

## Future Enhancements

- **Machine Learning Integration**: ML-based anomaly detection
- **Real-time Processing**: Streaming data quality validation
- **Custom Rules Engine**: User-defined validation rules
- **Quality Dashboards**: Web-based quality monitoring
- **Automated Remediation**: Self-healing data quality issues

## Support

For issues or questions about the data quality pipeline:

1. Check the test suite for examples
2. Review the configuration documentation
3. Examine the logs for detailed error information
4. Refer to the integration examples in the ingestion scripts
