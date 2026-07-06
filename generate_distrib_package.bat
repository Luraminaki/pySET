@echo off
setlocal EnableDelayedExpansion

SET SEVENZIP_EXE=C:\Program Files\7-Zip\7z.exe
SET REPO=git@github.com:Luraminaki/pySET.git
SET BRANCH_OR_TAG=main
SET INSTALL_DIR=pySET
SET DEST=pySET.zip

IF NOT EXIST "%SEVENZIP_EXE%" (
    echo 7-Zip not found at %SEVENZIP_EXE%
    echo Please install 7-Zip or update the script with the correct path.
    exit /b 1
)


echo Generating %DEST% from %BRANCH_OR_TAG% from repository %REPO%
git "fetch" "--all" "-p"
git "checkout" %BRANCH_OR_TAG%
git "pull"

cd "flask"
call npm install
call npm run generate
cd ..

REM `npm run generate` leaves flask\dist as a symlink/junction to flask\.output\public (see
REM pyset/server_app.py, which serves the app from flask\dist). 7-Zip's handling of NTFS
REM reparse points is unreliable, and the link itself is a machine-specific absolute path, so
REM re-materialize it as a real directory before zipping rather than trusting 7z to follow it.
IF EXIST "flask\dist" rmdir "flask\dist"
robocopy "flask\.output\public" "flask\dist" /E >nul

DEL %DEST%
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "README.md""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "INSTALL.md""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "pyproject.toml""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "config.json""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% ".env.example""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "pyset/*""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "gunicorn/*.py""
call cmd /C ""%SEVENZIP_EXE%" a -tzip %DEST% "flask/dist/*""

echo Done !