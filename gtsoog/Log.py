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
min_log_level = LEVEL_DEBUG


def set_min_log_level(level):
    """ Sets the minimum level of logs which actually should be logged.

    Args:
        level (int): The log level. Use the LEVEL_X constants from this module.
    """
    globals()['log_level'] = level


def log(message, level, mode=default_mode, logfile=None):
    """ Adds a new log entry. Entry will only be created if log level is equal or above minimum log level.

    Args:
        message (str): The actual log message
        level (int): The log level. Use the LEVEL_X constants from this module.
        mode (int): Optional. The logging mode. Use the MODE_X constants from this module.
        logfile (str): Optional. The filepath, where this message should be logged to.
    """
    if level < min_log_level:
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


def get_level_string(level):
    if level == LEVEL_ERROR:
        return "Error"
    if level == LEVEL_WARNING:
        return "Warning"
    if level == LEVEL_INFO:
        return "Info"
    if level == LEVEL_DEBUG:
        return "Debug"
