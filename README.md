# PyMarkdown Test Repository

## TL;DR

These are integration tests for the [PyMarkdown](https://github.com/jackdewinter/pymarkdown)
project.

## The Long Story

Ever since the first release of the [PyMarkdown](https://github.com/jackdewinter/pymarkdown)
project, I have had a local directory on my machine called "pym_test".  In that
directory, I had a couple of batch scripts that reach over to the PyMarkdown project,
install the release packages into the local directory, and execute tests of PyMarkdown.
These tests were simple tests, but they made sure that the releases of PyMarkdown
went smoothly.

Until they didn't.

Sometime after release 0.9.5, there were a couple of times where I caught something
just before or after it was released and was able to mitigate it.  And then
the release of 0.9.10 happened.  For whatever reason (still researching), that release
worked fine on my machine, but failed on other machines.

My test scripts were mainly testing a packaged PyMarkdown, with only a passing
glance at the [Pre-Commit](https://pre-commit.com/) usage of [PyMarkdown](https://github.com/jackdewinter/pymarkdown/blob/main/docs/pre-commit.md)
as a pre-commit hook. To accommodate a required increase
in one of the project's dependent packages, I changed the `Piplock` file to access
the changed API and tested locally with that configuration.  All the scenario
tests passed, so I thought all was good.  Even after running my local test scripts,
all tests were passing and everything looked good.

After doing some debugging, I found out that I had changed the `Piplock` file, but
I had not changed the `install-requirements.txt` file used by the package install
scripts.  This resulted in both package installations and the Pre-Commit installations
failing. My cobbled together tests on my machine were passing.  Installed on another
machine, those same tests were failing.  There was a problem.

That is how the idea for this project and repository were born.  With a year or
two of extra experience writing GitHub workflows, I was sure that I could come
up with a better solution to this problem than local scripts on my machine.

## The Design

### Automated Execution

To ensure that I can execute this project during development of these tests and
on demand from the PyMarkdown project, the GitHub workflow from this project is
triggered to execute during development (`pull_request` and `workflow_display`).
For execution from the PyMarkdown project, the same workflow is triggered using
the `repository_dispatch` trigger. The `repository_dispatch` trigger allows for
cross-repository dispatching that includes a request object that can be used to
supply more context to the remote workflow.

```yaml
on:
  pull_request:
    branches:
      - main
  repository_dispatch:
  workflow_display:
```

To meet the needs of this project, the PyMarkdown workflow creates the following
JSON object:

```json
"client_payload": {
    "ref": "$WORKFLOW_RUN_BRANCH",
    "repository": "jackdewinter/pymarkdown",
    "run_id": "$WORKFLOW_RUN_ID",
    "sha": "$LAST_COMMIT_SHA"
}
```

For the package tests, the `run_id` field is used to query GitHub about uploaded
artifacts and download the `my-artifact` artifact holding the package file for
that workflow run.  For the Pre-Commit scenario tests, the workflow uses the `sha`
field to key Pre-Commit to the specific hash that needs to be tested.

### Installation Tests and Use Case Tests

From a project level, there are two main concerns that I face when I release the latest
version of the PyMarkdown project: will it install and will it work properly. While
I do have concerns about the functionality of the project, over 5500 independent
scenario tests address those concerns nicely.  That leaves concerns about installing
the package properly and detecting simple dependency issues. Those two remaining
concerns are somewhat tied together and hard to separate.  Therefore, I decided
to test both with a variety of simple use case tests.

As noted above, the first use of the project is provided through a Pre-Commit hook
and the second is through installing the compiled package.  In both cases, I want
to test the simple execution of the project to make sure it installs.  Once that is done,
I want to go on to perform a few more tests of things that I know have been a
problem in the past.  Currently, I want to test cases where I may have forgotten
to change the `install-requirements.txt` file.

Therefore, I created two sets of tests: one for scanning with Pre-Commit and one
for installing and scanning with a packaged application.  In both cases, I started
off with one or two tests that are simple and just make sure that the application
works smoothly with a simple case. Then, as the main thing that changes in the
`install-requirements.txt` file is the version of the `application_properties`
package, I chose to include tests that use setting application properties
in each form.  From my analysis, these tests do not must be as exhaustive as
the scenario tests.  These tests just must make sure that the users can complete
their scans as expected.

### Future Work

I believe that these steps will raise my confidence that I have covered
the weak points in my release process testing for PyMarkdown.  It also removes my
need for a cobbled together set of batch scripts kept only on a local machine.

However, as I experiment with other small projects, I find that I am copying more
and more code from the core functionality of PyMarkdown.  These tend to be simple things like having
a tested and ready-to-go configuration system like the `application_properties`
package.  As I work to move this functionality to other small packages, I expect I
will run into similar issues as I did with the `application_properties` package.
Therefore, as I pull each one out, I believe that I will need to add other tests to cover
those scenarios in the future.

In addition, if I find any other "weird" patterns of usage that are causing me
issues, I can now add those tests to this project.

## The Tests

The first pass over these tests took about three weeks of playing around to get
things in working order.  There are parts of the code where I know things can
be improved on, but they work well enough for now.

In each test file, I strove to keep as much of the "plumbing" in the `util_helper.py`
file, allowing a reader to focus on the tests.  While the names of the test helper
functions may be long, I strived to name each function with a title that accurately
reflected what it was doing.

Local execution of these tests may not reveal it, but extra work was
performed to make these tests "version" resilient.  The first part of this was
to use the `modify_pipfile.py` script to replace the `3.8` version in the `Pipfile`
with the current Python version.  In addition, test `test_package_one` does extra
processing on the requested `help` output to deal with windows/non-windows output
issues and version 3.10 changes in output.  These have been clearly spelled out
to make those differences more visible.

### Specifics for Pre-Commit

For the Pre-Commit tests, the test execution is as follows:

1. Calculate the hash to use in the Pre-Commit `.pre-commit-config.yaml` file.
   1. If a SHA is provided, use that.
   1. If not, look at the [PyMarkdown](https://github.com/jackdewinter/pymarkdown)
      project and use the `main` branch to find the commit on that branch.
1. Create a temporary directory and copy any needed files into that directory.
1. Change the copied `.pre-commit-config.yaml` to include the calculated hash.
1. Initial an empty Git project. (Required for Pre-Commit.)
1. Execute Pre-Commit and check for results.

### Specifics for Packages

For the package install tests, the test execution is as follows:

1. Download the latest version of the package from the [PyMarkdown](https://github.com/jackdewinter/pymarkdown)
   project.
   1. For locally run tests, this logic first checks to see if there is a package
      already present in the `packages` directory.
   1. If the package is not found and the Workflow Run Id was provided, use that
      as the workflow to download the artifact from.
   1. Otherwise, look at the [PyMarkdown](https://github.com/jackdewinter/pymarkdown)
      project and use the `main` branch to find the last workflow run that passed.
1. Create a temporary directory and copy any needed files into that directory.
1. Install the downloaded package into the temporary directory.
1. Execute PyMarkdown and check for results.
