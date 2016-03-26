from sqlalchemy import Column, String, Integer
from sqlalchemy.sql.schema import ForeignKey

from model.objects.Base import Base

Base = Base().base

TYPE_ADDED = 1
TYPE_DELETED = 0

# noinspection PyClassHasNoInit
class Line(Base):
    __tablename__ = 'line'

    id = Column(Integer, primary_key=True)
    line = Column(String(3000))
    line_number = Column(Integer)
    type = Column(Integer)
    version_id = Column(String(36), ForeignKey("version.id"))
