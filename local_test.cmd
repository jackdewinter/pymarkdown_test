@echo on
set PIPENV_VENV_IN_PROJECT=1
setlocal EnableDelayedExpansion
pushd %~dp0

rem Enter main part of script.
echo {Executing full test suite...}

if not defined GITHUB_ACCESS_TOKEN (
    echo {Variable 'GITHUB_ACCESS_TOKEN' not defined.}
    goto error_end
)

echo {Copying new package files from sibling 'pymarkdown' directory.}
erase packages\py*.whl
erase packages\py*.gz
copy ..\pymarkdown\dist packages
if ERRORLEVEL 1 (
    echo {Copy of packages to local directory failed.}
    goto error_end
)

echo {Executing package based tests...}
call ptest -k test_package_
if ERRORLEVEL 1 (
    echo {Execution of package based tests failed.}
    goto error_end
)

echo {Executing pre-commit based tests...}
call ptest -k test_pre
if ERRORLEVEL 1 (
    echo {Execution of pre-commit based tests failed.}
    goto error_end
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
popd
exit /B %PC_EXIT_CODE%