import logging
import os

def setup_logger(log_file="slr_process.log"):
    """
    Sets up a logger that writes to both File and Console.
    """
    # Create a custom logger
    logger = logging.getLogger("SLR_Logger")
    logger.setLevel(logging.DEBUG) # Capture everything

    # Prevent duplicate logs if function is called twice
    if logger.handlers:
        return logger

    # 1. File Handler (Saves detailed logs to file)
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 2. Console Handler (Shows clean summaries to screen)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) # Only show INFO+ to screen (keeps terminal clean)
    console_formatter = logging.Formatter('%(message)s') 
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger