from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base
from model.objects.Commit import Commit

Base = Base().base


class Issue(Base):
    __tablename__ = 'issue'

    id = Column(Integer, primary_key=True)
    issue_tracking_id = Column(Integer, ForeignKey("issueTracking.id"))
    title = Column(String)
    commits = relationship("Commit", secondary=Commit.association_table, back_populates="issues")
    type = Column(String, nullable=False)
