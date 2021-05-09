import argparse
import os
import sys
import re
import json
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.File import File
from github.PaginatedList import PaginatedList
from github.ContentFile import ContentFile
from github.Branch import Branch

from Utils.github_workflow_scripts.utils import load_json, CONTENT_ROOT_PATH

METADATA = 'metadata.json'
PACKS = 'Packs'
SUPPORT = 'support'
XSOAR_SUPPORT = 'xsoar'
PACK_NAME_REGEX = re.compile(r'Packs/([A-Za-z0-9-_.]+)/')


def get_metadata_filename_from_pr(pr_files: PaginatedList[File]) -> str:
    """ Iterates over all pr files and return the pr metadata.json filename if exists, else None

    Args:
        pr_files: The list of pr files

    Returns:
        The pr metadata.json filename if exists, else None

    """
    for file in pr_files:
        if METADATA in file.filename:
            return file.filename
    return ''


def get_pack_support_type_from_pr_metadata_file(pr_metadata_file: str, pr: PullRequest, repo: Repository):
    """ Retrieves the support type from the pr metadata.json file

    Args:
        pr_metadata_file: The pr metadata.json filename
        repo: The repository
        pr: The pr

    Returns:
        The support type

    """
    branch_name: str = pr.head.label
    branch: Branch = repo.get_branch(branch=branch_name)
    metadata_file: ContentFile = repo.get_contents(path=pr_metadata_file, ref=branch.commit.sha)
    metadata_file_content: dict = json.loads(metadata_file.content)
    return metadata_file_content.get(SUPPORT)


def get_pack_name_from_pr(pr_files: PaginatedList[File]) -> str:
    """ Extracts the pack name from the pr files

    Args:
        pr_files: The list of pr files

    Returns:
        The pack name

    """
    for file in pr_files:
        if PACKS in file.filename:
            return re.findall(PACK_NAME_REGEX, file.filename)[0]

    raise Exception('PR does not contains files prefixed with "Packs".')


def get_pack_support_type_from_repo_metadata_file(pr_files: PaginatedList[File]):
    """ Retrieves the support type from the repo metadata.json file

    Args:
        pr_files: The pack name

    Returns:
        The support type

    """
    pack_name: str = get_pack_name_from_pr(pr_files)
    repo_pack_metadata_path: str = os.path.join(CONTENT_ROOT_PATH, PACKS, pack_name, METADATA)
    repo_pack_metadata: dict = load_json(repo_pack_metadata_path)
    return repo_pack_metadata.get(SUPPORT)


def arguments_handler():
    """ Validates and parses script arguments.

     Returns:
        Namespace: Parsed arguments object.

     """
    parser = argparse.ArgumentParser(description='Check if the contribution form needs to be filled.')
    parser.add_argument('-p', '--pr_number', help='The PR number to check if the contribution form needs to be filled.')
    parser.add_argument('-g', '--github_token', help='The GitHub token to authenticate the GitHub client.')
    return parser.parse_args()


def main():
    options = arguments_handler()
    pr_number = options.pr_number
    github_token = options.github_token

    org_name: str = 'demisto'
    repo_name: str = 'content'
    github_client: Github = Github(github_token, verify=False)
    content_repo: Repository = github_client.get_repo(f'{org_name}/{repo_name}')
    pr: PullRequest = content_repo.get_pull(pr_number)
    pr_files: PaginatedList[File] = pr.get_files()
    pr_metadata_file: str = get_metadata_filename_from_pr(pr_files)

    if pr_metadata_file:
        support_type = get_pack_support_type_from_pr_metadata_file(pr_metadata_file, pr, content_repo)
    else:
        support_type = get_pack_support_type_from_repo_metadata_file(pr_files)

    if support_type == XSOAR_SUPPORT:
        print('Contribution form should not be filled in XSOAR supported contributions.')
        sys.exit(0)
    else:
        error_message: str = f'Contribution form was not filled for PR: {pr_number}\n' \
                             f'Make sure to register your contribution by filling the contribution registration form ' \
                             f'in - https://forms.gle/XDfxU4E61ZwEESSMA'
        print(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
