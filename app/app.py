#!/usr/bin/env python3
"""
Simple test application that generates random structured logs
"""

import json
import logging
import sys
import time
from datetime import datetime
from random import choice, randint, gauss

# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        
        return json.dumps(log_entry)

# Setup logger
logger = logging.getLogger("test-app")
logger.setLevel(logging.INFO)

# Console handler with JSON formatter
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

def simulate_user_action():
    """Simulate a user action and log it."""
    actions = ["login", "view_page", "purchase", "logout", "search"]
    action = choice(actions)
    user_id = randint(1000, 9999)
    request_id = f"req-{randint(10000000, 99999999)}"
    duration = max(10, min(500, int(gauss(255, 80))))
    status_codes = [200, 200, 200, 404, 500, 502, 503, 504]  # Mostly success, some errors
    status = choice(status_codes)
    
    logger.info(
        f"User action: {action}",
        extra={
            "user_id": user_id,
            "request_id": request_id,
            "duration_ms": duration,
            "status_code": status,
            "action": action
        }
    )
    
    if status >= 500:
        logger.error(
            f"Error processing {action}",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "error_type": "server_error"
            }
        )

def main():
    """Main application loop."""
    logger.info("Application started", extra={"version": "1.0.0"})
    
    try:
        while True:
            simulate_user_action()
            time.sleep(randint(3, 6))
    except KeyboardInterrupt:
        logger.info("Application stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
