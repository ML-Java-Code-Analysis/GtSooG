from sqlalchemy.sql.schema import ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime
from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class File(Base):
    __tablename__ = 'file'

    id = Column(String(36), primary_key=True)
    precursor_file_id = Column(String(36), ForeignKey('file.id'))
    precursor_file = relationship("File")
    repository_id = Column(Integer, ForeignKey("repository.id"))
    path = Column(String(500), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    language = Column(String(20), nullable=False)

    __table_args__ = (UniqueConstraint('path', 'timestamp'), )
