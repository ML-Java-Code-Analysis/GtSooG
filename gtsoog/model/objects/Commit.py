from sqlalchemy.sql.schema import ForeignKey

from sqlalchemy import Column, String, Integer, DateTime
from model.objects.Base import Base

Base = Base().base


class Commit(Base):
    __tablename__ = 'commit'

    id = Column(String, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repository.id'))
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
