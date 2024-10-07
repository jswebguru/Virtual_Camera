import os.path
import sys
import threading
from PySide6.QtWidgets import (QApplication, QSplashScreen)
from PySide6.QtGui import QMovie
import time

WINDOW_WIDTH = 1025
WINDOW_HEIGHT = 600
done = False


def loop(input_splash, input_movie):
    global done

    # Create a loop to update the splash screen with each frame
    while not done:
        time.sleep(0.01)  # Adjust timing as needed to control speed
        if not input_movie.isValid():
            print("Invalid GIF")
            break

        input_movie.jumpToNextFrame()
        current_pixmap = input_movie.currentPixmap().scaled(WINDOW_WIDTH, WINDOW_HEIGHT)

        if not current_pixmap.isNull():
            input_splash.setPixmap(current_pixmap)

        # Process events and introduce a small delay
        QApplication.processEvents()
    input_movie.stop()


if __name__ == "__main__":
    app = QApplication([])
    if os.path.exists('res'):
        pre_path = ''
    else:
        pre_path = 'C:/Program Files/Meetn Bonus App/'
    if len(sys.argv) <= 1 or sys.argv[1] != '--auto-run':
        movie = QMovie(pre_path + 'res/loading.gif')
        movie.start()
        splash = QSplashScreen(movie.currentPixmap().scaled(WINDOW_WIDTH, WINDOW_HEIGHT))
        thread = threading.Thread(target=loop, args=(splash, movie))
        splash.show()
        thread.start()
        from main import VirtualCameraApp
        window = VirtualCameraApp()
        window.show()
        done = True
        thread.join()
        splash.finish(window)
    else:
        from main import VirtualCameraApp
        window = VirtualCameraApp()
        window.minimize_to_tray()
    sys.exit(app.exec())
