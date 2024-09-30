
First Set environment using set_env.py file.
    - It adds dependencies(ffmpeg, Akvcammanager) into the system environment variable.
    - Create new virtual camera and set required configurations.

Second you can run main.py for the actual GUI application.


Build binary for the driver.

pyinstaller --icon="images/MBA.ico" --windowed --name "MeetnDriver" --onefile set_env.py

Build Binary file for the app

pyinstaller --name "Meetn Bonus App" --icon='images/MBA.ico' --onedir --noconfirm --windowed main.py