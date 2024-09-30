import os.path
import subprocess
import sys
import threading
import time
import cv2
from background_removal import background_change, new_session
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QComboBox,
                               QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QWidget, QFileDialog, QPushButton, QSplashScreen)
from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter, QPainterPath, QMovie
from PySide6.QtCore import QTimer, Qt, QPoint, QRectF, Slot, QEvent
from Toggle_Switch import LabeledToggleSwitch, RoundedItemDelegate
from get_cameras import get_cameras
from get_image_path import list_files_in_directory
from startup_config import add_to_startup, remove_from_startup, check_startup_registry
from virtual_cam import feed_frame_to_vir_cam

CREATION_FLAGS = 0
if sys.platform == "win32":
    CREATION_FLAGS = subprocess.CREATE_NO_WINDOW

AKV_CAM_COMMAND = [
    'AkVCamManager',
    'stream',
    '--fps', '30',
    'AkVCamVideoDevice0',
    'RGB24',
    '640', '480'
]
CONTROL_BUTTON_SIZE = 23


class VirtualCameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        if os.path.exists('images'):
            self.pre_path = ''
        else:
            self.pre_path = 'C:/Program Files/Meetn Bonus App/'
        self.cameras = None
        self.setWindowTitle("Meet Bonus App")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.offset = QPoint()
        self.background_image = None
        # Start the AkVCamManager process
        self.akv_cam_proc = subprocess.Popen(AKV_CAM_COMMAND, stdin=subprocess.PIPE, creationflags=CREATION_FLAGS)
        print('here', self.pre_path)
        self.setStyleSheet(f"""  
            QLabel, QPushButton {{  
                color: white;  
                font-family: 'Sans-serif';  
                font-size: 14px;  
                background-color: black;  
            }}  
            QListWidget {{
                font-family: 'Sans-serif';
                background-color: black;

            }}

            QComboBox {{ 
                background-color: #333;  /* Gray background */  
                border: 1px solid #111;  /* Darker gray border */  
                color: white;            /* Text color */  
                font-family: 'Sans-serif';  
                border-radius: 5px;
                font-size: 14px;  
                padding: 5px;            /* Padding inside the dropdown */  
            }} 
            QComboBox::drop-down {{  
                border: none;            /* No border around the dropdown button */  
            }} 

            QComboBox QAbstractItemView {{  
                background-color: #333; /* Gray background for dropdown items */  
                color: white;           /* Text color for dropdown items */  
                selection-background-color: #777;  /* Background color when an item is hovered or selected */  
            }}  

            #Title {{ 
                font-size: 18px;  
                padding: 0px;  
                background-color: transparent;  
                text-align: left;  
            }}  
            #SectionTitle {{  
                font-size: 16px;  
                padding: 5px 0;  
                background-color: transparent;  
            }}  
            QPushButton#ControlButton {{ 
                border: none;  
                icon: url({self.pre_path}res/minimize.png);   
                icon-size: 30px;  
                background-color: gray;  
            }}  
            QPushButton#ControlButton:hover {{  
                border: none;  
                icon-size: 30px;  
                icon: url({self.pre_path}res/hover/minimize.png);   
            }}   
            QPushButton#CloseButton {{ 
                border: none;  
                icon: url(res/close.png);  
                icon-size: 30px;              
                background-color: gray;  
            }} 
            QPushButton#CloseButton:hover {{  
                border: none;  
                icon-size: 30px;  
                icon: url(res/hover/close.png);  
            }}  

        """)

        main_layout = QVBoxLayout()

        title_bar_layout = QHBoxLayout()

        self.title_label = QLabel("Meetn Bonus App")
        self.title_label.setObjectName("Title")
        title_bar_layout.addWidget(self.title_label)

        control_button_layout = QHBoxLayout()

        minimize_button = QPushButton('')
        minimize_button.setObjectName("ControlButton")
        minimize_button.setFixedWidth(CONTROL_BUTTON_SIZE)
        minimize_button.setFixedHeight(CONTROL_BUTTON_SIZE)
        minimize_button.clicked.connect(self.showMinimized)
        control_button_layout.addWidget(minimize_button)

        close_button = QPushButton("")
        close_button.setObjectName("CloseButton")
        close_button.setFixedWidth(CONTROL_BUTTON_SIZE)
        close_button.setFixedHeight(CONTROL_BUTTON_SIZE)
        close_button.clicked.connect(self.close)
        control_button_layout.addWidget(close_button)

        title_bar_layout.addLayout(control_button_layout)
        main_layout.addLayout(title_bar_layout)

        central_layout = QHBoxLayout()
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setContentsMargins(5, 5, 5, 5)
        left_panel_layout.setSpacing(10)

        self.cam_label = QLabel("Select a camera source:")
        self.cam_label.setObjectName("SectionTitle")
        left_panel_layout.addWidget(self.cam_label)

        self.cam_dropdown = QComboBox()
        self.add_cameras()

        self.cam_dropdown.currentIndexChanged.connect(self.select_camera_source)
        left_panel_layout.addWidget(self.cam_dropdown)

        self.camera_label = QLabel(self)
        self.camera_label.setStyleSheet("border: 1px solid white;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        left_panel_layout.addWidget(self.camera_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_feed)
        self.cap = None

        features_layout = QVBoxLayout()

        self.green_screen_switch = LabeledToggleSwitch("I have a green or blue screen", self)
        features_layout.addWidget(self.green_screen_switch)

        self.blur_switch = LabeledToggleSwitch("Blur Background", self)

        features_layout.addWidget(self.blur_switch)

        self.run_on_startup_switch = LabeledToggleSwitch("Run on Startup", self)
        # self.run_on_startup_switch.switch.connect(self.startup_register)
        if check_startup_registry('Meetn Bonus App'):
            self.run_on_startup_switch.switch.setChecked(True)

        self.run_on_startup_switch.switch.stateChanged.connect(self.startup_register)
        features_layout.addWidget(self.run_on_startup_switch)

        left_panel_layout.addLayout(features_layout)

        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(5, 5, 5, 5)
        right_panel_layout.setSpacing(10)
        try:
            self.session = new_session('u2netp')
        except Exception as e:
            print(e, ' has occurred! And running on the CPU')
            self.session = new_session('u2netp', ['CPUExecutionProvider'])
        self.bg_label = QLabel("Select a virtual background:")
        self.bg_label.setObjectName("SectionTitle")
        right_panel_layout.addWidget(self.bg_label)
        button_container = QWidget(self)

        bg_select_layout = QHBoxLayout(button_container)
        bg_select_layout.setContentsMargins(0, 0, 0, 0)
        bg_select_layout.setSpacing(0)
        self.bg_included_button = QPushButton("Included")
        self.bg_local_button = QPushButton("Local")
        self.bg_included_button.setCheckable(True)
        self.bg_local_button.setCheckable(True)
        self.bg_included_button.setChecked(True)

        self.bg_included_button.clicked.connect(lambda: self.switch_bg_selection("included"))
        self.bg_local_button.clicked.connect(lambda: self.switch_bg_selection("local"))

        self.bg_included_button.setStyleSheet("""  
            QPushButton {   
                height: 30px;  
                background-color: #555;  
                color: white;  
                border-radius: 10px;  /* Rounded corners */  
                border: none;  
            }  
            QPushButton:checked {   
                background-color: #777;  /* Checked button color */  
                color: white;  
                border-radius: 10px;  /* Rounded corners */  
            }   
        """)
        self.bg_local_button.setStyleSheet("""  
            QPushButton {   
                background-color: #555;  
                height: 30px;  
                color: white;  
                border-radius: 10px;  /* Rounded corners */  
                border: none;  
            }  
            QPushButton:checked {   
                background-color: #777;  /* Checked button color */  
                color: white;  
                border-radius: 10px;  /* Rounded corners */  

            }  
        """)
        # Set the background for button container
        button_container.setStyleSheet("""  
                        height: 30px;  
                        background-color: #555;  
                        border-radius: 10px;  /* Rounded corners */  

                """)

        bg_select_layout.addWidget(self.bg_included_button)
        bg_select_layout.addWidget(self.bg_local_button)

        right_panel_layout.addWidget(button_container)

        # New: ComboBox for current folder path
        self.folder_dropdown = QComboBox()
        self.update_folder_list(self.pre_path + 'images')
        self.folder_dropdown.currentIndexChanged.connect(self.folder_selection_changed)
        right_panel_layout.addWidget(self.folder_dropdown)

        self.bg_image_list = QListWidget()
        self.bg_image_list.setViewMode(QListWidget.IconMode)
        self.bg_image_list.setIconSize(QPixmap(150, 120).size())

        self.bg_image_list.setItemDelegate(RoundedItemDelegate())
        self.bg_image_list.setSpacing(5)
        self.selected_bg_path = None

        self.update_image_list(self.pre_path + 'images/Abstract')
        self.bg_image_list.itemClicked.connect(self.set_background_image)
        right_panel_layout.addWidget(self.bg_image_list)

        central_layout.addLayout(left_panel_layout, 1)
        central_layout.addLayout(right_panel_layout, 1)
        main_layout.addLayout(central_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.start_camera()

        # New: Method to update folder dropdown list

        self.cam_dropdown.installEventFilter(self)
        self.folder_dropdown.installEventFilter(self)
        self.resize(1000, 600)  # Set the window size
        self.center()  # Center the window on the screen

    def center(self):
        # Get the screen size
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Get the size of the window
        window_geometry = self.frameGeometry()

        # Find the center point
        center_point = screen_geometry.center()

        # Move the window's rectangle to the center of the screen
        window_geometry.moveCenter(center_point)

        # Move the top left of the window to the top left of the rectangle
        self.move(window_geometry.topLeft())

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress and source in [self.cam_dropdown, self.folder_dropdown]:
            # Ignore the mouse press event if it is coming from dropdowns
            QWidget.mousePressEvent(self, event)

        return super().eventFilter(source, event)

    def update_folder_list(self, base_dir):
        self.folder_dropdown.clear()
        folders = list_files_in_directory(base_dir, folders_only=True)
        if folders:
            simplified_folders = list(map(lambda folder: folder.split('/')[-1], folders))
            self.folder_dropdown.addItems(simplified_folders)

    def update_image_list(self, path):
        self.bg_image_list.clear()
        images = list_files_in_directory(path)
        for image in images:
            item = QListWidgetItem(QIcon(image), "")
            item.setData(Qt.UserRole, image)
            self.bg_image_list.addItem(item)

    @Slot(QListWidgetItem)
    def set_background_image(self, item):
        # Remove any existing styling from all items
        for i in range(self.bg_image_list.count()):
            self.bg_image_list.item(i).setBackground(Qt.transparent)

        if item.data(Qt.UserRole):
            self.selected_bg_path = item.data(Qt.UserRole)
            try:
                self.background_image = cv2.imread(self.selected_bg_path)

                # Highlight the selected item with a border
                item.setBackground(Qt.blue)  # Set the background color for selected

            except Exception as e:
                print(f'{e} has occurred.')

    def paintEvent(self, event):
        painter = QPainter(self)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(path)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.black)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    def closeEvent(self, event):
        self.stop_camera()
        self.akv_cam_proc.stdin.close()
        self.akv_cam_proc.wait()
        event.accept()

    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def start_camera(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.camera_label.setText("Failed to open the camera.")
            return

        self.timer.start(30)

    def update_camera_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            self.camera_label.setText("Failed to capture image.")
            return
        frame = cv2.resize(frame, (600, 400))
        frame = background_change(self.background_image, frame, self.blur_switch.switch.isChecked(),
                                  self.green_screen_switch.switch.isChecked(), input_session=self.session)

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        step = channel * width
        try:
            feed_frame_to_vir_cam(self.akv_cam_proc, frame)

        except Exception as e:
            print(f"An error occurred1: {e}")

        q_img = QImage(frame.data, width, height, step, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(q_img))

    def stop_camera(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()

    def select_camera_source(self, index):
        self.stop_camera()
        if index == len(self.cameras):
            index = 'videos/output.mp4'
        self.start_camera(index)

    def switch_bg_selection(self, mode):
        if mode == "included":
            self.bg_included_button.setChecked(True)
            self.bg_local_button.setChecked(False)
            self.update_folder_list('images')
            self.update_image_list('images/Abstract')
        else:
            self.bg_included_button.setChecked(False)
            self.bg_local_button.setChecked(True)
            self.select_local_bg_folder()

    def select_local_bg_folder(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec():
            folder_path = dialog.selectedFiles()[0]
            if folder_path:
                self.update_folder_list(folder_path)
                self.update_image_list(folder_path)

    def folder_selection_changed(self, index):
        folder_name = self.folder_dropdown.itemText(index)
        if folder_name:
            selected_folder = folder_name
            self.update_image_list(selected_folder)

    def startup_register(self):
        """Handle the toggle event for blur background."""
        if self.run_on_startup_switch.switch.isChecked():
            add_to_startup()
        else:
            remove_from_startup()

    def add_cameras(self):
        self.cameras = get_cameras()
        for camera_detail in self.cameras:
            self.cam_dropdown.addItem(camera_detail)
        self.cam_dropdown.addItem('Sample Video')


done = False

def loop(splash, movie):
    global done

    # Create a loop to update the splash screen with each frame
    while not done:
        time.sleep(0.01)  # Adjust timing as needed to control speed
        if not movie.isValid():
            print("Invalid GIF")
            break

        movie.jumpToNextFrame()
        current_pixmap = movie.currentPixmap().scaled(1000, 600)


        if not current_pixmap.isNull():
            splash.setPixmap(current_pixmap)

        # Process events and introduce a small delay
        QApplication.processEvents()
    movie.stop()

if __name__ == "__main__":

    app = QApplication([])
    if os.path.exists('res'):
        pre_path = ''
    else:
        pre_path = 'C:/Program Files/Meetn Bonus App/'

    movie = QMovie(pre_path + 'res/loading.gif')
    movie.start()
    splash = QSplashScreen(movie.currentPixmap().scaled(1000, 600))
    thread = threading.Thread(target=loop, args=(splash, movie))
    splash.show()
    thread.start()
    window = VirtualCameraApp()
    window.show()
    done = True
    thread.join()
    splash.finish(window)
    sys.exit(app.exec())