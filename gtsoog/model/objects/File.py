from sqlalchemy.sql.schema import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime
from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class File(Base):
    __tablename__ = 'file'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)

    precursor_file = relationship("File")
    precursor_file_id = Column(String)
    precursor_file_timestamp = Column(DateTime)
    __table_args__ = (ForeignKeyConstraint([precursor_file_id, precursor_file_timestamp],
                                          [id, timestamp]),
                      {})
    repository_id = Column(Integer, ForeignKey("repository.id"))
    language = Column(String, nullable=False)
