from sqlalchemy.sql.schema import ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime
from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class Commit(Base):
    __tablename__ = 'commit'

    association_table = Table('commit_issue', Base.metadata,
                              Column('commit_id', String(40), ForeignKey('commit.id')),
                              Column('issue_id', Integer, ForeignKey('issue.id'))
                              )

    id = Column(String(40), primary_key=True)
    repository_id = Column(Integer, ForeignKey('repository.id'))
    message = Column(String(3000), nullable=False)   # TODO: Is length enough?
    timestamp = Column(DateTime, nullable=False)
    issues = relationship("Issue", secondary=association_table, back_populates="commits")
