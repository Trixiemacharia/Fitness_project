# Examiner Build

This project can be packaged for an examiner without requiring Python or MySQL on the target machine.

## What the packaged app does

- Runs in `examiner mode` using a local SQLite database.
- Stores its working data in a local `_examiner_data` folder beside the executable.
- Falls back to `%LOCALAPPDATA%\FitTrackExaminer` only if the executable folder is not writable.
- Applies migrations automatically on launch.
- Seeds demo users and sample dashboard data automatically on launch.
- Opens the browser to the login page.

## Demo accounts

- Admin: `examiner_admin` / `admin1234`
- User: `demo_member` / `demo1234`
- Extra users: `demo_trainer` / `demo1234`, `demo_beginner` / `demo1234`

## Build steps

1. Install PyInstaller into the project virtual environment:
   `venv\Scripts\python.exe -m pip install pyinstaller`
2. Build the executable:
   `build_examiner.bat`
3. Share the full folder:
   `dist\FitTrackExaminer`

The examiner should run `FitTrackExaminer.exe` inside that folder.

## Reseeding during testing

To refresh the local demo database while developing:

1. `set FITTRACK_EXAMINER_MODE=1`
2. `set FITTRACK_DATA_DIR=%CD%\Core`
3. `venv\Scripts\python.exe Core\manage.py migrate`
4. `venv\Scripts\python.exe Core\manage.py seed_examiner_data --force`

## Notes

- Your existing MySQL development setup still works when `FITTRACK_EXAMINER_MODE` is not enabled.
- Examiner data is intentionally local and separate from your development database.
