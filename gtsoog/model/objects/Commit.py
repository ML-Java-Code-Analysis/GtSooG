from model.objects.Repository import Repository
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from model.objects.Base import Base

Base = Base().base


class Commit(Base):
    __tablename__ = 'Commit'

    id = Column(Integer, primary_key=True)
    repository = relationship(Repository)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
