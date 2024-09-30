import itertools
import subprocess
import sys
import threading
import time

import cv2
from background_removal import background_change
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QComboBox,
                               QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QWidget, QFileDialog, QPushButton)
from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter, QPainterPath
from PySide6.QtCore import QTimer, Qt, QPoint, QRectF, Slot
from background_removal import new_session
from Toggle_Switch import LabeledToggleSwitch
from get_image_path import list_files_in_directory
from startup_config import add_to_startup, remove_from_startup
from virtual_cam import feed_frame_to_vir_cam
from get_real_camera import update_camera_descriptions

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

class VirtualCameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Meet Bonus App")
        self.setGeometry(100, 20, 1000, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.offset = QPoint()
        self.background_image = None
        # Start the AkVCamManager process
        self.akv_cam_proc = subprocess.Popen(AKV_CAM_COMMAND, stdin=subprocess.PIPE, creationflags=CREATION_FLAGS)

        self.setStyleSheet("""  
            QLabel, QComboBox, QPushButton, QListWidget {  
                color: white;  
                font-family: 'Sans-serif';  
                font-size: 14px;  
                background-color: black;  
            }  
            #Title {  
                font-size: 18px;  
                padding: 10px;  
                background-color: transparent;  
                text-align: center;  
            }  
            #SectionTitle {  
                font-size: 16px;  
                padding: 5px 0;  
                background-color: transparent;  
            }  
            QPushButton#ControlButton {  
                width: 20px;  
                height: 20px;  
                border-radius: 10px;  
                font-size: 16px;  
                background-color: gray;  
                color: white;  
            }  
            QPushButton#CloseButton {  
                width: 20px;  
                height: 20px;  
                border-radius: 10px;  
                font-size: 12px;  
                background-color: red;  
                color: white;   
            }  
            QComboBox QAbstractItemView, QListWidget::item {  
                color: black;  
            }  
        """)

        main_layout = QVBoxLayout()

        title_bar_layout = QHBoxLayout()

        self.title_label = QLabel("Meet Virtual Camera")
        self.title_label.setObjectName("Title")
        title_bar_layout.addWidget(self.title_label)

        control_button_layout = QHBoxLayout()

        minimize_button = QPushButton("-")
        minimize_button.setObjectName("ControlButton")
        minimize_button.clicked.connect(self.showMinimized)
        control_button_layout.addWidget(minimize_button)

        maximize_button = QPushButton("+")
        maximize_button.setObjectName("ControlButton")
        maximize_button.clicked.connect(self.toggleMaximized)
        control_button_layout.addWidget(maximize_button)

        close_button = QPushButton("X")
        close_button.setObjectName("CloseButton")
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
        self.run_on_startup_switch.switch.stateChanged.connect(self.startup_register)
        features_layout.addWidget(self.run_on_startup_switch)

        left_panel_layout.addLayout(features_layout)

        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(5, 5, 5, 5)
        right_panel_layout.setSpacing(10)
        self.session = new_session('u2netp')

        self.bg_label = QLabel("Select a virtual background:")
        self.bg_label.setObjectName("SectionTitle")
        right_panel_layout.addWidget(self.bg_label)

        bg_select_layout = QHBoxLayout()
        self.bg_included_button = QPushButton("Included")
        self.bg_local_button = QPushButton("Local")
        self.bg_included_button.setCheckable(True)
        self.bg_local_button.setCheckable(True)
        self.bg_included_button.setChecked(True)

        self.bg_included_button.clicked.connect(lambda: self.switch_bg_selection("included"))
        self.bg_local_button.clicked.connect(lambda: self.switch_bg_selection("local"))

        self.bg_included_button.setStyleSheet("""  
            QPushButton {   
                background-color: #333;   
                color: white;   
            }  
            QPushButton:checked {   
                background-color: #555;   
                color: white;   
                border: 2px solid #0078D4;   
            }  
        """)
        self.bg_local_button.setStyleSheet("""  
            QPushButton {   
                background-color: #333;   
                color: white;   
            }  
            QPushButton:checked {   
                background-color: #555;   
                color: white;   
                border: 2px solid #0078D4;   
            }  
        """)

        bg_select_layout.addWidget(self.bg_included_button)
        bg_select_layout.addWidget(self.bg_local_button)
        right_panel_layout.addLayout(bg_select_layout)

        self.bg_image_list = QListWidget()
        self.bg_image_list.setViewMode(QListWidget.IconMode)
        self.bg_image_list.setIconSize(QPixmap(150, 150).size())
        self.bg_image_list.setSpacing(5)
        self.selected_bg_path = None

        images = list_files_in_directory('images')
        for image in images:
            item = QListWidgetItem(QIcon(image), "")
            item.setData(Qt.UserRole, image)
            self.bg_image_list.addItem(item)

        self.bg_image_list.itemDoubleClicked.connect(self.set_background_image)
        right_panel_layout.addWidget(self.bg_image_list)

        central_layout.addLayout(left_panel_layout, 1)
        central_layout.addLayout(right_panel_layout, 1)
        main_layout.addLayout(central_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.start_camera()

    @Slot(QListWidgetItem)
    def set_background_image(self, item):
        if item.data(Qt.UserRole):
            self.selected_bg_path = item.data(Qt.UserRole)
            try:
                self.background_image = cv2.imread(self.selected_bg_path)
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
            self.move(event.globalPos() - self.offset)

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
        frame = background_change(self.background_image, frame, self.blur_switch.switch.isChecked(), input_sessiion=self.session)

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
        else:
            self.bg_included_button.setChecked(False)
            self.bg_local_button.setChecked(True)
            self.select_local_bg_image()

    def select_local_bg_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Background Image", "",
                                                   "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            item = QListWidgetItem(QIcon(file_path), "")
            item.setData(Qt.UserRole, file_path)
            self.bg_image_list.addItem(item)

    def startup_register(self):
        """Handle the toggle event for blur background."""
        if self.run_on_startup_switch.switch.isChecked():
            add_to_startup()
        else:
            remove_from_startup()

    def add_cameras(self):
        self.cameras = update_camera_descriptions()
        for camera_detail in self.cameras:
            self.cam_dropdown.addItem(camera_detail)
        self.cam_dropdown.addItem('Sample Video')

done = False
#here is the animation
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\rloading ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rDone!     ')



if __name__ == '__main__':
    import sys

    # ...
    is_startup = ('--startup' in sys.argv)
    print(is_startup)