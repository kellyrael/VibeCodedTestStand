#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
from systemlink_reporter import create_reporter

logger = logging.getLogger("test_reporter")

reporter = create_reporter(logger=logger)
if reporter:
    print("Reporter created successfully!")
    try:
        reporter.connect()
        print("Connected to SystemLink!")
    except Exception as e:
        print(f"Connection failed: {type(e).__name__}: {e}")
else:
    print("Reporter creation failed (returned None)")


