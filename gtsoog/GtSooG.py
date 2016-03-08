# Hauptfile, dieses ruft man dann auf
from gtsoog import GitCollector
from gtsoog import GitStatistics

def main():
    REPO_PATH = "P:\Studium\FS2016\BA\GitHubProjects\liferay-portal"
    #GitCollector.collectData(REPO_PATH)
    GitStatistics.stats(REPO_PATH)

main()