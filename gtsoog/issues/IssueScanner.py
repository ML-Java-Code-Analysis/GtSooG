import re

from sqlalchemy.orm.exc import NoResultFound

from issues.systems import GitHub
from model import DB
from model.objects.Issue import Issue
from model.objects.IssueTracking import IssueTracking, TYPE_GITHUB
from utils import Log

# TODO: Relationship typ bestimmen für commit <-> issue: Associated, Closes, etc.

__issue_cache = {}


def scan_for_repository(repository_id):
    """ Scans the issue tracking of a repository in the DB and assigns issues to commits.

    Iterates through all recorded commits of this repository, checks their commit message for issue references,
    trys to retrieve those issues from the associated issue tracking system and saves them in the DB.

    Args:
        repository_id (int): The id of the repository to scan.
    """
    reset_issue_cache()

    # get issue tracking object
    Log.info("Retrieving IssueTracking for Repository with id " + str(repository_id))
    db_session = DB.create_session()
    query = db_session.query(IssueTracking).filter(IssueTracking.repository_id == int(repository_id))
    try:
        issue_tracking = query.one()
    except NoResultFound:
        Log.error("No IssueTracking-Entry found for Repository with id " + str(repository_id))
        db_session.close()
        return
    Log.debug("IssueTracking found. Type: " + str(issue_tracking.type))

    if issue_tracking.type == TYPE_GITHUB:
        retrieve = GitHub.retrieve
        extract_pattern = '#[0-9]+'
        transform = lambda x: x[1:]
    else:
        Log.error("No Implementation found for IssueTracking-Type '" + str(issue_tracking.type) + "'")
        db_session.close()
        return

    repository = issue_tracking.repository
    for commit in repository.commits:
        issue_ids = extract_issue_ids(commit.message, extract_pattern, transform=transform)
        for issue_id in issue_ids:
            process_issue(issue_tracking, commit, issue_id, retrieve, db_session)

    Log.info("Issue Analysis completed")
    db_session.close()
    reset_issue_cache()


def process_issue(issue_tracking, commit, issue_id, retrieve_function, db_session):
    """ Retrieves and persists an issue for a commit.

    Args:
        issue_tracking (IssueTracking): The issue tracking for this commit/issue
        commit (Commit): The commit which this issue is associated with.
        issue_id (str): The id, by which the issue is identified in its issue tracking.
        retrieve_function (FunctionType): A function to retrieve issues from their tracking system. One of the retrieve-
            functions from the issues.systems modules.
        db_session (Session): The db session to use.
    """
    issue_string = "Issue " + str(issue_id) + " from IssueTracking " + str(issue_tracking.id) + \
                   " for commit " + commit.id
    Log.debug("Processing " + issue_string)

    existing_issue = get_existing_issue(db_session, issue_tracking, issue_id)
    issue = retrieve_function(issue_tracking, issue_id, existing_issue=existing_issue)
    if not issue:
        Log.warning(issue_string + " could not be retrieved! Skipping this issue.")
        return
    update_issue_cache(issue)
    Log.debug(issue_string + " was successfully retrieved. Will be persisted now.")
    issue_tracking.issues.append(issue)
    commit.issues.append(issue)

    db_session.commit()
    Log.debug(issue_string + " was successfully processed and persisted.")


def extract_issue_ids(commit_message, search_pattern, transform=None):
    """ Extract issue ids from a commit message

    Args:
        commit_message (str): The full commit message
        search_pattern (str): A regular expression to match issue IDs
        transform (function): Optional. A function to transform the extracted issues, e.g. to make "1234" from "#1234"

    Returns:

    """
    result = re.findall(search_pattern, commit_message)
    if transform:
        result = [transform(search_result) for search_result in result]
    return result


def get_existing_issue(db_session, issue_tracking, issue_id):
    """ Checks if an issue already exists in the cache or DB and returns it.

    Args:
        db_session: The DB session to use.
        issue_tracking: The issue tracking system the issue belongs to
        issue_id: the issue id

    Returns:
        Issue: The issue or if nothing was found None.
    """
    if issue_id in __issue_cache:
        return __issue_cache[issue_id]
    query = db_session.query(Issue).filter(Issue.issue_tracking_id == issue_tracking.id, Issue.id == str(issue_id))
    issue = query.one_or_none()
    __issue_cache[issue_id] = issue
    return issue


def update_issue_cache(issue):
    """ Chache an issue. Should be called every time an issue was retrieved.

    Args:
        issue (Issue): The issue to cache.
    """
    __issue_cache[issue.id] = issue


def reset_issue_cache():
    """ Empties the issue chache."""
    global __issue_cache
    __issue_cache = {}
