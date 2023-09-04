@echo off
set PIPENV_VENV_IN_PROJECT=1
setlocal EnableDelayedExpansion
pushd %~dp0

rem Required to make sure coverage is written to the right areas.
set "PROJECT_DIRECTORY=%cd%"
set PYTHONPATH=%PROJECT_DIRECTORY%

rem Set needed environment variables.
set PTEST_TEMPFILE=temp_ptest.txt
set PTEST_SCRIPT_DIRECTORY=%~dp0

rem Look for options on the command line.
set PTEST_QUIET_MODE=
set PTEST_MARKER=
set PTEST_KEYWORD=
:process_arguments
if "%1" == "-h" (
    echo Command: %0 [options]
    echo   Usage:
    echo     - Execute the tests for this project.
    echo   Options:
    echo     -h                This message.
    echo     -q                Quiet mode.
	echo     -k [keyword]      Execute only the tests matching the specified keyword.
	echo     -m [marker]       Execute only the tests matching the specified marker.
    GOTO real_end
) else if "%1" == "-q" (
	set PTEST_QUIET_MODE=1
) else if "%1" == "-k" (
	set PTEST_KEYWORD=%2
	if not defined PTEST_KEYWORD (
		echo Option -m requires a keyword argument to follow it.
		goto error_end
	)
	shift
) else if "%1" == "-m" (
	set PTEST_MARKER=%2
	if not defined PTEST_MARKER (
		echo Option -k requires a marker argument to follow it.
		goto error_end
	)
	shift
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

if defined PTEST_MARKER (
	set PTEST_KEYWORD=-m %PTEST_MARKER%
) else if defined PTEST_KEYWORD (
	set PTEST_KEYWORD=-k %PTEST_KEYWORD%
)

rem Enter main part of script.
if defined PTEST_KEYWORD (
	echo {Executing partial test suite...}
	set PYTEST_ARGS=
) else (
	echo {Executing full test suite...}
)
if not defined PTEST_QUIET_MODE (
	pipenv run pytest --durations=0 --capture=tee-sys %PYTEST_ARGS% %PTEST_KEYWORD%
	if ERRORLEVEL 1 (
		echo.
		echo {Executing test suite failed.}
		goto error_end
	)
) else (
	pipenv run pytest --durations=0 --capture=tee-sys %PYTEST_ARGS% %PTEST_KEYWORD% > %PTEST_TEMPFILE% 2>&1
	if ERRORLEVEL 1 (
		type %PTEST_TEMPFILE%
		echo.
		echo {Executing test suite failed.}
		goto error_end
	)
)

if defined PTEST_KEYWORD (
	echo {Execution of partial test suite succeeded.}
	goto success_end
)

echo {Execution of full test suite succeeded.}
goto success_end

:success_end
rem Exit main part of script.
echo.
set PC_EXIT_CODE=0
goto real_end

:error_end
set PC_EXIT_CODE=1

:real_end
erase /f /q %PTEST_TEMPFILE% > nul 2>&1
popd
echo "%PC_EXIT_CODE%"
exit /B %PC_EXIT_CODE%