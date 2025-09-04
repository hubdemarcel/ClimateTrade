#!/usr/bin/env python3
"""
Weather2Geo Integration for ClimateTrade Data Pipeline

This script integrates Weather2Geo data extraction with the existing
ClimateTrade data collection pipeline, providing enhanced weather
data points from MSN Weather API.

Features:
- Automated Weather2Geo data extraction
- Integration with existing data pipeline
- Data enrichment and quality processing
- Support for multiple extraction modes
- Comprehensive logging and error handling
"""

import os
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import schedule
import time

# Add project root to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add Weather2Geo to path
sys.path.append(str(Path(__file__).parent / "Weather2Geo"))

try:
    from weather2geo_client import Weather2GeoClient
except ImportError as e:
    print(f"Error importing Weather2Geo client: {e}")
    print("Make sure Weather2Geo dependencies are installed")
    sys.exit(1)

# Import centralized logging
try:
    from utils.logging import setup_logging, get_logger
    # Setup centralized logging
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging if centralized system not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('weather2geo_integration.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

class Weather2GeoIntegration:
    """Integration class for Weather2Geo data extraction and pipeline processing."""

    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.client = Weather2GeoClient(
            cities_file=self.config.get('cities_file', '../data/cities15000.txt'),
            max_workers=self.config.get('max_workers', 50)
        )
        self.output_dir = Path(self.config.get('output_dir', 'data/weather2geo_output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'cities_file': '../data/cities15000.txt',
            'max_workers': 50,
            'output_dir': 'data/weather2geo_output',
            'extraction_mode': 'bulk',  # 'bulk', 'conditions', 'locations'
            'max_locations': 500,
            'temp_tolerance': 1.0,
            'enable_enrichment': True,
            'auto_ingest': True,
            'ingest_script': 'data_pipeline/ingest_weather.py',
            'db_path': 'data/climatetrade.db',
            'schedule_interval': 3600,  # seconds
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

    def extract_weather_data(self,
                           mode: str = None,
                           target_datetime: datetime = None,
                           locations: List = None,
                           condition: str = None,
                           temperature: float = None) -> List[Dict]:
        """Extract weather data based on specified parameters."""

        mode = mode or self.config.get('extraction_mode', 'bulk')

        if mode == 'conditions':
            if not target_datetime:
                target_datetime = datetime.now()

            logger.info(f"Extracting weather data for conditions: {condition}, temp: {temperature}°C at {target_datetime}")
            weather_data = self.client.extract_weather_by_conditions(
                target_datetime=target_datetime,
                desired_condition=condition,
                desired_temp=temperature,
                temp_tolerance=self.config.get('temp_tolerance', 1.0),
                max_locations=self.config.get('max_locations', 1000)
            )

        elif mode == 'locations':
            if not locations:
                logger.error("Locations mode requires location list")
                return []

            logger.info(f"Extracting weather data for {len(locations)} specific locations")
            weather_data = self.client.get_bulk_weather_data(locations=locations)

        else:  # bulk mode
            if not target_datetime:
                target_datetime = datetime.now()

            logger.info(f"Extracting bulk weather data for {target_datetime}")
            weather_data = self.client.get_bulk_weather_data(
                target_datetime=target_datetime,
                max_locations=self.config.get('max_locations', 500)
            )

        # Apply data enrichment if enabled
        if self.config.get('enable_enrichment', True):
            logger.info("Enriching weather data with derived metrics")
            weather_data = self.client.enrich_weather_data(weather_data)

        logger.info(f"Extracted {len(weather_data)} weather records")
        return weather_data

    def save_weather_data(self, weather_data: List[Dict], filename: str = None) -> str:
        """Save weather data to JSON file."""
        if not weather_data:
            logger.warning("No weather data to save")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weather2geo_{timestamp}.json"

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
        if not self.config.get('auto_ingest', True):
            logger.info("Auto-ingest disabled, skipping pipeline ingestion")
            return True

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
                logger.info(f"Ingest output: {result.stdout}")
                return True
            else:
                logger.error(f"Ingest failed with return code {result.returncode}")
                logger.error(f"Ingest stderr: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running ingest script: {e}")
            return False

    def run_extraction_cycle(self,
                           mode: str = None,
                           target_datetime: datetime = None,
                           locations: List = None,
                           condition: str = None,
                           temperature: float = None,
                           save_file: bool = True) -> Dict:
        """Run a complete extraction cycle."""

        start_time = datetime.now()
        logger.info("Starting Weather2Geo extraction cycle")

        try:
            # Extract weather data
            weather_data = self.extract_weather_data(
                mode=mode,
                target_datetime=target_datetime,
                locations=locations,
                condition=condition,
                temperature=temperature
            )

            if not weather_data:
                return {
                    'success': False,
                    'error': 'No weather data extracted',
                    'records': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # Save to file
            json_file = None
            if save_file:
                json_file = self.save_weather_data(weather_data)

            # Ingest to pipeline
            ingest_success = True
            if json_file:
                ingest_success = self.ingest_to_pipeline(json_file)

            duration = (datetime.now() - start_time).total_seconds()

            result = {
                'success': True,
                'records': len(weather_data),
                'json_file': json_file,
                'ingest_success': ingest_success,
                'duration': duration,
                'extraction_mode': mode or self.config.get('extraction_mode'),
                'timestamp': start_time.isoformat()
            }

            logger.info(f"Extraction cycle completed successfully in {duration:.2f}s")
            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Extraction cycle failed: {e}")

            return {
                'success': False,
                'error': str(e),
                'records': 0,
                'duration': duration
            }

    def run_scheduled_extraction(self):
        """Run scheduled extraction cycles."""
        interval = self.config.get('schedule_interval', 3600)
        logger.info(f"Starting scheduled extraction every {interval} seconds")

        def extraction_job():
            try:
                result = self.run_extraction_cycle()
                if result['success']:
                    logger.info(f"Scheduled extraction completed: {result['records']} records")
                else:
                    logger.error(f"Scheduled extraction failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Scheduled extraction error: {e}")

        # Schedule the job
        schedule.every(interval).seconds.do(extraction_job)

        # Run initial extraction
        extraction_job()

        # Keep running scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduled extraction stopped by user")
        except Exception as e:
            logger.error(f"Scheduled extraction error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Weather2Geo Integration for ClimateTrade Data Pipeline"
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )

    # Extraction mode
    parser.add_argument(
        '--mode',
        choices=['bulk', 'conditions', 'locations'],
        default='bulk',
        help='Extraction mode (default: bulk)'
    )

    # Conditions mode options
    parser.add_argument(
        '--datetime',
        type=str,
        help='Target date/time in ISO format (YYYY-MM-DDTHH:MM:SS)'
    )
    parser.add_argument(
        '--condition',
        type=str,
        help='Weather condition to match (e.g., "Mostly cloudy")'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        help='Target temperature in Celsius'
    )

    # Locations mode options
    parser.add_argument(
        '--locations-file',
        type=str,
        help='JSON file with locations list [{"name": "City", "lat": 0.0, "lon": 0.0}]'
    )

    # Output options
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output filename (default: auto-generated)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Skip saving to file'
    )
    parser.add_argument(
        '--no-ingest',
        action='store_true',
        help='Skip automatic pipeline ingestion'
    )

    # Scheduling
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run in scheduled mode'
    )

    # Logging
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        # Update logging level for verbose output
        try:
            from utils.logging import update_logging_config, LogConfig
            config = LogConfig(level='DEBUG', console_level='DEBUG')
            update_logging_config(config)
        except ImportError:
            logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize integration
        integration = Weather2GeoIntegration(args.config)

        # Override config for no-ingest
        if args.no_ingest:
            integration.config['auto_ingest'] = False

        if args.schedule:
            # Run in scheduled mode
            integration.run_scheduled_extraction()

        else:
            # Parse datetime
            target_datetime = None
            if args.datetime:
                try:
                    target_datetime = datetime.fromisoformat(args.datetime.replace('Z', '+00:00'))
                except ValueError:
                    logger.error("Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
                    sys.exit(1)

            # Parse locations
            locations = None
            if args.locations_file and Path(args.locations_file).exists():
                try:
                    with open(args.locations_file, 'r') as f:
                        locations_data = json.load(f)
                    locations = [(loc['name'], loc['lat'], loc['lon']) for loc in locations_data]
                except Exception as e:
                    logger.error(f"Error loading locations file: {e}")
                    sys.exit(1)

            # Run extraction cycle
            result = integration.run_extraction_cycle(
                mode=args.mode,
                target_datetime=target_datetime,
                locations=locations,
                condition=args.condition,
                temperature=args.temperature,
                save_file=not args.no_save
            )

            # Print result
            if result['success']:
                print(f"✅ Extraction completed successfully!")
                print(f"📊 Records extracted: {result['records']}")
                print(f"⏱️  Duration: {result['duration']:.2f}s")
                if result.get('json_file'):
                    print(f"💾 Data saved to: {result['json_file']}")
                if result.get('ingest_success'):
                    print("🔄 Data ingested into pipeline")
                else:
                    print("⚠️  Pipeline ingestion failed")
            else:
                print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Integration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()