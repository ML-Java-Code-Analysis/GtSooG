# coding=utf-8
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base
from model.objects.CommitIssue import CommitIssue

Base = Base().base


# noinspection PyClassHasNoInit
class Commit(Base):
    __tablename__ = 'commit'

    id = Column(String(40), primary_key=True)
    repository_id = Column(Integer, ForeignKey('repository.id'))
    message = Column(String(3000), nullable=False)  # TODO: Is length enough?
    timestamp = Column(DateTime, nullable=False)
    issues = relationship("Issue", secondary=CommitIssue.__table__, back_populates="commits")
