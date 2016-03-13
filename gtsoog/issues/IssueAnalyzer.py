from gtsoog.issues.interfaces.GitHub import GitHub
import re

# TODO: make usable lol
# TODO: implement caching for repeated issues


def extract_issue_ids(commit_message, search_pattern, extract_pattern=None):
    result = re.findall(search_pattern, commit_message)
    if extract_pattern:
        result = [re.search(extract_pattern, search_result).group() for search_result in result]
    return result

# These are just tests:

# ==== dotCMS core ====
dotcms_issue_interface = GitHub('api.github.com', 'dotCMS', 'core')

# Commit: bd867bb7ac6ca098adc95081a11f148aeba98307 (Bug)
dotcms_commit_message_1 = """Fixes #8424 : Escape file name when downloading."""
# Commit: afe92be9c05a9018a4819694ebe121044b80c5c1 (Bug)
dotcms_commit_message_2 = """Fixes #8586 : Fixing casting problem when instantiating the Host class."""
# Commit: 613594c9e4ff77a9c848d4d71483f1891d3d516e (Bug)
dotcms_commit_message_3 = """proposed fix #8238"""
# Commit: bb5449da3be2e245a5d8f6323ff1220db6b63126 (Bug)
dotcms_commit_message_4 = """fixes #7793 : Unable to edit child folder name """
# Commit: 292e16e259523cbcc67580d56fd97fa7d63b10ef (No Bug)
dotcms_commit_message_5 = """#7880 added method """
# Commit: 0a04222e3557b0289e476b021f67fad89e3d1896 (No Bug)
dotcms_commit_message_6 = """closes #6584"""
# Commit: 9567d374492a8f1dc8946b23b7cc887f6deccded (No Issue)
dotcms_commit_message_7 = """card762: 4 spaces instead tab """
# Commit: 31270a31569daf77a5e8d90b037f41a129a7137a (No Issue)
dotcms_commit_message_8 = """Update RulePermissionableUtil.java """

dotcms_commit_messages = [
    dotcms_commit_message_1,
    dotcms_commit_message_2,
    dotcms_commit_message_3,
    dotcms_commit_message_4,
    dotcms_commit_message_5,
    dotcms_commit_message_6,
    dotcms_commit_message_7,
    dotcms_commit_message_8
]

search_pattern = '#[0-9]+'
extract_pattern = '[0-9]+'
for commit_message in dotcms_commit_messages:
    issue_numbers = extract_issue_ids(commit_message, search_pattern, extract_pattern)
    if len(issue_numbers) == 0:
        print("No issue number found.")
    else:
        for issue_number in issue_numbers:
            dotcms_issue_interface.get_issue(issue_number)

"""
interface_led = GitHub('github.engineering.zhaw.ch/api/v3', 'mekesyac', 'LED-Cube-Prototyper')
interface_led.get_issue(4)

interface = GitHub('github.engineering.zhaw.ch/api/v3', 'BA16-ML-Java-Analysis', 'Documents')
interface.get_issue(10)
"""