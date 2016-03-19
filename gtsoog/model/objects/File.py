from sqlalchemy.sql.schema import ForeignKey

from sqlalchemy import Column, String, Integer
from model.objects.Base import Base

Base = Base().base


# noinspection PyClassHasNoInit
class File(Base):
    __tablename__ = 'file'

    id = Column(String, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repository.id"))
    language = Column(String, nullable=False)
