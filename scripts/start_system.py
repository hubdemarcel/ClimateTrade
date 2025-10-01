#!/usr/bin/env python3
"""
ClimaTrade AI System Startup Script

This script provides a unified way to start different components of the ClimaTrade AI system.
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / "web" / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SystemStarter:
    """Manages starting different components of the ClimaTrade AI system"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes: List[subprocess.Popen] = []

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("[INFO] Checking prerequisites...")

        # Check Python version
        if sys.version_info < (3, 9):
            print("[ERROR] Python 3.9+ required")
            return False

        # Check virtual environment
        if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
            print("[WARNING] Not running in virtual environment")

        # Check database
        db_path = self.project_root / "data" / "climatetrade.db"
        if not db_path.exists():
            print("[WARNING] Database not found. Run database setup first.")
            return False

        # Check environment variables
        required_env_vars = ['MET_OFFICE_API_KEY', 'POLYGON_WALLET_PRIVATE_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            print(f"[WARNING] Missing environment variables: {', '.join(missing_vars)}")

        print("[OK] Prerequisites check completed")
        return True

    def start_backtesting(self, strategy: str = "temperature", background: bool = True) -> Optional[subprocess.Popen]:
        """Start the backtesting framework"""
        print(f"[START] Starting backtesting framework with {strategy} strategy...")

        cmd = [
            sys.executable,
            str(self.project_root / "backtesting_framework" / "main.py"),
            "single",
            "--strategy", strategy
        ]

        if background:
            process = subprocess.Popen(cmd, cwd=self.project_root)
            self.processes.append(process)
            print(f"[OK] Backtesting started in background (PID: {process.pid})")
            return process
        else:
            return subprocess.run(cmd, cwd=self.project_root)

    def start_data_collection(self, background: bool = True) -> Optional[subprocess.Popen]:
        """Start data collection pipeline"""
        print("[START] Starting data collection pipeline...")

        cmd = [
            sys.executable,
            str(self.project_root / "scripts" / "example_real_time_integration.py")
        ]

        if background:
            process = subprocess.Popen(cmd, cwd=self.project_root)
            self.processes.append(process)
            print(f"[OK] Data collection started in background (PID: {process.pid})")
            return process
        else:
            return subprocess.run(cmd, cwd=self.project_root)

    def start_agent_cli(self, command: str = "get-all-markets", background: bool = False) -> Optional[subprocess.Popen]:
        """Start the agent CLI"""
        print(f"[START] Starting agent CLI with command: {command}...")

        cmd = [
            sys.executable,
            str(self.project_root / "scripts" / "agents" / "scripts" / "python" / "cli.py"),
            command
        ]

        if background:
            process = subprocess.Popen(cmd, cwd=self.project_root)
            self.processes.append(process)
            print(f"[OK] Agent CLI started in background (PID: {process.pid})")
            return process
        else:
            return subprocess.run(cmd, cwd=self.project_root)

    def start_dashboard(self) -> None:
        """Start the web dashboard"""
        print("[START] Starting ClimaTrade AI Dashboard...")

        # Check if we're in the web directory
        web_dir = self.project_root / "web"
        if not web_dir.exists():
            print("[ERROR] Web directory not found. Please ensure dashboard is properly set up.")
            return

        # Start backend
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ]

        backend_process = subprocess.Popen(backend_cmd, cwd=str(self.project_root / "web"))
        self.processes.append(backend_process)
        print(f"[OK] Backend started on http://localhost:8001 (PID: {backend_process.pid})")

        # Start frontend (requires npm)
        try:
            # Use 'npm run dev' to be consistent with documentation and standard practice
            frontend_cmd = ["npm", "run", "dev"]
            frontend_process = subprocess.Popen(
                frontend_cmd,
                cwd=str(web_dir / "frontend"),
                shell=True
            )
            self.processes.append(frontend_process)
            print(f"[OK] Frontend development server starting (PID: {frontend_process.pid})")
            print("[INFO] Vite will find an open port (e.g., 8080, 8081, etc.)")
        except FileNotFoundError:
            print("[WARNING] npm not found. Please install Node.js and run 'npm install' in web/frontend/")
            print("[INFO] You can still access the backend API at http://localhost:8001")

        print("[OK] Dashboard started successfully")
        print("[INFO] Backend API: http://localhost:8001")
        print("[INFO] API Docs: http://localhost:8001/docs")
        print("[INFO] Check the terminal output for the exact Frontend URL (e.g., http://localhost:8082/)")

    def start_full_system(self) -> None:
        """Start all components of the system"""
        print("[START] Starting full ClimaTrade AI system...")

        # Start data collection
        self.start_data_collection(background=True)
        time.sleep(2)  # Brief pause between starts

        # Start backtesting with temperature strategy
        self.start_backtesting(strategy="temperature", background=True)
        time.sleep(2)

        # Start agent system monitoring markets
        self.start_agent_cli(command="get-all-markets", background=True)

        print("[OK] Full system started successfully")
        print("[INFO] System components running in background")
        print("[INFO] Use Ctrl+C to stop all components")

    def stop_all(self) -> None:
        """Stop all running processes"""
        print("[STOP] Stopping all system components...")

        for process in self.processes:
            if process.poll() is None:  # Still running
                process.terminate()

        # Wait for processes to terminate
        time.sleep(2)

        # Force kill if still running
        for process in self.processes:
            if process.poll() is None:
                process.kill()

        self.processes.clear()
        print("[OK] All components stopped")

    def show_status(self) -> None:
        """Show status of running components"""
        print("[STATUS] System Status:")

        if not self.processes:
            print("   No components currently running")
            return

        for i, process in enumerate(self.processes, 1):
            status = "Running" if process.poll() is None else f"Exited ({process.returncode})"
            print(f"   Component {i}: {status} (PID: {process.pid})")

    def run_health_check(self) -> None:
        """Run basic health checks"""
        print("[HEALTH] Running health checks...")

        # Check database
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.project_root / "data" / "climatetrade.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM weather_data")
            count = cursor.fetchone()[0]
            print(f"[OK] Database: {count} weather records")
            conn.close()
        except Exception as e:
            print(f"[ERROR] Database check failed: {e}")

        # Check API keys
        api_keys_ok = all([
            os.getenv('MET_OFFICE_API_KEY'),
            os.getenv('POLYGON_WALLET_PRIVATE_KEY')
        ])
        print(f"[OK] API Keys: {'Configured' if api_keys_ok else 'Missing'}")

        print("[OK] Health check completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ClimaTrade AI System Starter")
    parser.add_argument(
        "--mode",
        choices=["development", "backtesting", "data-collection", "agents", "dashboard", "full"],
        default="development",
        help="System startup mode"
    )
    parser.add_argument(
        "--component",
        choices=["backtesting", "data-pipeline", "agents", "all"],
        help="Specific component to start"
    )
    parser.add_argument(
        "--strategy",
        default="temperature",
        help="Backtesting strategy to use"
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run components in background"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all running components"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health checks"
    )

    args = parser.parse_args()

    starter = SystemStarter()

    try:
        if args.status:
            starter.show_status()
        elif args.stop:
            starter.stop_all()
        elif args.health_check:
            starter.run_health_check()
        elif args.component:
            # Start specific component
            if not starter.check_prerequisites():
                sys.exit(1)

            if args.component == "backtesting":
                starter.start_backtesting(args.strategy, args.background)
            elif args.component == "data-pipeline":
                starter.start_data_collection(args.background)
            elif args.component == "agents":
                starter.start_agent_cli("get-all-markets", args.background)
            elif args.component == "all":
                starter.start_full_system()
        else:
            # Default mode-based startup
            if not starter.check_prerequisites():
                sys.exit(1)

            if args.mode == "development":
                print("[MODE] Development mode: Starting essential components...")
                starter.start_data_collection(background=True)
                time.sleep(2)
                starter.start_backtesting(args.strategy, background=True)
            elif args.mode == "backtesting":
                starter.start_backtesting(args.strategy, args.background)
            elif args.mode == "data-collection":
                starter.start_data_collection(args.background)
            elif args.mode == "agents":
                starter.start_agent_cli("get-all-markets", args.background)
            elif args.mode == "dashboard":
                starter.start_dashboard()
            elif args.mode == "full":
                starter.start_full_system()

        # Keep running if background processes are started
        if starter.processes and not args.background:
            print("\n[INFO] System running. Press Ctrl+C to stop...")
            try:
                while starter.processes:
                    time.sleep(1)
                    # Clean up finished processes
                    starter.processes = [p for p in starter.processes if p.poll() is None]
            except KeyboardInterrupt:
                print("\n[STOP] Received interrupt signal...")
                starter.stop_all()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        starter.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()