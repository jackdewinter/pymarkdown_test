"""
Tests to apply the pre-commit hook invocation of PyMarkdown.
"""
import os
import tempfile

import pytest

from .util_helpers import UtilHelpers


@pytest.mark.pre_commit
def test_pre_commit_one() -> None:  # sourcery skip: extract-method
    """
    Test to make sure that PyMarkdown can be invoked through Pre-Commit.
    """

    # Arrange
    branch_hash = UtilHelpers.calculate_branch_hash()
    with tempfile.TemporaryDirectory() as temporary_directory:
        UtilHelpers.copy_test_resource_to_test_directory(
            "pre_commit_test_one", temporary_directory
        )
        UtilHelpers.localize_precommit_configuration(temporary_directory, branch_hash)
        UtilHelpers.initialize_git_in_directory(temporary_directory)

        # Act
        pre_commit_result = UtilHelpers.execute_pre_commit(temporary_directory)

        # Assert
        assert pre_commit_result.return_code == 0
        assert pre_commit_result.does_any_line_match_expression(r"PyMarkdown\.*Passed")


@pytest.mark.pre_commit
def test_pre_commit_two() -> None:  # sourcery skip: extract-method
    """
    Test to make sure that PyMarkdown can be invoked through Pre-Commit and report an error.
    """

    # Arrange
    branch_hash = UtilHelpers.calculate_branch_hash()
    with tempfile.TemporaryDirectory() as temporary_directory:
        UtilHelpers.copy_test_resource_to_test_directory(
            "pre_commit_test_two", temporary_directory
        )
        UtilHelpers.localize_precommit_configuration(temporary_directory, branch_hash)
        UtilHelpers.initialize_git_in_directory(temporary_directory)

        # Act
        pre_commit_result = UtilHelpers.execute_pre_commit(temporary_directory)

        # Assert
        assert pre_commit_result.return_code == 1
        assert pre_commit_result.does_any_line_match_expression(r"PyMarkdown\.*Failed")
        scan_file_path = os.path.join(".", "README.md")
        error_line = (
            f"{scan_file_path}:1:1: MD041: First line in file should be a top level heading "
            + "(first-line-heading,first-line-h1)"
        )
        assert pre_commit_result.does_any_line_match_string(error_line)


@pytest.mark.pre_commit
def test_pre_commit_three() -> None:  # sourcery skip: extract-method
    """
    Test to make sure that PyMarkdown can be invoked through Pre-Commit and not report an error
    through disabling on the command line.
    """

    # Arrange
    branch_hash = UtilHelpers.calculate_branch_hash()
    with tempfile.TemporaryDirectory() as temporary_directory:
        UtilHelpers.copy_test_resource_to_test_directory(
            "pre_commit_test_three", temporary_directory
        )
        UtilHelpers.localize_precommit_configuration(temporary_directory, branch_hash)
        UtilHelpers.initialize_git_in_directory(temporary_directory)

        # Act
        pre_commit_result = UtilHelpers.execute_pre_commit(temporary_directory)

        # Assert
        assert pre_commit_result.return_code == 0
        assert pre_commit_result.does_any_line_match_expression(r"PyMarkdown\.*Passed")


@pytest.mark.pre_commit
def test_pre_commit_four() -> None:  # sourcery skip: extract-method
    """
    Test to make sure that PyMarkdown can be invoked through Pre-Commit and not report an error
    through disabling through a configuration file.
    """

    # Arrange
    branch_hash = UtilHelpers.calculate_branch_hash()
    with tempfile.TemporaryDirectory() as temporary_directory:
        UtilHelpers.copy_test_resource_to_test_directory(
            "pre_commit_test_four", temporary_directory
        )
        UtilHelpers.localize_precommit_configuration(temporary_directory, branch_hash)
        UtilHelpers.initialize_git_in_directory(temporary_directory)

        # Act
        pre_commit_result = UtilHelpers.execute_pre_commit(temporary_directory)

        # Assert
        assert pre_commit_result.return_code == 0
        assert pre_commit_result.does_any_line_match_expression(r"PyMarkdown\.*Passed")
