from json.decoder import JSONDecodeError

import requests

import Log


class GitHub(object):

    BUG_LABELS = ('bug', 'defect')

    def __init__(self, domain, owner, repo, use_https=True, user=None, password=None, bug_label_names=BUG_LABELS):
        self.domain = domain
        self.owner = owner
        self.repo = repo
        self.use_https = use_https
        self.user = user
        self.password = password
        self.bug_label_names = bug_label_names

    def get_protocol_prefix(self):
        if self.use_https:
            return 'https://'
        return 'http://'

    def get_issue_url(self, number):
        return '{protocol}{domain}/api/v3/repos/{owner}/{repo}/issues/{number}'.format(
            protocol=self.get_protocol_prefix(),
            domain=self.domain,
            owner=self.owner,
            repo=self.repo,
            number=number
        )

    def __is_bug_label(self, label_name):
        """ Returns true if the label seems to indicate a bug

        Args:
            label_name (str): Name of the label
        """
        label_name = label_name.lower()
        for bug_label_name in self.bug_label_names:
            if bug_label_name in label_name:
                return True
        return False

    def get_issue(self, number):
        url = self.get_issue_url(number)
        auth = None
        if self.user and self.password:
            auth = (self.user, self.password)

        Log.log('Retrieving Issue Nr. ' + str(number) + ' via ' + url, Log.LEVEL_DEBUG)
        response = requests.get(url, auth=auth)

        if not response.status_code == 200:
            message = 'Issue Nr. {number} could not be retrieved from Repository {repo}. Status Code: {status}'.format(
                number=number,
                repo=self.repo,
                status=response.status_code)
            Log.log(message, Log.LEVEL_WARNING)
            return None

        try:
            issue = response.json()
        except JSONDecodeError:
            message = 'Issue Nr. {number} from Repository {repo} contains invalid JSON'.format(
                number=number,
                repo=self.repo)
            Log.log(message, Log.LEVEL_WARNING)
            return None

        if 'number' not in issue or not str(issue['number']) == str(number) or 'labels' not in issue:
            message = 'Retrieved JSON for Issue Nr. {number} from Repository {repo} doesn\'t ' + \
                      'seem to represent an actual issue.'.format(
                          number=number,
                          repo=self.repo)
            Log.log(message, Log.LEVEL_WARNING)
            return None

        label_names = [label['name'] for label in issue['labels']]
        is_associated_with_bug = any([self.__is_bug_label(label_name) for label_name in label_names])

        info_message = 'Retrieved JSON for Issue Nr. {number} from Repository {repo}.'.format(
            number=number,
            repo=self.repo
        )
        if is_associated_with_bug:
            info_message += ' Seems to be a bug.'
        Log.log(info_message, Log.LEVEL_INFO)

        return issue