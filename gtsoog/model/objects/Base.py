from sqlalchemy.ext.declarative import declarative_base

from utils.Borg import Borg


class Base(Borg):
    def __init__(self):
        Borg.__init__(self)
        if not hasattr(self, 'base'):
            self.base = declarative_base()
