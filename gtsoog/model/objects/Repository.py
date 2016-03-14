from sqlalchemy import Column, String, Integer

from model.objects.Base import Base

Base = Base().base


class Repository(Base):
    __tablename__ = 'repository'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String)
    issue_tracking = Column(String)
