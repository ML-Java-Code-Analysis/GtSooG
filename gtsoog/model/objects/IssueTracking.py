from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from model.objects.Base import Base
from model.objects.Repository import Repository

Base = Base().base


class IssueTracking(Base):
    __tablename__ = "IssueTracking"

    id = Column(Integer, primary_key=True)
    repository = relationship(Repository)
    type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    username = Column(String)
    password = Column(String)
