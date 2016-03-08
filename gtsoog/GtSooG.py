# Hauptfile, dieses ruft man dann auf
from src import GitCollector
from src import GitStatistics

def main():
    REPO_PATH = "P:\Studium\FS2016\BA\GitHubProjects\liferay-portal"
    #GitCollector.collectData(REPO_PATH)
    GitStatistics.stats(REPO_PATH)

main()