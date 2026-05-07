import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from shutil import copytree
from wsgiref.simple_server import make_server


def _bundle_root():
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _data_root():
    portable_dir = Path(sys.executable).resolve().parent / '_examiner_data' if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent / '_examiner_data'
    candidates = [portable_dir, Path.cwd() / '_examiner_data']

    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        candidates.append(Path(local_app_data) / 'FitTrackExaminer')

    for candidate in candidates:
        if not str(candidate):
            continue
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except PermissionError:
            continue

    raise PermissionError('Unable to create an examiner data directory.')


def _copy_seed_media(bundle_root, data_dir):
    source = bundle_root / 'media'
    target = data_dir / 'media'
    if source.exists() and not target.exists():
        copytree(source, target)


def _pick_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _bootstrap_django(bundle_root, data_dir):
    os.environ.setdefault('FITTRACK_EXAMINER_MODE', '1')
    os.environ.setdefault('FITTRACK_DATA_DIR', str(data_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
    os.environ.setdefault('DJANGO_SECRET_KEY', 'fittrack-examiner-secret-key')

    if str(bundle_root) not in sys.path:
        sys.path.insert(0, str(bundle_root))

    import django

    django.setup()

    from django.core.management import call_command

    call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
    call_command('seed_examiner_data', verbosity=0)


def main():
    bundle_root = _bundle_root()
    data_dir = _data_root()
    _copy_seed_media(bundle_root, data_dir)
    _bootstrap_django(bundle_root, data_dir)

    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.wsgi import get_wsgi_application

    port = _pick_port()
    url = f'http://127.0.0.1:{port}/login/'
    application = StaticFilesHandler(get_wsgi_application())

    threading.Thread(
        target=lambda: (time.sleep(1.2), webbrowser.open(url)),
        daemon=True,
    ).start()

    with make_server('127.0.0.1', port, application) as server:
        print('FitTrack Examiner is running.')
        print(f'Open {url} if your browser does not launch automatically.')
        print('Demo accounts:')
        print('  admin: examiner_admin / admin1234')
        print('  user:  demo_member / demo1234')
        server.serve_forever()


if __name__ == '__main__':
    main()
