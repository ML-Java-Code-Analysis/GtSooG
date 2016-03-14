from sqlalchemy import Column, String, Integer
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base

Base = Base().base


class Issue(Base):
    __tablename__ = 'issue'

    id = Column(Integer, primary_key=True)
    issue_tracking_id = Column(Integer, ForeignKey("issueTracking.id"))
    # commit = relationship("Commit")
    type = Column(String, nullable=False)
