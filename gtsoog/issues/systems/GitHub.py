from json.decoder import JSONDecodeError

import requests

from model.objects.Commit import Commit
from model.objects.Issue import Issue, TYPE_BUG, TYPE_ENHANCEMENT, TYPE_OTHER
from model.objects.IssueTracking import IssueTracking
from utils import Log


def retrieve(issue_tracking, commit, issue_nr, existing_issue=None):
    """

    Args:
        issue_tracking (IssueTracking): The issue tracking
        commit (Commit): The commit
        issue_nr (int|str): The issue number
        existing_issue (Issue): Optional. Provide if there exists already an issue in the DB.
    """
    issue_nr = str(issue_nr)
    assert issue_nr.isnumeric()

    Log.info("Analyzing Issue #" + issue_nr + " for Commit " + commit.id + \
             " from issue tracking with id " + str(issue_tracking.id))

    issue_url = get_issue_url(issue_tracking.url, issue_nr)

    auth = None
    if issue_tracking.username and issue_tracking.password:
        auth = (issue_tracking.username, issue_tracking.password)
    Log.debug("Retrieving Issue Nr. " + issue_nr + " via " + issue_url)
    response = requests.get(issue_url, auth=auth)

    if not response.status_code == 200:
        Log.error("Issue #" + issue_nr + " could not be retrieved from " + issue_url + \
                  ". Status Code: " + str(response.status_code))
        return None

    try:
        issue_json = response.json()
    except JSONDecodeError:
        Log.error("Issue #" + issue_nr + " retrieved from " + issue_url + " could not be parsed to JSON")
        return None

    # Check for some fields to determine wether the parsed data seems to be an issue
    if 'number' not in issue_json or not str(issue_json['number']) == issue_nr or 'labels' not in issue_json:
        Log.error("Retrieved JSON for Issue #" + issue_nr + " from " + issue_url + \
                  " doesn't seem to represent an actual issue.")
        return None

    # Determine type from labels
    label_names = [label['name'] for label in issue_json['labels']]
    issue_type = get_issue_type(label_names)
    Log.debug("Issue #" + issue_nr + " has following labels: " + str(label_names) + ". Resulting type: " + issue_type)

    if existing_issue:
        existing_issue.title = issue_json['title']
        existing_issue.type = issue_type
        return existing_issue
    else:
        return Issue(
            id=issue_nr,
            title=issue_json['title'],
            type=issue_type
        )


def get_issue_url(api_url, issue_nr):
    """ Returns the url to access an issue resource.

    Args:
        api_url (str): The url to the git API. E.g. "github.engineering.zhaw.ch/api/v3/repos/mekesyac/LED-Cube-Prototyper"
        issue_nr (int|str): The issue number
    """
    return 'https://{url}/issues/{number}'.format(
        url=api_url,
        number=issue_nr
    )


def get_issue_type(label_names):
    """ Returns the type of an issue depending on it's labels """
    issue_types = [get_label_type(label_name) for label_name in label_names]

    # Choose one Issue type. Bug has highest priority
    if TYPE_BUG in issue_types:
        return TYPE_BUG
    elif TYPE_ENHANCEMENT in issue_types:
        return TYPE_ENHANCEMENT
    else:
        return TYPE_OTHER


label_keywords = {
    TYPE_BUG: ['bug', 'defect'],
    TYPE_ENHANCEMENT: ['enhancement', 'feature']
}


def get_label_type(label_name):
    """ Returns the issue-type which a label is associated with.

    Args:
        label_name (str): Name of the label
    """
    label_name = label_name.lower()
    for label_type, keywords in label_keywords.items():
        for keyword in keywords:
            if keyword in label_name:
                return label_type
    return None
