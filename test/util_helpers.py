"""
Module to provide helper methods and classes for tests.
"""
import dataclasses
import json
import os
import re
import shutil
import subprocess
from typing import Optional, cast
from urllib.request import urlopen


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

    @staticmethod
    def get_branch_hash() -> str:
        """
        Determine the hash to use for the branch.
        """

        # def_branch = UtilHelpers.get_default_branch()
        # branch_hash = UtilHelpers.get_branch_head_hash(def_branch)
        branch_hash = "55b0cfffe3d8cc21c8cd0b94322cc4c839a03095"
        branch_hash = "v0.9.9"
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
        file_path = os.path.join(destination_directory, file_path)
        with open(file_path, "rt", encoding="utf-8") as input_file:
            all_lines = input_file.readlines()
        modified_lines = [i.replace("{{git-sha}}", branch_hash) for i in all_lines]
        with open(file_path, "wt", encoding="utf-8") as output_file:
            output_file.writelines(modified_lines)

    @staticmethod
    def copy_test_resource_to_test_directory(
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
    def get_default_branch() -> str:
        """
        Use the GitHub API to determine the default branch for the repository.
        """

        with urlopen(
            "https://api.github.com/repos/jackdewinter/pymarkdown"
        ) as response:
            git_response = json.loads(response.read().decode("utf-8"))
            default_branch = git_response["default_branch"]

            assert default_branch is not None
            resultant_branch = cast(str, default_branch)
            print(f"Default Branch: {resultant_branch}")
            return resultant_branch

    @staticmethod
    def get_branch_head_hash(branch_name: str) -> str:
        """
        Use the GitHub API to determine the head hash fo rthe supplied branch.
        """

        with urlopen(
            "https://api.github.com/repos/jackdewinter/pymarkdown/git/refs/heads"
        ) as response:
            git_response = json.loads(response.read().decode("utf-8"))
            branch_head_ref = f"refs/heads/{branch_name}"
            branch_hash = next(
                (
                    i["object"]["sha"]
                    for i in git_response
                    if i["ref"] == branch_head_ref
                ),
                None,
            )
            assert branch_hash is not None
            resultant_hash = cast(str, branch_hash)
            print(f"Default Branch Hash: {resultant_hash}")
            return resultant_hash
