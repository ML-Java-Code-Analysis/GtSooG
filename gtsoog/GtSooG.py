from model import DB
from repository.RepositoryMiner import RepositoryMiner


def main():
    DB.create_db()
    repository_url = r"C:\Users\ymeke\PycharmProjects\LED-Cube-Prototyper"

    RepositoryMiner(repository_url)


main()
