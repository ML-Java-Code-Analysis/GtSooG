from model.objects.Repository import Repository
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from model.objects.Base import Base

Base = Base().base


class File(Base):
    __tablename__ = 'File'

    id = Column(Integer, primary_key=True)
    repository = relationship(Repository)
    language = Column(String, nullable=False)
