# Hauptfile, dieses ruft man dann auf
from src import GitCollector


def main():
    REPO_PATH = "C:\\Users\\ymeke\\PycharmProjects\\LED-Cube-Prototyper"
    GitCollector.collectData(REPO_PATH)

main()