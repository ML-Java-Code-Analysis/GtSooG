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


def log(message, level, mode=default_mode, logfile=None):
    """

    Args:
        message (str):
        level (int):
        mode (int):
        logfile (str):
    """
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
