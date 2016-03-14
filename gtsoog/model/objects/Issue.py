from model.objects.Repository import Repository
from model.objects.Commit import Commit
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from model.objects.Base import Base

Base = Base().base


class Issue(Base):
    __tablename__ = 'Issue'

    id = Column(Integer, primary_key=True)
    repository = relationship(Repository)
    commit = relationship(Commit)
    type = Column(String, nullable=False)
