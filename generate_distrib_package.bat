@echo off
setlocal EnableDelayedExpansion

SET REPO=git@github.com:Luraminaki\pySET.git
SET BRANCH_OR_TAG=main
SET INSTALL_DIR=pySET
SET DEST=pySET.zip

echo Generating %DEST% from %BRANCH_OR_TAG% from repository %REPO%
git "fetch" "--all" "-p"
git "checkout" %BRANCH_OR_TAG%
git "pull"

cd "flask"
call yarn install
call yarn generate
cd..

DEL %DEST%
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "README.md""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "*.py""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "requirements.txt""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "config.json""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "modules/*""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "gunicorn/*.py""
call cmd /C ""C:\Program Files\7-Zip\7z.exe" a -tzip %DEST% "flask/.output/*""

echo "Done !"