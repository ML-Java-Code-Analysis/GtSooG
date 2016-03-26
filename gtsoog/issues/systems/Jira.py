from json.decoder import JSONDecodeError

from model.objects.Issue import Issue, TYPE_BUG, TYPE_ENHANCEMENT, TYPE_OTHER
from model.objects.IssueTracking import IssueTracking, TYPE_JIRA
from utils import Log
import requests
from requests.auth import HTTPBasicAuth


def retrieve(issue_tracking, issue_id, existing_issue=None):
    """ Retrieves an issue from Jira

    Args:
        issue_tracking (IssueTracking): The issue tracking. Must be of type 'Jira'
        issue_id (int|str): The issue number.
        existing_issue (Issue): Optional. Provide if there exists already an issue in the DB.

    Returns:
        Issue: The retrieved issue or None if nothing was found.
    """

    issue_id = str(issue_id)
    assert issue_tracking.type == TYPE_JIRA, "This module is only compatible with GitHub-IssueTrackers"
    if existing_issue:
        assert existing_issue.id == issue_id, "The existing issue provided does not have the correct id"

    Log.info("Analyzing Issue " + issue_id + " from JIRA issue tracking with id " + str(issue_tracking.id))

    issue_url = get_issue_url(issue_tracking.url, issue_id)
    msg = "Requesting Issue Nr. " + issue_id + " from " + issue_url
    auth = None
    if issue_tracking.username and issue_tracking.password:
        auth = HTTPBasicAuth(issue_tracking.username, issue_tracking.password)
        msg += " using basic auth."
    Log.debug(msg)
    response = requests.get(issue_url, auth=auth)

    if not response.status_code == 200:
        Log.error("Issue " + issue_id + " could not be retrieved from " + issue_url + \
                  ". Status Code: " + str(response.status_code))
        return None

    try:
        issue_json = response.json()
    except JSONDecodeError:
        Log.error("Issue " + issue_id + " retrieved from " + issue_url + " could not be parsed to JSON")
        return None

    # Check for some fields to determine wether the parsed data seems to be an issue
    if 'key' not in issue_json or not str(issue_json['key']) == issue_id \
            or 'fields' not in issue_json or 'issuetype' not in issue_json['fields']:
        Log.error("Retrieved JSON for Issue " + issue_id + " from " + issue_url + \
                  " doesn't seem to represent an actual issue.")
        return None

    # Determine type from issuetype
    issue_type_name = issue_json['fields']['issuetype']['name']
    issue_type = get_issue_type(issue_type_name)
    Log.debug("Issue " + issue_id + " seems to be a " + issue_type)

    title = issue_json['fields']['summary']
    if existing_issue:
        existing_issue.title = title
        existing_issue.type = issue_type
        return existing_issue
    else:
        return Issue(
            id=issue_id,
            title=title,
            type=issue_type
        )


def get_issue_url(api_url, issue_id):
    """ Returns the url to access an issue resource.

    Args:
        api_url (str): The url to the git API. E.g. "issues.apache.org/jira/rest/api/latest"
        issue_id (str): The issue id

    Returns:
        str: The url to access the issue resource via REST
    """
    return 'https://{url}/issue/{id}'.format(
        url=api_url,
        id=issue_id
    )


def get_issue_type(issue_type_name):
    """ Returns the GtSooG Issue Type for a JIRA issue type

    Args:
        issue_type_name: The name of the JIRA issue type

    Returns:
        str: An Issue Type (A TYPE_X string Constant from model.objects.Issue)
    """
    normalized_name = str(issue_type_name).lower()
    if normalized_name == 'bug':
        return TYPE_BUG
    elif 'feature' in normalized_name or normalized_name == 'improvement':
        return TYPE_ENHANCEMENT
    else:
        return TYPE_OTHER
