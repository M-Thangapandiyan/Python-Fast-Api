"""
Logger configuration for the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)  


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_format = logging.Formatter("[%(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s")

# info file logging setup
info_log_file_= RotatingFileHandler(os.path.join(LOG_DIR,"app.log"), maxBytes=5_000_000,backupCount=5)
info_log_file_.setFormatter(log_format)
info_log_file_.setFormatter(log_format)
info_log_file_.setLevel(logging.INFO)


# error file logging setup
error_log_file= RotatingFileHandler(os.path.join(LOG_DIR,"error.log"), maxBytes=5_000_000,backupCount=5)
error_log_file.setFormatter(log_format)
error_log_file.setLevel(logging.ERROR)   
error_log_file.setFormatter(log_format)


# terminal logging setup
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.INFO)

# Add all handlers to logger
logger.addHandler(info_log_file_)
logger.addHandler(error_log_file)
logger.addHandler(console_handler)

