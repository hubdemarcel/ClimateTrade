"""
Logging Handlers Module

This module provides custom handlers for different logging needs including
rotating file handlers, environment-specific handlers, and buffered handlers.
"""

import gzip
import logging
import logging.handlers
import os
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Enhanced rotating file handler with compression support.

    This handler extends the standard RotatingFileHandler with optional
    compression of rotated log files.
    """

    def __init__(self,
                 filename: str,
                 mode: str = 'a',
                 maxBytes: int = 0,
                 backupCount: int = 0,
                 encoding: Optional[str] = None,
                 delay: bool = False,
                 compress: bool = True,
                 compression_method: str = 'gzip'):
        """
        Initialize the rotating file handler.

        Args:
            filename: Log file path
            mode: File mode
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding
            delay: Whether to delay file opening
            compress: Whether to compress rotated files
            compression_method: Compression method ('gzip' or 'bz2')
        """
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress = compress
        self.compression_method = compression_method

    def doRollover(self):
        """
        Perform log rotation with optional compression.
        """
        super().doRollover()

        if self.compress:
            self._compress_rotated_files()

    def _compress_rotated_files(self):
        """
        Compress rotated log files in a separate thread.
        """
        # Get the list of files to compress
        log_dir = Path(self.baseFilename).parent
        base_name = Path(self.baseFilename).stem
        extension = Path(self.baseFilename).suffix

        files_to_compress = []
        for i in range(1, self.backupCount + 1):
            rotated_file = log_dir / f"{base_name}.{i}{extension}"
            if rotated_file.exists():
                files_to_compress.append(rotated_file)

        # Compress files asynchronously
        if files_to_compress:
            executor = ThreadPoolExecutor(max_workers=2)
            for rotated_file in files_to_compress:
                executor.submit(self._compress_file, rotated_file)

    def _compress_file(self, file_path: Path):
        """
        Compress a single log file.

        Args:
            file_path: Path to the file to compress
        """
        try:
            compressed_path = file_path.with_suffix(f"{file_path.suffix}.gz")

            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove the original file
            file_path.unlink()

        except Exception as e:
            # Log compression errors but don't fail the rotation
            print(f"Failed to compress log file {file_path}: {e}")


class EnvironmentHandler(logging.Handler):
    """
    Environment-aware handler that routes logs based on environment.

    This handler can route logs to different destinations based on the
    current environment (development, production, etc.).
    """

    def __init__(self,
                 environment: str,
                 development_handler: Optional[logging.Handler] = None,
                 production_handler: Optional[logging.Handler] = None,
                 testing_handler: Optional[logging.Handler] = None):
        """
        Initialize the environment handler.

        Args:
            environment: Current environment
            development_handler: Handler for development environment
            production_handler: Handler for production environment
            testing_handler: Handler for testing environment
        """
        super().__init__()
        self.environment = environment.lower()

        # Set default handlers if not provided
        self.handlers = {
            'development': development_handler or logging.StreamHandler(),
            'production': production_handler or self._create_production_handler(),
            'testing': testing_handler or self._create_testing_handler(),
            'staging': production_handler or self._create_production_handler()
        }

    def _create_production_handler(self) -> logging.Handler:
        """Create a production-ready handler."""
        return RotatingFileHandler(
            'logs/climatetrade.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=30,
            compress=True
        )

    def _create_testing_handler(self) -> logging.Handler:
        """Create a testing handler."""
        return RotatingFileHandler(
            'test_logs/test.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            compress=False
        )

    def emit(self, record: logging.LogRecord):
        """
        Emit the log record to the appropriate handler.

        Args:
            record: Log record to emit
        """
        handler = self.handlers.get(self.environment, self.handlers['development'])
        if handler:
            handler.emit(record)


class BufferedHandler(logging.Handler):
    """
    Buffered handler for high-performance logging.

    This handler buffers log records and flushes them in batches,
    reducing I/O overhead for high-volume logging.
    """

    def __init__(self,
                 target_handler: logging.Handler,
                 buffer_size: int = 1000,
                 flush_interval: float = 1.0):
        """
        Initialize the buffered handler.

        Args:
            target_handler: The handler to buffer records for
            buffer_size: Maximum number of records to buffer
            flush_interval: Time interval for flushing (seconds)
        """
        super().__init__()
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        self.buffer: List[logging.LogRecord] = []
        self.last_flush = time.time()
        self.lock = threading.Lock()

        # Start flush timer
        self.timer = threading.Timer(self.flush_interval, self._periodic_flush)
        self.timer.daemon = True
        self.timer.start()

    def emit(self, record: logging.LogRecord):
        """
        Buffer the log record.

        Args:
            record: Log record to buffer
        """
        with self.lock:
            self.buffer.append(record)

            # Flush if buffer is full
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush all buffered records to the target handler."""
        with self.lock:
            if self.buffer:
                for record in self.buffer:
                    try:
                        self.target_handler.emit(record)
                    except Exception:
                        # Continue processing other records even if one fails
                        pass
                self.buffer.clear()
            self.last_flush = time.time()

    def _periodic_flush(self):
        """Periodically flush the buffer."""
        self._flush_buffer()

        # Schedule next flush
        self.timer = threading.Timer(self.flush_interval, self._periodic_flush)
        self.timer.daemon = True
        self.timer.start()

    def close(self):
        """Close the handler and flush any remaining records."""
        if self.timer:
            self.timer.cancel()
        self._flush_buffer()
        self.target_handler.close()
        super().close()


class AsyncHandler(logging.Handler):
    """
    Asynchronous handler for non-blocking logging.

    This handler processes log records in a separate thread to avoid
    blocking the main application thread.
    """

    def __init__(self, target_handler: logging.Handler, queue_size: int = 1000):
        """
        Initialize the async handler.

        Args:
            target_handler: The handler to process records asynchronously
            queue_size: Maximum queue size for pending records
        """
        super().__init__()
        self.target_handler = target_handler
        self.queue_size = queue_size

        self.queue = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def emit(self, record: logging.LogRecord):
        """
        Queue the log record for asynchronous processing.

        Args:
            record: Log record to queue
        """
        with self.condition:
            if len(self.queue) < self.queue_size:
                self.queue.append(record)
                self.condition.notify()
            else:
                # Queue is full, drop the record or handle overflow
                pass

    def _worker(self):
        """Worker thread that processes queued records."""
        while True:
            with self.condition:
                while not self.queue:
                    self.condition.wait()

                # Process all queued records
                records = self.queue[:]
                self.queue.clear()

            # Process records outside the lock
            for record in records:
                try:
                    self.target_handler.emit(record)
                except Exception:
                    # Continue processing other records
                    pass

    def close(self):
        """Close the handler."""
        self.target_handler.close()
        super().close()