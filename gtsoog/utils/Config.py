# coding=utf-8
import argparse
import configparser
import ast
from model.objects import IssueTracking
from utils import Log

# Config parameters
repository_path = None
issue_tracking_system = None
issue_tracking_url = None
issue_tracking_username = None
issue_tracking_password = None
database_dialect = None
database_name = None
database_user = None
database_user_password = None
database_host = None
database_port = None
number_of_threads = None
number_of_database_sessions = None
programming_languages = []
issue_scanner_issue_id_regex = None
write_lines_in_database = None

DIALECT_SQLITE = 'sqlite'
DIALECT_MYSQL = 'mysql'
DIALECT_POSTGRES = 'postgresql'


def parse_arguments():
    """ Parses the provided command line arguments.

    Returns:
        A collection of argument values.
    """
    parser = argparse.ArgumentParser(description='GtSoog - git data miner')

    # CLI parameters
    parser.add_argument('-f', action="store", required=True, dest="config_file", help='Specify config file')

    return parser.parse_args()


def parse_config(config_file):
    """ Reads the config file and initializes the config variables.

    Args:
        config_file (str): The relative filepath to the config file.
    """
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)

        global database_dialect

        # DATABASE Config
        try:
            database_dialect = config['DATABASE']['database_engine']
        except KeyError:
            raise EnvironmentError('Database engine not specified in config file')

        try:
            global database_name
            database_name = config['DATABASE']['database_name']
        except KeyError:
            raise EnvironmentError('Database name is missing in config file')

        try:
            global database_user
            database_user = config['DATABASE']['database_user']
        except KeyError:
            if (database_dialect == str(DIALECT_MYSQL)) or (database_dialect == str(DIALECT_POSTGRES)):
                raise EnvironmentError('Database user is missing in config file')

        try:
            global database_user_password
            database_user_password = config['DATABASE']['database_user_password']
        except KeyError:
            if (database_dialect == str(DIALECT_MYSQL)) or (database_dialect == str(DIALECT_POSTGRES)):
                raise EnvironmentError('Database user password is missing in config file')

        try:
            global database_host
            database_host = config['DATABASE']['database_host']
        except KeyError:
            if (database_dialect == str(DIALECT_MYSQL)) or (database_dialect == str(DIALECT_POSTGRES)):
                raise EnvironmentError('Database host is missing in config file')

        try:
            global database_port
            database_port = int(config['DATABASE']['database_port'])
        except KeyError:
            if (database_dialect == str(DIALECT_MYSQL)) or (database_dialect == str(DIALECT_POSTGRES)):
                raise EnvironmentError('Database port is missing in config file')

        # REPOSITORY Config
        try:
            global repository_path
            repository_path = config['REPOSITORY']['repository_path']
        except KeyError:
            raise EnvironmentError('Repository Path is missing in config file')

        try:
            global issue_tracking_system
            issue_tracking_system = config['REPOSITORY']['issue_tracking_system']
            if (issue_tracking_system != str(IssueTracking.TYPE_GITHUB)) and (
                    issue_tracking_system != str(IssueTracking.TYPE_JIRA)):
                raise EnvironmentError('Unsupported issue tracking system. Use GITHUB or JIRA')
        except KeyError:
            raise EnvironmentError('Issue Tracking System is missing in config file')

        try:
            global issue_tracking_url
            issue_tracking_url = config['REPOSITORY']['issue_tracking_url']
        except KeyError:
            raise EnvironmentError('IssueTracking URL is missing in config file')

        global issue_tracking_username
        if 'issue_tracking_username' in config['REPOSITORY']:
            issue_tracking_username = config['REPOSITORY']['issue_tracking_username']

        global issue_tracking_password
        if 'issue_tracking_password' in config['REPOSITORY']:
            issue_tracking_password = config['REPOSITORY']['issue_tracking_password']

        # REPOSITORYMINER Config
        try:
            global number_of_threads
            Log.warning("Number of threads is not implemented and will be ignored.")
            if database_dialect == str(DIALECT_SQLITE):
                Log.warning("Using SQLite as database engine: Only one thread supported. Processing might be slow.")
                number_of_threads = 1
            else:
                number_of_threads = int(config['REPOSITORYMINER']['number_of_threads'])
        except KeyError:
            number_of_threads = 1

        try:
            global number_of_database_sessions
            Log.warning("Number of db sessions is not implemented and will be ignored.")
            if database_dialect == str(DIALECT_SQLITE):
                Log.warning(
                    "Using SQLite as database engine: Only one database session supported. Processing might be slow.")
                number_of_database_sessions = 1
            else:
                number_of_database_sessions = int(config['REPOSITORYMINER']['number_of_database_sessions'])
        except KeyError:
            number_of_database_sessions = 1

        try:
            global write_lines_in_database
            write_lines_in_database = ast.literal_eval(config['REPOSITORYMINER']['write_lines_in_database'])
        except KeyError:
            write_lines_in_database = True

        # PROGRAMMINGLANGUAGES config
        try:
            global programming_languages
            for item in config.items('PROGRAMMINGLANGUAGES'):
                programming_languages.append(item)
        except KeyError:
            raise EnvironmentError('Programming languages not specified in config file')

        # ISSUESCANNER config
        global issue_scanner_issue_id_regex
        if 'ISSUESCANNER' in config and 'issue_id_regex' in config['ISSUESCANNER']:
            issue_scanner_issue_id_regex = config['ISSUESCANNER']['issue_id_regex']
