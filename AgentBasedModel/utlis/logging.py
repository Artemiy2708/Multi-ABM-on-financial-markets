import datetime
import logging


def create_logger(filename: str = "results.log") -> logging.Logger:
    FORMAT = '%(asctime)s.%(msecs)03d\t%(levelname)s\t[%(filename)s:%(lineno)d]\t%(message)s'
    DATEFMT = "%H:%M:%S"
    logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt=DATEFMT)
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(logging.Formatter(FORMAT))
    file_handler.setLevel(logging.ERROR)
    logger.addHandler(file_handler)
    return logger


Logger = create_logger(filename=f"output/logs/experiment_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
