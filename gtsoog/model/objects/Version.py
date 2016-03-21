from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql.schema import ForeignKey, ForeignKeyConstraint

from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class Version(Base):
    __tablename__ = 'version'

    id = Column(Integer, primary_key=True)

    #file_id = Column(String, ForeignKey("file.id"))
    file_id = Column(String)
    file_timestamp = Column(DateTime)
    __table_args__ = (ForeignKeyConstraint([file_id, file_timestamp],
                                           ["file.id", "file.timestamp"]),
                      {})

    commit_id = Column(String, ForeignKey("commit.id"))
    lines_changed = Column(Integer, nullable=False)
    lines_added = Column(Integer, nullable=False)
    lines_deleted = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
