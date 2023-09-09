"""
Module to provide helper methods and classes for tests.
"""
import dataclasses
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.request import Request, urlopen


@dataclasses.dataclass()
class Bob:
    """
    Class to provide encapsulation on what was returned from a process execution.
    """

    return_code: int
    std_out: str
    std_error: str

    def does_any_line_match_expression(self, regex_to_match: str) -> Optional[str]:
        """
        Does any line in the output match the regular expression?
        """
        return next(
            (
                next_line
                for next_line in self.std_out.split("\n")
                if re.search(regex_to_match, next_line)
            ),
            None,
        )

    def does_any_line_match_string(self, string_to_match: str) -> Optional[str]:
        """
        Does any line in the output match the string EXACTLY?
        """
        return next(
            (
                next_line
                for next_line in self.std_out.split("\n")
                if string_to_match == next_line
            ),
            None,
        )


class UtilHelpers:
    """
    Class to provide utility helper methods for the integration tests.
    """

    __old_hash_value: str = ""
    __old_access_token: Optional[str] = None
    __package_extension = ".tar.gz"

    @staticmethod
    def get_python_version() -> str:
        """
        Get a cleaned up python version.
        """
        current_python_version = sys.version
        index = current_python_version.index("(")
        current_python_version = current_python_version[:index].strip()
        return current_python_version

    @staticmethod
    def __get_github_key_token_from_environment() -> Optional[str]:
        """
        Query the environment for a access token to use.
        """

        if UtilHelpers.__old_access_token:
            return UtilHelpers.__old_access_token

        print("Querying environment for variable GITHUB_ACCESS_TOKEN.")
        env_run_id = os.environ.get("GITHUB_ACCESS_TOKEN")
        UtilHelpers.__old_access_token = env_run_id
        return env_run_id

    @staticmethod
    def get_workflow_run_id_from_environment() -> Optional[int]:
        """
        Query the environment for a workflow run id to use.
        """

        print("Querying environment for variable REMOTE_RUN_ID.")
        if env_run_id := os.environ.get("REMOTE_RUN_ID"):
            return int(env_run_id)
        return None

    @staticmethod
    def __get_remote_branch_sha_from_enviroment() -> Optional[str]:
        """
        Query the environment for a SHA for a branch.
        """

        print("Querying environment for variable REMOTE_SHA.")
        return os.environ.get("REMOTE_SHA")

    @staticmethod
    def get_packages_path() -> str:
        """
        Get the path where Pip packages are expected to be kept.
        """

        return os.path.join(os.getcwd(), "packages")

    @staticmethod
    def __url_open(url_to_open: str) -> Dict[str, Any]:
        """
        Submit a GET request for JSON data.
        """

        req = Request(url_to_open)
        req.add_header(
            "Authorization",
            f"token {UtilHelpers.__get_github_key_token_from_environment()}",
        )
        with urlopen(req) as response:
            json_object = json.loads(response.read().decode("utf-8"))
            return cast(Dict[str, Any], json_object)

    @staticmethod
    def url_open_binary(url_to_open: str) -> None:
        """
        Submnit a GET request for a binary file that is a zip file,
        and extract any contents into the packages directory.
        """

        packages_path = os.path.join(os.getcwd(), "packages")
        zip_file_download_path = os.path.join(packages_path, "download.zip")

        req = Request(url_to_open)
        req.add_header(
            "Authorization",
            f"token {UtilHelpers.__get_github_key_token_from_environment()}",
        )
        with urlopen(req) as response, open(zip_file_download_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)

        with zipfile.ZipFile(zip_file_download_path) as zip_file:
            zip_file.extractall(packages_path)

    @staticmethod
    def calculate_branch_hash() -> str:
        """
        Calculate the hash to use for the branch.
        """
        if UtilHelpers.__old_hash_value:
            print(f"Using hash '{UtilHelpers.__old_hash_value}' from previous test.")
            return UtilHelpers.__old_hash_value

        branch_hash = UtilHelpers.__get_remote_branch_sha_from_enviroment()
        if branch_hash:
            print(f"Using hash '{branch_hash}' from environment.")
        else:
            print(                "Calculating hash from last workflow run of default branch."            )
            if not UtilHelpers.__get_github_key_token_from_environment():
                assert False, "GitHub Personal Access Token not provided."

            def_branch = UtilHelpers.__get_default_branch()
            branch_hash = UtilHelpers.__get_branch_head_hash(def_branch)
            print(f"Using hash '{branch_hash}' from default branch.")
        UtilHelpers.__old_hash_value = branch_hash
        return branch_hash

    @staticmethod
    def execute_pre_commit(destination_directory: str) -> Bob:
        """
        Execute pre-commit in the specified directory.
        """

        command_result = subprocess.run(
            [
                "pipenv",
                "run",
                "pre-commit",
                "run",
                "pymarkdown",
                "--files",
                "README.md",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=destination_directory,
            check=False,
        )

        print(f"Pre-Commit code: {str(command_result.returncode)}")
        if std_out := command_result.stdout.decode("utf-8"):
            print("Pre-Commit output:::\n" + std_out + "\n::")
        if std_error := command_result.stderr.decode("utf-8"):
            print("Pre-Commit error:::\n" + std_error + "\n::")
        return Bob(command_result.returncode, std_out, std_error)

    @staticmethod
    def initialize_git_in_directory(destination_directory: str) -> None:
        """
        Pre-Commit REQUIRES git, even a dummy one. So provide it.
        """

        command_result = subprocess.run(
            ["git", "init"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=destination_directory,
            check=False,
        )
        print(f"Git Init Code: {command_result.returncode}")
        if command_result.returncode != 0:
            if std_out := command_result.stdout.decode("utf-8"):
                print("Git Init output:::\n" + std_out + "\n::")
            if std_error := command_result.stderr.decode("utf-8"):
                print("Git Init error:::\n" + std_error + "\n::")
            assert False

    @staticmethod
    def localize_precommit_configuration(
        destination_directory: str, branch_hash: str
    ) -> None:
        """
        Localize the pre-commit config py replacing `{{git-sha}}` with the hash.
        """

        file_path = ".pre-commit-config.yaml"
        print(f"Replacing hash in '{file_path}' with '{branch_hash}'.")
        file_path = os.path.join(destination_directory, file_path)
        with open(file_path, "rt", encoding="utf-8") as input_file:
            all_lines = input_file.readlines()
        modified_lines = [i.replace("{{git-sha}}", branch_hash) for i in all_lines]
        with open(file_path, "wt", encoding="utf-8") as output_file:
            output_file.writelines(modified_lines)

    @staticmethod
    def __make_value_visible(value_to_modify: Any) -> str:
        """
        For the given value, turn it into a string if necessary, and then replace
        any known "invisible" characters with more visible strings.
        """
        return (
            str(value_to_modify)
            .replace("\b", "\\b")
            .replace("\\a", "\\a")
            .replace("\t", "\\t")
            .replace("\n", "\\n")
        )

    @staticmethod
    def __find_line_differences(
        expected_text_lines: List[str], actual_text_lines: List[str]
    ) -> Tuple[bool, List[str]]:
        line_differences = list(difflib.ndiff(expected_text_lines, actual_text_lines))
        return (
            any(
                (
                    next_possible_difference.startswith("?")
                    or next_possible_difference.startswith("+")
                    or next_possible_difference.startswith("-")
                )
                for next_possible_difference in line_differences
            ),
            line_differences,
        )

    @staticmethod
    def compare_actual_output_versus_expected_output(
        stream_name: str,
        actual_text_lines: List[str],
        expected_text_lines: List[str],
        windows_output_lines: Optional[List[str]] = None,
    ) -> None:
        """
        Do a thorough comparison of the actual stream against the expected text.
        """

        print("Comparing expected against differences.")
        was_one_different, line_differences = UtilHelpers.__find_line_differences(
            expected_text_lines, actual_text_lines
        )
        if not was_one_different:
            return
        if windows_output_lines and sys.platform.startswith("win"):
            print("Comparing expected against windows differences.")
            was_one_different, line_differences = UtilHelpers.__find_line_differences(
                windows_output_lines, actual_text_lines
            )
            if not was_one_different:
                return

        # print("==========")
        # for i,j in enumerate(line_differences):
        #     print(f"{i}:{j}")
        # print("==========")
        # print(len(line_differences))
        formatted_line_differences = "\n".join(line_differences)
        diff_values = (
            f"\n---Diff Start---\n{formatted_line_differences}\n---Diff End---\n"
        )

        print(f"WARN>actual>>{UtilHelpers.__make_value_visible(actual_text_lines)}")
        print(f"WARN>expect>>{UtilHelpers.__make_value_visible(expected_text_lines)}")
        raise AssertionError(f"{stream_name} not as expected:\n{diff_values}")

    @staticmethod
    def __run_pipenv_lock(directory_path: str, environment_dict: Dict[str, str]) -> Bob:
        """
        Create a pipenv lock file.
        """

        current_python_version = UtilHelpers.get_python_version()

        command_result = subprocess.run(
            [
                "pipenv",
                "--python",
                current_python_version,
                "lock",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=directory_path,
            env=environment_dict,
            check=False,
        )

        print(f"Pipenv Lock code: {str(command_result.returncode)}")
        if std_out := command_result.stdout.decode("utf-8"):
            print("Pipenv Lock output:::\n" + std_out + "\n::")
        if std_error := command_result.stderr.decode("utf-8"):
            print("Pipenv Lock error:::\n" + std_error + "\n::")
        return Bob(command_result.returncode, std_out, std_error)

    @staticmethod
    def __run_pipenv_sync(directory_path: str, environment_dict: Dict[str, str]) -> Bob:
        """
        Syncronize to the provided PipEnv packages.
        """

        command_result = subprocess.run(
            [
                "pipenv",
                "sync",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=directory_path,
            env=environment_dict,
            check=False,
        )

        print(f"Pipenv Sync code: {str(command_result.returncode)}")
        if std_out := command_result.stdout.decode("utf-8"):
            print("Pipenv Sync output:::\n" + std_out + "\n::")
        if std_error := command_result.stderr.decode("utf-8"):
            print("Pipenv Sync error:::\n" + std_error + "\n::")
        return Bob(command_result.returncode, std_out, std_error)

    @staticmethod
    def __run_pipenv_install(
        directory_path: str, environment_dict: Dict[str, str], package_path: str
    ) -> Bob:
        """
        Used PipEnv install to install the specified package.
        """

        command_result = subprocess.run(
            ["pipenv", "install", package_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=directory_path,
            env=environment_dict,
            check=False,
        )

        print(f"Pipenv Install code: {str(command_result.returncode)}")
        if std_out := command_result.stdout.decode("utf-8"):
            print("Pipenv Install output:::\n" + std_out + "\n::")
        if std_error := command_result.stderr.decode("utf-8"):
            print("Pipenv Install error:::\n" + std_error + "\n::")
        return Bob(command_result.returncode, std_out, std_error)

    @staticmethod
    def run_pipenv_run(
        directory_path: str, environment_dict: Dict[str, str], run_arguments: List[str]
    ) -> Bob:
        """
        Execute a "Pipenv run" command.
        """

        pipenv_run_arguments = ["pipenv", "run", *run_arguments]
        print(f"Arguments: {pipenv_run_arguments}")
        command_result = subprocess.run(
            pipenv_run_arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=directory_path,
            env=environment_dict,
            check=False,
        )

        print(f"Pipenv Install code: {str(command_result.returncode)}")
        if std_out := command_result.stdout.decode("utf-8"):
            print("Pipenv Install output:::\n" + std_out + "\n::")
        if std_error := command_result.stderr.decode("utf-8"):
            print("Pipenv Install error:::\n" + std_error + "\n::")
        return Bob(command_result.returncode, std_out, std_error)

    @staticmethod
    def __search_for_eligible_packages_to_install() -> List[str]:
        """
        Search in the local "packages" directory for pip install packages.
        """

        packages_path = UtilHelpers.get_packages_path()
        if os.path.exists(packages_path):
            assert os.path.isdir(
                packages_path
            ), f"Path {packages_path} should be a directory."
        try:
            files = os.listdir(packages_path)
            files = [
                f
                for f in files
                if os.path.isfile(os.path.join(packages_path, f))
                and f.endswith(UtilHelpers.__package_extension)
            ]
        except FileNotFoundError:
            files = []
        return files

    @staticmethod
    def __get_only_package_to_install() -> str:
        """
        In the packages directory, there should be one-and-only-one tar file.
        """

        files = UtilHelpers.__search_for_eligible_packages_to_install()
        packages_path = UtilHelpers.get_packages_path()
        assert len(files) == 1, (
            f"Only one file matching {UtilHelpers.__package_extension} should exist "
            + f"in {packages_path}"
        )
        return os.path.join(packages_path, files[0])

    @staticmethod
    def copy_test_resource_file_to_test_directory(
        test_name: str, file_name: str, destination_directory: str
    ) -> None:
        """
        Copy the directory from the resources to a new test directory.
        """

        source_directory = os.path.join(os.getcwd(), "test", "resources", test_name)
        source_path = os.path.join(source_directory, file_name)
        destination_path = os.path.join(destination_directory, file_name)
        shutil.copyfile(source_path, destination_path)

        print(
            f"Copied file '{file_name}' from '{source_directory}' to '{destination_directory}'."
        )

    @staticmethod
    def copy_test_resource_directory_to_test_directory(
        test_name: str, destination_directory: str
    ) -> None:
        """
        Copy the directory from the resources to a new test directory.
        """

        source_directory = os.path.join(os.getcwd(), "test", "resources", test_name)
        shutil.copytree(source_directory, destination_directory, dirs_exist_ok=True)

        print(
            f"Copied directory from '{source_directory}' to '{destination_directory}'."
        )

    @staticmethod
    def load_templated_output(test_name: str, template_file: str) -> List[str]:
        """
        Load a templated file, strip any line endings, and apply any templated
        values specified in the dictionary.
        """

        source_directory = os.path.join(os.getcwd(), "test", "resources", test_name)
        file_path = os.path.join(source_directory, template_file)
        with open(file_path, "rt", encoding="utf-8") as input_file:
            all_lines = input_file.readlines()

        return [i[:-1] for i in all_lines]

    @staticmethod
    def get_workflow_id_for_workflow_path(relative_workflow_path: str) -> int:
        """
        Find the workflow id for a workflow with the specified path.
        """

        print(
            f"  Searching workflows for relative workflow path '{relative_workflow_path}'."
        )
        git_response = UtilHelpers.__url_open(
            "https://api.github.com/repos/jackdewinter/pymarkdown/actions/workflows"
        )

        fixed_path = f".github/workflows/{relative_workflow_path}"
        for i in git_response["workflows"]:
            if i["path"] == fixed_path:
                workflow_id = int(i["id"])
                print(f"  Workflow id '{workflow_id}' found.")
                return workflow_id
        assert (
            False
        ), f"No workflow with a relative path of {relative_workflow_path} was found."

    @staticmethod
    def find_workflow_run_object_from_workflow_id(
        workflow_id: int, branch_name: str
    ) -> Dict[str, Any]:
        """
        Use the workflow id and the branch name to find the last time a workflow was
        executed for that branch.
        """

        print(
            f"  Searching workflow id {workflow_id} for last run for branch '{branch_name}'."
        )
        git_response = UtilHelpers.__url_open(
            "https://api.github.com/repos/jackdewinter/pymarkdown"
            + f"/actions/workflows/{workflow_id}/runs"
        )

        for i in git_response["workflow_runs"]:
            if i["head_branch"] == branch_name:
                workflow_run_id = i["id"]
                print(
                    f"  Workflow run id '{workflow_run_id}' for branch name '{branch_name}' found."
                )
                return cast(Dict[str, Any], i)
        assert False, f"No workflow run with a branch name of {branch_name} was found."

    @staticmethod
    def get_workflow_run_object_from_run_id(run_id: int) -> Dict[str, Any]:
        """
        Fetch the workflow object by its run id.
        """

        return UtilHelpers.__url_open(
            f"https://api.github.com/repos/jackdewinter/pymarkdown/actions/runs/{run_id}"
        )

    @staticmethod
    def get_artifact_object_from_workflow_run_object(
        workflow_run_object: Dict[str, Any], artifact_name: str
    ) -> Dict[str, Any]:
        """
        Fetch the artifact object using the information in the workflow object.
        """

        workflow_run_id = workflow_run_object["id"]
        print(
            f"  Searching workflow id {workflow_run_id} for artifact named '{artifact_name}'."
        )
        git_response = UtilHelpers.__url_open(workflow_run_object["artifacts_url"])

        for i in git_response["artifacts"]:
            if i["name"] == artifact_name:
                return cast(Dict[str, Any], i)
        assert False, (
            f"No artifact with a name of {artifact_name} was found in "
            + f"workflow run id '{workflow_run_id}'."
        )

    @staticmethod
    def __get_default_branch() -> str:
        """
        Use the GitHub API to determine the default branch for the repository.
        """
        print("  Searching repository for the default branch name.")
        git_response = UtilHelpers.__url_open(
            "https://api.github.com/repos/jackdewinter/pymarkdown"
        )
        default_branch = git_response["default_branch"]

        assert default_branch is not None
        resultant_branch = cast(str, default_branch)
        print(f"  Default Branch name is '{resultant_branch}'.")
        return resultant_branch

    @staticmethod
    def __get_branch_head_hash(branch_name: str) -> str:
        """
        Use the GitHub API to determine the head hash fo rthe supplied branch.
        """

        print(f"  Searching repository branch '{branch_name}' for the latest commit.")
        git_response = UtilHelpers.__url_open(
            "https://api.github.com/repos/jackdewinter/pymarkdown/git/refs/heads"
        )
        modified_git_response = cast(List[Dict[str, Any]], git_response)

        branch_head_ref = f"refs/heads/{branch_name}"
        branch_hash = next(
            (
                cast(str, i["object"]["sha"])
                for i in modified_git_response
                if i["ref"] == branch_head_ref
            ),
            None,
        )
        assert branch_hash is not None
        print(f"  Default Branch Hash: {branch_hash}")
        return branch_hash

    @staticmethod
    def install_pymarkdown_in_fresh_environment(
        directory_to_install_in: str,
    ) -> Dict[str, str]:
        """
        In the provided directory, initialize PipEnv and install the one and only
        one package located in the packages directory.
        """

        only_package_path = UtilHelpers.__get_only_package_to_install()
        print(f"Package to install: {only_package_path}")

        environment_dict = dict(os.environ.copy(), **{"PIPENV_VENV_IN_PROJECT": "1"})

        bob_lock = UtilHelpers.__run_pipenv_lock(
            directory_to_install_in, environment_dict
        )
        assert bob_lock.return_code == 0

        bob_sync = UtilHelpers.__run_pipenv_sync(
            directory_to_install_in, environment_dict
        )
        assert bob_sync.return_code == 0

        bob_sync = UtilHelpers.__run_pipenv_install(
            directory_to_install_in, environment_dict, only_package_path
        )
        assert bob_sync.return_code == 0
        return environment_dict

    @staticmethod
    def assert_pymarkdown_install_package_present() -> None:
        """
        Assert that a pymarkdown package is present and that it is installed.
        """

        eligible_package_list = UtilHelpers.__search_for_eligible_packages_to_install()
        if len(eligible_package_list) != 0:
            print(f"Eligible package to install found: {eligible_package_list[0]}")
            return

        if not UtilHelpers.__get_github_key_token_from_environment():
            assert False, "GitHub Personal Access Token not provided."
        else:
            print("Did not find eligible package to install.")
            if not os.path.exists(UtilHelpers.get_packages_path()):
                print("Creating packages directory to hold artifacts.")
                os.mkdir(UtilHelpers.get_packages_path())

            workflow_run_id = UtilHelpers.get_workflow_run_id_from_environment()
            if workflow_run_id:
                print(f"Fetching specified workflow run id '{workflow_run_id}'.")
                workflow_run_object = UtilHelpers.get_workflow_run_object_from_run_id(
                    workflow_run_id
                )
            else:
                print("Determining last respective workflow run id.")
                workflow_id = UtilHelpers.get_workflow_id_for_workflow_path("main.yml")
                workflow_run_object = (
                    UtilHelpers.find_workflow_run_object_from_workflow_id(
                        workflow_id, "main"
                    )
                )
                workflow_run_id = workflow_run_object["id"]

            print(f"Fetching artifact information for workflow id '{workflow_run_id}'.")
            artifact_json = UtilHelpers.get_artifact_object_from_workflow_run_object(
                workflow_run_object, "my-artifact"
            )
            UtilHelpers.url_open_binary(artifact_json["archive_download_url"])
