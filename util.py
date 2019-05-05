import logging

def init_logging(name):
    log = logging.getLogger(name=name)
    log.setLevel(logging.DEBUG)
    if len(log.handlers):
        return log
    sh = logging.StreamHandler()
    sh.level = logging.DEBUG
    log.addHandler(sh)
    return log