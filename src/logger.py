import logging

WHITE = "\033[0m"
LOGLEVEL_COLORS = {
    "DEBUG": "\033[32m", # green
    'INFO': WHITE,       
    'WARNING': "\033[33m", # yellow
    'ERROR': "\033[31m",   # red
    'CRITICAL': "\033[1;31m" # dark red
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "process_name"):
            record.process_name = "-"
        levelname = record.levelname
        color = LOGLEVEL_COLORS.get(levelname, "")
        record.levelname = f"{color}{levelname}{WHITE}"
        # record.msg = f"{record.msg}"
        return super().format(record)


def setup_logger(logger_name="test-name", debug_mode=False):
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        handler.setFormatter(
            ColorFormatter("%(asctime)s %(levelname)s: [%(process_name)s] %(message)s",
                           datefmt="%H:%M:%S"))
            
        logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        logger.handlers = [handler]
        logger.propagate = False
    return logger
    

if __name__ == "__main__":
    logger = setup_logger(debug_mode=True)
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    
    
    process_name = "random_proces"
    logger.debug("debug message", extra={"process_name": process_name})
    logger.info("info message", extra={"process_name": process_name})
    logger.warning("warning message", extra={"process_name": process_name})
    logger.error("error message", extra={"process_name": process_name})
    logger.critical("critical message", extra={"process_name": process_name})