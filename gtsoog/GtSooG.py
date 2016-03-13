# Hauptfile, dieses ruft man dann auf
from gtsoog import GitCollector
from gtsoog.RepositoryMiner import RepositoryMiner


def main():
    #REPO_PATH = "P:\Studium\FS2016\BA\GitHubProjects\liferay-portal"
    #GitCollector.collectData(REPO_PATH)
    #GitStatistics.stats(REPO_PATH)


    RepositoryMiner(r"P:\Studium\FS2016\BA\GitHubProjects\LED-Cube-Prototyper")
    #RepositoryMiner(r"P:\Studium\FS2016\BA\GitHubProjects\liferay-portal")

main()