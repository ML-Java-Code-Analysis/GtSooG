# coding=utf-8
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint

from model.objects.Base import Base

Base = Base().base

MAX_PATH_LENGTH = 500

# noinspection PyClassHasNoInit
class File(Base):
    __tablename__ = 'file'

    id = Column(String(36), primary_key=True)
    precursor_file_id = Column(String(36), ForeignKey('file.id'))
    precursor_file = relationship("File")
    repository_id = Column(Integer, ForeignKey("repository.id"))
    path = Column(String(MAX_PATH_LENGTH+1), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    language = Column(String(20))

    __table_args__ = (UniqueConstraint('repository_id', 'path', 'timestamp'), )
