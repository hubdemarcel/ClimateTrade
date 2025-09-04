#!/usr/bin/env python3
"""
Weather2Geo Automated Processing Pipeline

This script provides automated processing capabilities for Weather2Geo
data extraction, including scheduled runs, batch processing, and
integration with the ClimateTrade data pipeline.

Features:
- Scheduled automated data extraction
- Batch processing for multiple time periods
- Data quality monitoring and alerting
- Integration with existing data pipeline
- Comprehensive logging and reporting
- Configurable processing parameters
"""

import os
import json
import sys
import argparse
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add Weather2Geo to path
sys.path.append(str(Path(__file__).parent / "Weather2Geo"))

try:
    from weather2geo_client import Weather2GeoClient
except ImportError as e:
    print(f"Error importing Weather2Geo client: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather2geo_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedPipeline:
    """Automated processing pipeline for Weather2Geo data extraction."""

    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.client = Weather2GeoClient(
            cities_file=self.config.get('cities_file', '../data/cities15000.txt'),
            max_workers=self.config.get('max_workers', 50)
        )
        self.output_dir = Path(self.config.get('output_dir', 'data/weather2geo_output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.output_dir / 'pipeline_stats.json'
        self.load_stats()

    def load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'cities_file': '../data/cities15000.txt',
            'max_workers': 50,
            'output_dir': 'data/weather2geo_output',
            'extraction_modes': ['bulk', 'conditions'],
            'schedule_interval_hours': 6,
            'batch_size': 10,
            'max_locations': 500,
            'enable_enrichment': True,
            'auto_ingest': True,
            'ingest_script': 'data_pipeline/ingest_weather.py',
            'db_path': 'data/climatetrade.db',
            'quality_threshold': 80.0,
            'alerts': {
                'enable_email': False,
                'email_recipient': '',
                'email_sender': '',
                'smtp_server': '',
                'smtp_port': 587,
                'alert_on_failure': True,
                'alert_on_low_quality': True
            },
            'retention_days': 30,
            'log_level': 'INFO'
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                default_config.update(file_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        return default_config

    def load_stats(self):
        """Load pipeline statistics."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
                self.stats = self.get_default_stats()
        else:
            self.stats = self.get_default_stats()

    def get_default_stats(self) -> Dict:
        """Get default statistics structure."""
        return {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_records': 0,
            'last_run': None,
            'average_duration': 0,
            'quality_scores': [],
            'run_history': []
        }

    def save_stats(self):
        """Save pipeline statistics."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    def update_stats(self, run_result: Dict):
        """Update pipeline statistics with run results."""
        self.stats['total_runs'] += 1

        if run_result['success']:
            self.stats['successful_runs'] += 1
        else:
            self.stats['failed_runs'] += 1

        self.stats['total_records'] += run_result.get('records', 0)
        self.stats['last_run'] = datetime.now().isoformat()

        # Update average duration
        if 'duration' in run_result:
            current_avg = self.stats['average_duration']
            total_runs = self.stats['total_runs']
            self.stats['average_duration'] = (current_avg * (total_runs - 1) + run_result['duration']) / total_runs

        # Update quality scores
        if 'quality_score' in run_result:
            self.stats['quality_scores'].append(run_result['quality_score'])
            # Keep only last 100 scores
            self.stats['quality_scores'] = self.stats['quality_scores'][-100:]

        # Update run history
        run_summary = {
            'timestamp': datetime.now().isoformat(),
            'success': run_result['success'],
            'records': run_result.get('records', 0),
            'duration': run_result.get('duration', 0),
            'mode': run_result.get('extraction_mode', 'unknown')
        }
        self.stats['run_history'].append(run_summary)
        # Keep only last 50 runs
        self.stats['run_history'] = self.stats['run_history'][-50:]

        self.save_stats()

    def send_alert(self, subject: str, message: str):
        """Send email alert if configured."""
        alerts_config = self.config.get('alerts', {})
        if not alerts_config.get('enable_email', False):
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = alerts_config['email_sender']
            msg['To'] = alerts_config['email_recipient']
            msg['Subject'] = f"Weather2Geo Pipeline: {subject}"

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(alerts_config['smtp_server'], alerts_config['smtp_port'])
            server.starttls()
            server.login(alerts_config['email_sender'], alerts_config.get('email_password', ''))
            server.send_message(msg)
            server.quit()

            logger.info("Alert email sent successfully")

        except Exception as e:
            logger.error(f"Error sending alert email: {e}")

    def run_extraction_cycle(self, mode: str = 'bulk', **kwargs) -> Dict:
        """Run a single extraction cycle."""
        start_time = datetime.now()
        logger.info(f"Starting extraction cycle: {mode}")

        try:
            # Extract weather data
            if mode == 'bulk':
                weather_data = self.client.get_bulk_weather_data(
                    max_locations=self.config.get('max_locations', 500)
                )
            elif mode == 'conditions':
                weather_data = self.client.extract_weather_by_conditions(
                    target_datetime=kwargs.get('target_datetime', datetime.now()),
                    desired_condition=kwargs.get('condition'),
                    desired_temp=kwargs.get('temperature'),
                    max_locations=kwargs.get('max_locations', 1000)
                )
            else:
                raise ValueError(f"Unknown extraction mode: {mode}")

            # Apply data enrichment
            if self.config.get('enable_enrichment', True):
                weather_data = self.client.enrich_weather_data(weather_data)

            # Calculate quality score
            quality_score = self.calculate_data_quality(weather_data)

            # Save to file
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"weather2geo_{mode}_{timestamp}.json"
            json_file = self.save_weather_data(weather_data, filename)

            # Ingest to pipeline
            ingest_success = True
            if json_file and self.config.get('auto_ingest', True):
                ingest_success = self.ingest_to_pipeline(json_file)

            duration = (datetime.now() - start_time).total_seconds()

            result = {
                'success': True,
                'records': len(weather_data),
                'json_file': json_file,
                'ingest_success': ingest_success,
                'duration': duration,
                'extraction_mode': mode,
                'quality_score': quality_score,
                'timestamp': start_time.isoformat()
            }

            logger.info(f"Extraction cycle completed: {len(weather_data)} records in {duration:.2f}s")
            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Extraction cycle failed: {e}")

            result = {
                'success': False,
                'error': str(e),
                'records': 0,
                'duration': duration,
                'extraction_mode': mode
            }

            # Send alert for failures
            if self.config.get('alerts', {}).get('alert_on_failure', True):
                self.send_alert(
                    "Extraction Failed",
                    f"Weather2Geo extraction cycle failed: {str(e)}"
                )

            return result

    def calculate_data_quality(self, weather_data: List[Dict]) -> float:
        """Calculate data quality score."""
        if not weather_data:
            return 0.0

        total_records = len(weather_data)
        quality_score = 0.0

        # Check completeness (presence of key fields)
        required_fields = ['temperature', 'location_name', 'timestamp']
        completeness_scores = []

        for record in weather_data:
            complete_fields = sum(1 for field in required_fields if record.get(field) is not None)
            completeness_scores.append(complete_fields / len(required_fields))

        avg_completeness = sum(completeness_scores) / len(completeness_scores)

        # Check data reasonableness
        reasonable_scores = []
        for record in weather_data:
            temp = record.get('temperature')
            if temp is not None:
                # Temperature should be between -50°C and 60°C
                reasonable = -50 <= temp <= 60
                reasonable_scores.append(1.0 if reasonable else 0.0)
            else:
                reasonable_scores.append(0.0)

        avg_reasonableness = sum(reasonable_scores) / len(reasonable_scores) if reasonable_scores else 0.0

        # Calculate overall quality score
        quality_score = (avg_completeness * 0.6 + avg_reasonableness * 0.4) * 100

        return round(quality_score, 2)

    def save_weather_data(self, weather_data: List[Dict], filename: str) -> str:
        """Save weather data to JSON file."""
        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(weather_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(weather_data)} records to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error saving weather data: {e}")
            return None

    def ingest_to_pipeline(self, json_file: str) -> bool:
        """Ingest weather data into the ClimateTrade data pipeline."""
        ingest_script = self.config.get('ingest_script')
        db_path = self.config.get('db_path')

        if not Path(ingest_script).exists():
            logger.error(f"Ingest script not found: {ingest_script}")
            return False

        try:
            import subprocess

            cmd = [
                sys.executable,
                ingest_script,
                json_file,
                '--source', 'weather2geo',
                '--location', 'multiple_locations',
                '--db-path', db_path,
                '--verbose'
            ]

            logger.info(f"Running ingest command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

            if result.returncode == 0:
                logger.info("Successfully ingested data into pipeline")
                return True
            else:
                logger.error(f"Ingest failed with return code {result.returncode}")
                logger.error(f"Ingest stderr: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running ingest script: {e}")
            return False

    def cleanup_old_files(self):
        """Clean up old data files based on retention policy."""
        retention_days = self.config.get('retention_days', 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        try:
            for file_path in self.output_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run_batch_processing(self, modes: List[str] = None, batch_size: int = None) -> Dict:
        """Run batch processing for multiple extraction modes."""
        if modes is None:
            modes = self.config.get('extraction_modes', ['bulk'])

        if batch_size is None:
            batch_size = self.config.get('batch_size', 10)

        batch_results = {
            'batch_start': datetime.now().isoformat(),
            'modes_processed': [],
            'total_records': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'results': []
        }

        logger.info(f"Starting batch processing: {len(modes)} modes, batch size {batch_size}")

        for mode in modes:
            mode_results = []
            successful = 0
            failed = 0
            total_records = 0

            for i in range(batch_size):
                logger.info(f"Running {mode} extraction {i+1}/{batch_size}")

                if mode == 'bulk':
                    result = self.run_extraction_cycle(mode='bulk')
                elif mode == 'conditions':
                    # Use different conditions for variety
                    conditions = [
                        ("Mostly cloudy", 20),
                        ("Sunny", 25),
                        ("Partly cloudy", 18),
                        ("Clear", 15)
                    ]
                    condition, temp = conditions[i % len(conditions)]
                    result = self.run_extraction_cycle(
                        mode='conditions',
                        condition=condition,
                        temperature=temp
                    )
                else:
                    continue

                mode_results.append(result)
                self.update_stats(result)

                if result['success']:
                    successful += 1
                    total_records += result.get('records', 0)
                else:
                    failed += 1

                # Small delay between runs
                time.sleep(1)

            mode_summary = {
                'mode': mode,
                'runs': batch_size,
                'successful': successful,
                'failed': failed,
                'total_records': total_records,
                'results': mode_results
            }

            batch_results['modes_processed'].append(mode_summary)
            batch_results['total_records'] += total_records
            batch_results['successful_runs'] += successful
            batch_results['failed_runs'] += failed

        batch_results['batch_end'] = datetime.now().isoformat()
        batch_results['duration'] = (
            datetime.fromisoformat(batch_results['batch_end']) -
            datetime.fromisoformat(batch_results['batch_start'])
        ).total_seconds()

        logger.info(f"Batch processing completed: {batch_results['successful_runs']} successful, {batch_results['failed_runs']} failed")
        return batch_results

    def run_scheduled_pipeline(self):
        """Run the pipeline in scheduled mode."""
        interval_hours = self.config.get('schedule_interval_hours', 6)
        logger.info(f"Starting scheduled pipeline every {interval_hours} hours")

        def pipeline_job():
            try:
                # Run batch processing
                result = self.run_batch_processing()

                # Check quality threshold
                quality_threshold = self.config.get('quality_threshold', 80.0)
                if self.stats['quality_scores']:
                    avg_quality = sum(self.stats['quality_scores']) / len(self.stats['quality_scores'])
                    if avg_quality < quality_threshold:
                        logger.warning(f"Data quality below threshold: {avg_quality}% < {quality_threshold}%")
                        if self.config.get('alerts', {}).get('alert_on_low_quality', True):
                            self.send_alert(
                                "Low Data Quality Alert",
                                f"Average data quality dropped to {avg_quality}%. Threshold: {quality_threshold}%"
                            )

                # Cleanup old files
                self.cleanup_old_files()

                logger.info(f"Scheduled pipeline completed: {result['successful_runs']} successful runs")

            except Exception as e:
                logger.error(f"Scheduled pipeline error: {e}")
                self.send_alert("Pipeline Error", f"Scheduled pipeline failed: {str(e)}")

        # Schedule the job
        schedule.every(interval_hours).hours.do(pipeline_job)

        # Run initial job
        pipeline_job()

        # Keep running scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(300)  # Check every 5 minutes
        except KeyboardInterrupt:
            logger.info("Scheduled pipeline stopped by user")
        except Exception as e:
            logger.error(f"Scheduled pipeline error: {e}")

    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status and statistics."""
        return {
            'config': self.config,
            'stats': self.stats,
            'last_run': self.stats.get('last_run'),
            'is_running': True,  # This would be more sophisticated in a real implementation
            'next_scheduled_run': None  # Would calculate based on schedule
        }

def main():
    parser = argparse.ArgumentParser(
        description="Weather2Geo Automated Processing Pipeline"
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )

    # Operation modes
    parser.add_argument(
        '--mode',
        choices=['single', 'batch', 'scheduled'],
        default='single',
        help='Pipeline operation mode'
    )

    # Single run options
    parser.add_argument(
        '--extract-mode',
        choices=['bulk', 'conditions'],
        default='bulk',
        help='Extraction mode for single run'
    )

    parser.add_argument(
        '--condition',
        type=str,
        help='Weather condition for conditions mode'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        help='Temperature for conditions mode'
    )

    # Batch options
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Number of runs per mode in batch processing'
    )

    # Status and monitoring
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show pipeline status and statistics'
    )

    # Logging
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        pipeline = AutomatedPipeline(args.config)

        if args.status:
            # Show pipeline status
            status = pipeline.get_pipeline_status()
            print(json.dumps(status, indent=2, default=str))
            return

        if args.mode == 'scheduled':
            # Run in scheduled mode
            pipeline.run_scheduled_pipeline()

        elif args.mode == 'batch':
            # Run batch processing
            result = pipeline.run_batch_processing(batch_size=args.batch_size)
            print(json.dumps(result, indent=2, default=str))

        else:  # single mode
            # Run single extraction cycle
            result = pipeline.run_extraction_cycle(
                mode=args.extract_mode,
                condition=args.condition,
                temperature=args.temperature
            )

            pipeline.update_stats(result)

            if result['success']:
                print(f"✅ Extraction completed successfully!")
                print(f"📊 Records extracted: {result['records']}")
                print(f"⏱️  Duration: {result['duration']:.2f}s")
                print(f"📈 Quality Score: {result.get('quality_score', 'N/A')}%")
                if result.get('json_file'):
                    print(f"💾 Data saved to: {result['json_file']}")
                if result.get('ingest_success'):
                    print("🔄 Data ingested into pipeline")
            else:
                print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()