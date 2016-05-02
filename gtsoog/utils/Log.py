# coding=utf-8
from datetime import datetime


MODE_PRINT = 0
MODE_LOGFILE = 1
MODE_BOTH = 2

LEVEL_ERROR = 0
LEVEL_WARNING = 1
LEVEL_INFO = 2
LEVEL_DEBUG = 3

default_mode = MODE_PRINT
default_logfile = "log.txt"
main_logfile = default_logfile
file_pointers = {}
max_log_level = LEVEL_DEBUG


def config():
    """ Configures the logging behaviour according to Config.py"""
    from utils import Config
    if Config.log_level:
        log_level_str = Config.log_level
        if log_level_str.upper() == 'ERROR':
            set_min_log_level(LEVEL_ERROR)
        elif log_level_str.upper() == 'WARNING':
            set_min_log_level(LEVEL_WARNING)
        elif log_level_str.upper() == 'INFO':
            set_min_log_level(LEVEL_INFO)
        elif log_level_str.upper() == 'DEBUG':
            set_min_log_level(LEVEL_DEBUG)
    else:
        set_min_log_level(max_log_level)

    global main_logfile
    global default_logfile
    if Config.log_file:
        main_logfile = Config.log_file
    else:
        main_logfile = default_logfile

    global default_mode
    if Config.log_mode:
        log_mode_str = Config.log_mode
        if log_mode_str.upper() == 'PRINT':
            default_mode = MODE_PRINT
        elif log_mode_str.upper() == 'LOGFILE':
            default_mode = MODE_LOGFILE
        elif log_mode_str.upper() == 'BOTH':
            default_mode = MODE_BOTH
    else:
        default_mode = MODE_PRINT



def set_min_log_level(level):
    """ Sets the maximum level of logs which actually should be logged.

    Args:
        level (int): The log level. Use the LEVEL_X constants from this module.
    """
    globals()['max_log_level'] = level


def log(message, level, mode=None, logfile=None):
    """ Adds a new log entry. Entry will only be created if log level is equal or above maximum log level.

    Args:
        message (str): The actual log message
        level (int): The log level. Use the LEVEL_X constants from this module.
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    if level > max_log_level:
        return None
    if not mode:
        mode = default_mode

    timestamp = datetime.now().strftime("%y.%m.%d-%H:%M:%S")
    level_string = get_level_string(level)
    log_msg = timestamp + ": [" + level_string + "] " + message

    if mode == MODE_PRINT or mode == MODE_BOTH:
        print(log_msg)
    if mode == MODE_LOGFILE or mode == MODE_BOTH:
        if logfile is None:
            global main_logfile
            logfile = main_logfile
        if logfile in file_pointers:
            f = file_pointers[logfile]
        else:
            f = open(logfile, 'w')
            file_pointers[logfile] = f
        f.write(log_msg + "\n")


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


def info(message, mode=None, logfile=None):
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
