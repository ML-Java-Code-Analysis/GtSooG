# coding=utf-8
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class Version(Base):
    __tablename__ = 'version'

    id = Column(String(36), primary_key=True)

    file_id = Column(String(36), ForeignKey('file.id'))
    commit_id = Column(String(40), ForeignKey("commit.id"))
    lines_added = Column(Integer, nullable=False)
    lines_deleted = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
    lines = relationship("Line")
