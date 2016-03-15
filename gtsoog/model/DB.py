from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.objects.Base import Base

__engine = None


def __get_engine():
    global __engine
    if __engine is None:
        __engine = create_engine('sqlite:///gtsoog.db')
    return __engine


# noinspection PyUnresolvedReferences
def create_db():
    from model.objects.IssueTracking import IssueTracking
    from model.objects.Repository import Repository
    from model.objects.Commit import Commit
    from model.objects.File import File
    from model.objects.Issue import Issue
    from model.objects.Version import Version
    engine = __get_engine()
    Base().base.metadata.create_all(engine)


def create_session():
    engine = __get_engine()
    session = sessionmaker()
    session.configure(bind=engine)

    return session()
