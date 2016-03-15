from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from model.objects.Base import Base
from model.objects.File import File

Base = Base().base


class Repository(Base):
    __tablename__ = 'repository'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    url = Column(String)
    issueTracking = relationship("IssueTracking", uselist=False, back_populates="repository")
    commits = relationship("Commit")
    files = relationship(File)
