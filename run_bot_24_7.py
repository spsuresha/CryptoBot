"""
24/7 Bot Runner with Automatic Restart on Failure
Monitors the bot and restarts it automatically if it crashes.
"""
import subprocess
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
import psutil
import json

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "bot_runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BotRunner:
    """Manages bot execution with automatic restart."""

    def __init__(self, mode="paper", pair="BTC/USDT", timeframe="5m"):
        """
        Initialize bot runner.

        Args:
            mode: Trading mode (paper or live)
            pair: Trading pair
            timeframe: Timeframe for trading
        """
        self.mode = mode
        self.pair = pair
        self.timeframe = timeframe
        self.max_restart_attempts = 5
        self.restart_delay = 60  # seconds
        self.restart_count = 0
        self.start_time = datetime.now()
        self.process = None
        self.stats_file = Path("logs/bot_stats.json")

    def run_bot(self):
        """Run the trading bot."""
        logger.info("=" * 60)
        logger.info("STARTING TRADING BOT - 24/7 MODE")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.mode.upper()}")
        logger.info(f"Pair: {self.pair}")
        logger.info(f"Timeframe: {self.timeframe}")
        logger.info(f"Started at: {self.start_time}")
        logger.info("=" * 60)

        while True:
            try:
                self._execute_bot()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Shutting down gracefully...")
                self._cleanup()
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                self._handle_failure()

    def _execute_bot(self):
        """Execute the bot process."""
        cmd = [
            sys.executable,
            "main.py",
            self.mode,
            "--pair", self.pair,
            "--timeframe", self.timeframe
        ]

        logger.info(f"Executing: {' '.join(cmd)}")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Monitor the process
        self._monitor_process()

    def _monitor_process(self):
        """Monitor the bot process and handle output."""
        logger.info(f"Bot process started (PID: {self.process.pid})")

        while True:
            # Check if process is still running
            if self.process.poll() is not None:
                # Process has terminated
                return_code = self.process.returncode
                logger.warning(f"Bot process terminated with code: {return_code}")

                # Read remaining output
                stdout, stderr = self.process.communicate()
                if stdout:
                    logger.info(f"Bot stdout: {stdout}")
                if stderr:
                    logger.error(f"Bot stderr: {stderr}")

                raise RuntimeError(f"Bot crashed with exit code {return_code}")

            # Read output line by line
            if self.process.stdout:
                line = self.process.stdout.readline()
                if line:
                    print(line.strip())

            time.sleep(1)

    def _handle_failure(self):
        """Handle bot failure and attempt restart."""
        self.restart_count += 1

        logger.error(f"Bot failure #{self.restart_count}")

        if self.restart_count >= self.max_restart_attempts:
            logger.critical(
                f"Max restart attempts ({self.max_restart_attempts}) reached. "
                "Bot will not restart automatically."
            )
            self._save_stats()
            sys.exit(1)

        # Calculate exponential backoff
        delay = self.restart_delay * (2 ** (self.restart_count - 1))
        delay = min(delay, 3600)  # Max 1 hour

        logger.info(f"Restarting in {delay} seconds...")
        logger.info(f"Restart attempt {self.restart_count}/{self.max_restart_attempts}")

        time.sleep(delay)

        logger.info("Attempting to restart bot...")

    def _cleanup(self):
        """Cleanup on shutdown."""
        logger.info("Cleaning up...")

        if self.process and self.process.poll() is None:
            logger.info("Terminating bot process...")
            self.process.terminate()

            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Process didn't terminate gracefully, forcing kill...")
                self.process.kill()

        self._save_stats()
        logger.info("Cleanup complete")

    def _save_stats(self):
        """Save runtime statistics."""
        stats = {
            "mode": self.mode,
            "pair": self.pair,
            "timeframe": self.timeframe,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "restart_count": self.restart_count,
            "runtime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }

        try:
            self.stats_file.write_text(json.dumps(stats, indent=2))
            logger.info(f"Stats saved to {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def get_system_info(self):
        """Log system information."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            logger.info("=" * 60)
            logger.info("SYSTEM INFORMATION")
            logger.info("=" * 60)
            logger.info(f"CPU Usage: {cpu_percent}%")
            logger.info(f"Memory Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
            logger.info(f"Disk Usage: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run trading bot 24/7 with automatic restart"
    )
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="Trading mode (default: paper)"
    )
    parser.add_argument(
        "--pair",
        default="BTC/USDT",
        help="Trading pair (default: BTC/USDT)"
    )
    parser.add_argument(
        "--timeframe",
        default="5m",
        help="Trading timeframe (default: 5m)"
    )

    args = parser.parse_args()

    # Confirm live trading
    if args.mode == "live":
        print("\n" + "=" * 60)
        print("WARNING: LIVE TRADING MODE - REAL MONEY AT RISK!")
        print("=" * 60)
        confirmation = input("\nType 'START LIVE TRADING 24/7' to confirm: ")

        if confirmation != "START LIVE TRADING 24/7":
            print("Live trading cancelled.")
            sys.exit(0)

    # Create and run bot runner
    runner = BotRunner(
        mode=args.mode,
        pair=args.pair,
        timeframe=args.timeframe
    )

    # Log system info
    runner.get_system_info()

    # Start the bot
    runner.run_bot()


if __name__ == "__main__":
    main()
