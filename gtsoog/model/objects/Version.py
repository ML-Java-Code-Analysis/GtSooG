from model.objects.File import File
from model.objects.Commit import Commit
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from model.objects.Base import Base

Base = Base().base


class Version(Base):
    __tablename__ = 'Version'

    id = Column(Integer, primary_key=True)
    file = relationship(File)
    commit = relationship(Commit)
    lines_changed = Column(Integer, nullable=False)
    lines_added = Column(Integer, nullable=False)
    lines_deleted = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
