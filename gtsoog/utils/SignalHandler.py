import signal
from utils import Log

shutdown = False

def signal_handler(signal, frame):
        Log.info("Received shutdown signal doing graceful shutdown")
        shutdown=True

def register_signal_handler():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)