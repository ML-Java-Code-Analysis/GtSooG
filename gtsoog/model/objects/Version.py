from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base

Base = Base().base


class Version(Base):
    __tablename__ = 'version'

    id = Column(Integer, primary_key=True)
    file_id = Column(String, ForeignKey("file.id"))
    commit_id = Column(String, ForeignKey("commit.id"))
    lines_changed = Column(Integer, nullable=False)
    lines_added = Column(Integer, nullable=False)
    lines_deleted = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)