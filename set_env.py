import logging
import os
import ctypes
import sys
import subprocess
logger = logging.getLogger(__name__)
CREATION_FLAGS = 0
if sys.platform == "win32":
    CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
# Check here if not working: Computer\HKEY_CLASSES_ROOT\CLSID\{860BB310-5D01-11d0-BD3B-00A0C911CE86}


def set_system_path():
    """
    1. set ffmpeg as a system environment path variable
    2. set akvcammanager as a system environment path variable
    """
    ffmpeg_path = 'Dependency/ffmpeg/bin'
    akvcammanager_path = 'Dependency/AkVirtualCamera/x64'

    # Get current path and prepare to add only if necessary
    current_path = os.getenv('PATH', '')

    absolute_ffmpeg_path = os.path.abspath(ffmpeg_path)
    absolute_akvcammanager_path = os.path.abspath(akvcammanager_path)

    # Check if the paths are already in PATH to avoid duplicates
    dir_to_add = []
    if absolute_ffmpeg_path not in current_path:
        dir_to_add.append(absolute_ffmpeg_path)

    if absolute_akvcammanager_path not in current_path:
        dir_to_add.append(absolute_akvcammanager_path)

    if dir_to_add:
        new_path_entries = os.pathsep.join(dir_to_add)
        new_path = f"{current_path}{os.pathsep}{new_path_entries}"

        # Make sure to use PowerShell for modifying PATH
        try:
            command = rf'[System.Environment]::SetEnvironmentVariable("PATH", "{new_path}", "Machine")'
            completed_process = subprocess.run(['powershell', '-Command', command], capture_output=True,
                                               text=True, creationflags=CREATION_FLAGS)
            if completed_process.returncode != 0:
                print(f"Error setting system PATH: {completed_process.stderr}")
            else:
                print("PATH environment variable updated successfully via PowerShell.")
        except Exception as e:
            print(f"An exception occurred: {e}")


def create_virtual_camera():
    """
    Create virtual camera as 'VirtualCamera0' and update
    :return:
    """
    # Example command: list files in the current directory (Unix/Linux) or dir (Windows)
    abs_path = os.path.abspath('images/default_picture.jpg')
    commands = [
        'AkVCamAssistant -i'  # It's very important.
        'AkVCamManager add-device -i "AkVCamVideoDevice0" "Meetn Virtual Camera"',
        'AkVCamManager add-format AkVCamVideoDevice0 RGB24 640 480 30',
        'AkVCamManager update',
        'AkVCamManager set-picture ' + abs_path,
        'AkVcamManager devices'
    ]
    for command in commands:
        try:
            # Execute the command
            result = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=CREATION_FLAGS)

            # Print command output
            logging.info("Command Output:")
            logging.info(result.stdout)

        except subprocess.CalledProcessError as e:
            logging.info(f"An error occurred: {e}")
            logging.info(f"Stderr: {e.stderr}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.info(e, ' has occurred.')
        return False


def set_all_env():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

    # set_system_path()
    # print("PATH environment variable updated successfully.")
    create_virtual_camera()
    print('Virtual Camera created!!!')


if __name__ == "__main__":
    set_all_env()
    # create_virtual_camera()
