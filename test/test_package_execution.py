"""
Tests to apply the pre-commit hook invocation of PyMarkdown.
"""
import os
import tempfile

import pytest

from .util_helpers import UtilHelpers


def __assert_pymarkdown_install_package_present() -> None:
    eligible_package_list = UtilHelpers.search_for_eligible_packages_to_install()
    if len(eligible_package_list) != 0:
        print(f"Eligible package to install found: {eligible_package_list[0]}")
        return

    if not UtilHelpers.get_github_key_token_from_environment():
        assert False, "GitHub Personal Access Token not provided."
    else:
        print(len(UtilHelpers.get_github_key_token_from_environment()))

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
            workflow_run_object = UtilHelpers.find_workflow_run_object_from_workflow_id(
                workflow_id, "main"
            )
            workflow_run_id = workflow_run_object["id"]

        print(f"Fetching artifact information for workflow id '{workflow_run_id}'.")
        artifact_json = UtilHelpers.get_artifact_object_from_workflow_run_object(
            workflow_run_object, "my-artifact"
        )
        UtilHelpers.url_open_binary(artifact_json["archive_download_url"])


@pytest.mark.packages
def test_package_one() -> None:
    """
    Test to make sure that we can install the package and run it without any arguments.
    """
    __assert_pymarkdown_install_package_present()

    # Arrange
    expected_output_lines = UtilHelpers.load_templated_output(
        "package_one", "output_template"
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
            "package_one", bob_sync.std_out.splitlines(), expected_output_lines
        )
