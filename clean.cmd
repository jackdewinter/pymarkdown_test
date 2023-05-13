@echo off
set PIPENV_VENV_IN_PROJECT=1
setlocal EnableDelayedExpansion
pushd %~dp0

rem Set needed environment variables.
set CLEAN_TEMPFILE=%TEMP%\temp_clean_%RANDOM%.txt

rem Look for options on the command line.

set MY_VERBOSE=
:process_arguments
if "%1" == "-h" (
    echo Command: %0 [options]
    echo   Usage:
    echo     - Execute a clean build for this project.
    echo   Options:
    echo     -h                This message.
	echo     -v                Display verbose information.
    GOTO real_end
) else if "%1" == "-v" (
	set MY_VERBOSE=--verbose
) else if "%1" == "" (
    goto after_process_arguments
) else (
    echo Argument '%1' not understood.  Stopping.
	echo Type '%0 -h' to see valid arguments.
    goto error_end
)
shift
goto process_arguments
:after_process_arguments

rem Announce what this script does.

echo {Analysis of project started.}

rem Cleanly start the main part of the script

echo {Executing black formatter on Python code.}
pipenv run black %MY_VERBOSE% .
if ERRORLEVEL 1 (
	echo.
	echo {Executing black formatter on Python code failed.}
	goto error_end
)

echo {Executing import sorter on Python code.}
pipenv run isort %MY_VERBOSE% .
if ERRORLEVEL 1 (
	echo.
	echo {Executing import sorter on Python code failed.}
	goto error_end
)

if "%SOURCERY_USER_KEY%" == "" (
	echo {Sourcery user key not defined.  Skipping Sourcery static analyzer.}
) else (
	echo {Executing Sourcery static analyzer on Python code.}
	pipenv run sourcery login --token %SOURCERY_USER_KEY%
	if ERRORLEVEL 1 (
		echo.
		echo {Logging into Sourcery failed.}
		goto error_end
	)
	
	echo {  Executing Sourcery against changed project contents.}
	set "SOURCERY_LIMIT=--diff ^"git diff^""

	pipenv run sourcery review --check test !SOURCERY_LIMIT!
	if ERRORLEVEL 1 (
		echo.
		echo {Executing Sourcery on Python code failed.}
		goto error_end
	)
)

echo {Executing flake8 static analyzer on Python code.}
pipenv run flake8 -j 4 --exclude dist,build,.venv %MY_VERBOSE%
if ERRORLEVEL 1 (
	echo.
	echo {Executing static analyzer on Python code failed.}
	goto error_end
)

echo {Executing pylint static analyzer on Python source code.}
set TEST_EXECUTION_FAILED=
pipenv run pylint -j 1 --recursive=y %MY_VERBOSE% test
if ERRORLEVEL 1 (
	echo.
	echo {Executing pylint static analyzer on Python source code failed.}
	goto error_end
)

echo {Executing mypy static analyzer on Python source code.}
pipenv run mypy --strict test
if ERRORLEVEL 1 (
	echo.
	echo {Executing mypy static analyzer on Python source code failed.}
	goto error_end
)

echo {Executing unit tests on Python code.}
call ptest.cmd
if ERRORLEVEL 1 (
	echo.
	echo {Executing unit tests on Python code failed.}
	goto error_end
)

rem Cleanly exit the script

echo.
set PC_EXIT_CODE=0
echo {Analysis of project succeeded.}
goto real_end

:error_end
set PC_EXIT_CODE=1
echo {Analysis of project failed.}

:real_end
erase /f /q %CLEAN_TEMPFILE% > nul 2>&1
set CLEAN_TEMPFILE=
popd
exit /B %PC_EXIT_CODE%