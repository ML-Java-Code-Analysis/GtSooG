# coding=utf-8
from datetime import datetime

MODE_PRINT = 0
MODE_LOGFILE = 1

LEVEL_ERROR = 0
LEVEL_WARNING = 1
LEVEL_INFO = 2
LEVEL_DEBUG = 3

default_mode = MODE_PRINT
default_logfile = "log.txt"
file_pointers = {}
max_log_level = LEVEL_DEBUG


def set_min_log_level(level):
    """ Sets the maximum level of logs which actually should be logged.

    Args:
        level (int): The log level. Use the LEVEL_X constants from this module.
    """
    globals()['max_log_level'] = level


def log(message, level, mode=default_mode, logfile=None):
    """ Adds a new log entry. Entry will only be created if log level is equal or above maximum log level.

    Args:
        message (str): The actual log message
        level (int): The log level. Use the LEVEL_X constants from this module.
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    if level > max_log_level:
        return None

    timestamp = datetime.now().strftime("%y.%m.%d-%H:%M:%S")
    level_string = get_level_string(level)
    log_msg = timestamp + ": [" + level_string + "] " + message

    if mode == MODE_PRINT:
        print(log_msg)
    elif mode == MODE_LOGFILE:
        if logfile is None:
            raise FileNotFoundError("File " + logfile + " was not found.")
        if logfile in file_pointers:
            f = file_pointers[logfile]
        else:
            f = open(logfile)
            file_pointers[logfile] = f
        f.write(log_msg)


def error(message, mode=default_mode, logfile=None):
    """ Adds a new log entry with ERROR level.

    Args:
        message (str): The actual log message
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    log(message, LEVEL_ERROR, mode=mode, logfile=logfile)


def warning(message, mode=default_mode, logfile=None):
    """ Adds a new log entry with WARNING level.

    The message will only be logged if maximum log level is at least at WARNING.

    Args:
        message (str): The actual log message
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    log(message, LEVEL_WARNING, mode=mode, logfile=logfile)


def info(message, mode=default_mode, logfile=None):
    """ Adds a new log entry with INFO level.

    The message will only be logged if maximum log level is at least at INFO.

    Args:
        message (str): The actual log message
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    log(message, LEVEL_INFO, mode=mode, logfile=logfile)


def debug(message, mode=default_mode, logfile=None):
    """ Adds a new log entry with DEBUG level.

    The message will only be logged if maximum log level is at least at DEBUG.

    Args:
        message (str): The actual log message
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    log(message, LEVEL_DEBUG, mode=mode, logfile=logfile)


def get_level_string(level):
    if level == LEVEL_ERROR:
        return "Error"
    if level == LEVEL_WARNING:
        return "Warning"
    if level == LEVEL_INFO:
        return "Info"
    if level == LEVEL_DEBUG:
        return "Debug"
