import logging

def get_logger(name):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logfile = logging.FileHandler('log.txt')
    logfile.setLevel(logging.INFO)
    logfile.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(logfile)
    logger.addHandler(console)
    return logger
    