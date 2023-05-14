"""
Tests to apply the pre-commit hook invocation of PyMarkdown.
"""
import tempfile

import pytest

from .util_helpers import UtilHelpers


@pytest.mark.packages
def test_package_one() -> None:
    """
    Test to make sure that we can install the package and run it without any arguments.
    """

    # Arrange
    UtilHelpers.assert_pymarkdown_install_package_present()
    expected_output_lines = UtilHelpers.load_templated_output(
        "package_one", "output_template"
    )
    windows_output_lines = UtilHelpers.load_templated_output(
        "package_one", "windows_output_template"
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        execution_environment = UtilHelpers.install_pymarkdown_in_fresh_environment(
            temporary_directory
        )

        pipenv_arguments = ["pymarkdown"]

        # Act
        bob_sync = UtilHelpers.run_pipenv_run(
            temporary_directory, execution_environment, pipenv_arguments
        )

        # Assert
        assert bob_sync.return_code == 2
        UtilHelpers.compare_actual_output_versus_expected_output(
            "package_one",
            bob_sync.std_out.splitlines(),
            expected_output_lines,
            windows_output_lines,
        )


@pytest.mark.packages
def test_package_two() -> None:
    """
    Test to make sure that we can install the package and run it without any arguments.
    """

    # Arrange
    UtilHelpers.assert_pymarkdown_install_package_present()
    expected_output_lines = UtilHelpers.load_templated_output(
        "package_two", "output_template"
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        UtilHelpers.copy_test_resource_file_to_test_directory(
            "package_two", "test.md", temporary_directory
        )
        execution_environment = UtilHelpers.install_pymarkdown_in_fresh_environment(
            temporary_directory
        )

        pipenv_arguments = ["pymarkdown", "scan", "test.md"]

        # Act
        bob_sync = UtilHelpers.run_pipenv_run(
            temporary_directory, execution_environment, pipenv_arguments
        )

        # Assert
        assert bob_sync.return_code == 1
        UtilHelpers.compare_actual_output_versus_expected_output(
            "package_two", bob_sync.std_out.splitlines(), expected_output_lines
        )
