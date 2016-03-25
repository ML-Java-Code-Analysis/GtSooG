import argparse
import configparser

#Config Parameters

repository_url = None
database_engine = None
database_file = None
database_name = None
database_user = None
database_user_password = None
database_host = None
database_port = None
number_of_repository_miner_threads = None


DIALECT_SQLITE = 'sqlite'
DIALECT_MYSQL = 'mysql'
DIALECT_POSTGRES = 'postgresql'


def argument_parser():
    parser = argparse.ArgumentParser(description='GtSoog - git data miner')

    #CLI Parameters
    parser.add_argument('-f', action="store", required=True, dest="config_file", help='Specify config file')

    args = parser.parse_args()

    config_file = args.config_file
    config_parser(config_file)


def config_parser(config_file):
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)

        try:
            global number_of_repository_miner_threads
            number_of_repository_miner_threads = config['RUNTIME']['number_of_repository_miner_threads']
        except KeyError:
            number_of_repository_miner_threads = 1

        try:
            global database_engine
            database_engine = config['DATABASE']['database_engine']
        except KeyError:
            raise EnvironmentError('Database engine not specified in config file')

        try:
            global database_file
            database_file = config['DATABASE']['database_file']
        except KeyError:
            if database_engine == DIALECT_SQLITE:
                raise EnvironmentError('SQLite database file is missing in config file')

        try:
            global database_name
            database_name = config['DATABASE']['database_name']
        except KeyError:
            raise EnvironmentError('Database name is missing in config file')

        try:
            global database_user
            database_user = config['DATABASE']['database_user']
        except KeyError:
            if (database_engine == DIALECT_MYSQL) or (database_engine == DIALECT_POSTGRES):
                raise EnvironmentError('Database user is missing in config file')

        try:
            global database_user_password
            database_user_password = config['DATABASE']['database_user_password']
        except KeyError:
            if (database_engine == DIALECT_MYSQL) or (database_engine == DIALECT_POSTGRES):
                raise EnvironmentError('Database user password is missing in config file')

        try:
            global database_host
            database_host = config['DATABASE']['database_host']
        except KeyError:
            if (database_engine == DIALECT_MYSQL) or (database_engine == DIALECT_POSTGRES):
                raise EnvironmentError('Database host is missing in config file')

        try:
            global database_port
            database_port = config['DATABASE']['database_port']
        except KeyError:
            if (database_engine == DIALECT_MYSQL) or (database_engine == DIALECT_POSTGRES):
                raise EnvironmentError('Database port is missing in config file')

        try:
            global repository_url
            repository_url = config['GIT']['repository_url']
        except KeyError:
            raise EnvironmentError('Repository URL is missing in config file')