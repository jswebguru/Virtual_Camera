import logging
import os.path
import subprocess
import sys
import cv2
import numpy as np
from background_removal import background_change
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QComboBox,
                               QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QWidget, QFileDialog, QPushButton, QSystemTrayIcon, QMenu, QAbstractItemView)
from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter, QPainterPath, QAction
from PySide6.QtCore import QTimer, Qt, QPoint, QRectF, Slot, QEvent
from Toggle_Switch import LabeledToggleSwitch, RoundedItemDelegate
from get_cameras import get_cameras
from get_image_path import list_files_in_directory
from replace_with_chroma import find_dominant_colors
from startup_config import add_to_startup, remove_from_startup, check_startup_registry
from virtual_cam import feed_frame_to_vir_cam, resize, pad
import concurrent.futures
from ai_engine import Predictor
import json

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
WINDOW_WIDTH = 1025
WINDOW_HEIGHT = 600


class VirtualCameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.included = True
        self.cur_frame = None
        self.chromakey = None
        self.camera_index = 0
        self.background_image = None
        self.scroll_position = 0
        self.selected_bg_path = None
        self.selected_bg_index = 0
        self._pool = concurrent.futures.ThreadPoolExecutor()

        if os.path.exists('images'):
            self.pre_path = ''
        else:
            self.pre_path = 'C:/Program Files/Meetn Bonus App/'
        self.cameras = None
        self.load_settings(self.pre_path + 'res/settings.json')
        self.config = self.pre_path + 'res/model/deploy.yaml'
        self.setWindowTitle("Meet Bonus App")
        self.cur_vcam_width = 640
        self.cur_vcam_height = 480
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(f'{self.pre_path}res/tray.jpg'))  # Make sure to provide an icon path

        self.tray_menu = QMenu(self)
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)

        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.offset = QPoint()
        # Start the AkVCamManager process
        self.akv_cam_proc = None
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
                icon-size: 23px; 
                border-radius: 5px; 
                background-color: gray;  
            }}  
            QPushButton#ControlButton:hover {{  
                border: none;  
                icon-size: 23px; 
                border-radius: 5px; 
                icon: url({self.pre_path}res/hover/minimize.png);   
            }}
            QPushButton#MinimizeTrayButton {{ 
                border: none;  
                icon: url({self.pre_path}res/tray.png);   
                icon-size: 25px;  
                border-radius: 5px;
                background-color: gray;  
            }}  
            QPushButton#MinimizeTrayButton:hover {{  
                border: none;  
                icon-size: 25px;  
                border-radius: 5px;
                icon: url({self.pre_path}res/hover/tray.png);   
            }}   
            QPushButton#CloseButton {{ 
                border: none;  
                icon: url({self.pre_path}res/close.png);  
                icon-size: 23px;       
                border-radius: 5px;       
                background-color: gray;  
            }} 
            QPushButton#CloseButton:hover {{  
                border: none;  
                icon-size: 23px;  
                border-radius: 5px;
                icon: url({self.pre_path}res/hover/close.png);  
            }}  
            QPushButton#FolderOpen {{ 
                border: 2px;  
                icon: url({self.pre_path}res/open-folder.png);  
                icon-size: 30px; 
                height: 40px;      
                border-radius: 5px;       
                background-color: gray;  
            }} 
            QPushButton#FolderOpen:hover {{  
                border: 2px;  
                icon-size: 30px;  
                height: 40px;
                border-radius: 5px;
                icon: url({self.pre_path}res/hover/open-folder.png);  
            }} 

        """)

        main_layout = QVBoxLayout()

        title_bar_layout = QHBoxLayout()

        self.title_label = QLabel("Meetn Bonus App")
        self.title_label.setObjectName("Title")
        title_bar_layout.addWidget(self.title_label)

        control_button_layout = QHBoxLayout()

        minimize_tray_button = QPushButton('')
        minimize_tray_button.setObjectName("MinimizeTrayButton")
        minimize_tray_button.setFixedWidth(CONTROL_BUTTON_SIZE)
        minimize_tray_button.setFixedHeight(CONTROL_BUTTON_SIZE)
        minimize_tray_button.clicked.connect(self.minimize_to_tray)

        control_button_layout.addWidget(minimize_tray_button)

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
        self.camera_label.setFixedHeight(480)
        self.camera_label.setFixedWidth(640)
        left_panel_layout.addWidget(self.camera_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_feed)
        self.cap = None

        features_layout = QVBoxLayout()

        self.green_screen_switch = LabeledToggleSwitch("I have a green or blue screen", self)
        self.green_screen_switch.switch.stateChanged.connect(self.green_switch_changed)
        features_layout.addWidget(self.green_screen_switch)
        if self.chromakey is not None:
            self.chromakey = np.array(self.chromakey)
            self.green_screen_switch.switch.setChecked(True)
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
        self.model = Predictor(self.config)
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
        self.bg_included_button.setChecked(self.included)

        # Button to open directory - initially hidden
        self.select_directory_button = QPushButton("Select Directory")
        self.select_directory_button.setObjectName("FolderOpen")
        self.select_directory_button.setVisible(False)
        self.select_directory_button.clicked.connect(self.select_local_bg_folder)

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
        self.folder_dropdown = QComboBox()
        right_panel_layout.addWidget(self.folder_dropdown)
        right_panel_layout.addWidget(self.select_directory_button)

        # New: ComboBox for current folder path

        self.bg_image_list = QListWidget()
        self.bg_image_list.setViewMode(QListWidget.IconMode)
        self.bg_image_list.setIconSize(QPixmap(150, 120).size())

        self.bg_image_list.setItemDelegate(RoundedItemDelegate())
        self.bg_image_list.setSpacing(5)
        self.bg_image_list.setDragEnabled(False)
        self.bg_image_list.itemClicked.connect(self.set_background_image)
        if self.included:
            self.update_folder_list(self.pre_path + 'images')
        else:
            self.bg_included_button.setChecked(False)
            self.bg_local_button.setChecked(True)
            self.folder_dropdown.setVisible(False)
            self.select_directory_button.setVisible(True)
        if self.selected_bg_path is not None:
            self.update_image_list(os.path.dirname(self.pre_path + self.selected_bg_path))
        else:
            self.update_image_list(self.pre_path + 'images/Abstract')
        right_panel_layout.addWidget(self.bg_image_list)

        central_layout.addLayout(left_panel_layout, 1)
        central_layout.addLayout(right_panel_layout, 1)
        main_layout.addLayout(central_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.start_camera(self.camera_index)
        if type(self.camera_index) is str:
            self.cam_dropdown.setCurrentIndex(len(self.cameras))
        self.cam_dropdown.installEventFilter(self)
        self.folder_dropdown.installEventFilter(self)
        self.folder_dropdown.currentIndexChanged.connect(self.folder_selection_changed)

        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Set the window size
        self.center()  # Center the window on the screen

        item = self.bg_image_list.item(self.selected_bg_index)
        item.setSelected(True)
        self.bg_image_list.scrollToItem(item, QAbstractItemView.PositionAtTop)

    def save_settings(self, file_path='res/settings.json'):
        settings = {
            'camera': self.camera_index,
            'chroma': self.chromakey if self.chromakey is None else self.chromakey.tolist(),
            'background': [self.selected_bg_index, self.selected_bg_path],
            'scroll': self.bg_image_list.verticalScrollBar().value(),
            'included': self.bg_included_button.isChecked()
        }

        try:
            with open(file_path, 'w') as file:
                json.dump(settings, file, indent=4)
            logging.info(f"Settings successfully saved to {file_path}.")
        except Exception as e:
            logging.info(f"Failed to save settings: {e}")

    def load_settings(self, file_path='res/settings.json'):
        """
        Load settings from a JSON file.

        :param file_path: Path of the JSON file to load.
        :return: A dictionary containing the loaded settings.
        """
        try:
            with open(file_path, 'r') as file:
                settings = json.load(file)
        except FileNotFoundError:
            logging.info(f"No settings file found at {file_path}.")
        except Exception as e:
            logging.info(f"Failed to load settings: {e}")

        self.camera_index = settings['camera']
        self.chromakey = settings['chroma']
        self.selected_bg_index = settings['background'][0]
        self.scroll_position = settings['scroll']
        self.selected_bg_path = settings['background'][1]
        self.background_image = cv2.imread(self.selected_bg_path)
        self.included = settings['included']

    def determine_chromakey(self):
        if self.cur_frame is None:
            logging.info('Current frame is not selected.')
            return
        # Convert from RGB to BGR (since OpenCV uses BGR)
        input_image = cv2.cvtColor(self.cur_frame, cv2.COLOR_RGB2BGR)
        initial_mask = self.model.run(input_image, input_image, only_mask=True)
        original_background = input_image * (1 - initial_mask[:, :, np.newaxis])

        # Find the most dominant color assuming it's the background chromakey
        self.chromakey = find_dominant_colors(original_background)

    def green_switch_changed(self):
        if self.green_screen_switch.switch.isChecked():
            self._pool.submit(self.determine_chromakey)
        else:
            self.chromakey = None

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
            normalized_path1 = list(map(os.path.normpath, folders))

            try:
                index = normalized_path1.index(os.path.normpath(os.path.dirname(self.selected_bg_path)))
            except Exception as e:
                index = 0
                logging.info('Found non path: ', e)
            simplified_folders = list(map(lambda folder: folder.split('/')[-1], folders))
            self.folder_dropdown.addItems(simplified_folders)
            self.folder_dropdown.setCurrentIndex(index)

    def update_image_list(self, path):
        self.bg_image_list.clear()
        self.bg_image_list.scrollToTop()
        images = list_files_in_directory(path)
        if images[0] != self.pre_path + 'res/none.png':
            images.insert(0, self.pre_path + 'res/none.png')

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
            self.selected_bg_index = self.bg_image_list.row(item)
            try:
                if self.bg_image_list.row(item) == 0:
                    self.background_image = None
                else:
                    self.background_image = cv2.imread(self.selected_bg_path)

            except Exception as e:
                logging.info(f'{e} has occurred.')

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
            self.offset = QPoint(int(event.position().x()), int(event.position().y()))

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    def closeEvent(self, event):

        if self.tray_icon.isVisible():
            self.tray_icon.hide()
        self.stop_camera()
        self.akv_cam_proc.stdin.close()
        self.akv_cam_proc.wait()
        self.save_settings(self.pre_path + 'res/settings.json')
        event.accept()

    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def start_camera(self, source=0):
        self.camera_index = source
        if isinstance(source, str):
            self.cap = cv2.VideoCapture(source)
        else:

            self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            self.camera_label.setText("Failed to open the camera.")
            return
        if self.akv_cam_proc is None:
            self.akv_cam_proc = subprocess.Popen(AKV_CAM_COMMAND, stdin=subprocess.PIPE,
                                                 creationflags=subprocess.CREATE_NO_WINDOW)
        ret, cur_frame = self.cap.read()
        if self.green_screen_switch.switch.isChecked() and ret:
            self.cur_frame = cur_frame
            self.green_switch_changed()
        self.timer.start(30)

    def update_camera_feed(self):
        ret, cur_frame = self.cap.read()
        if not ret:
            self.camera_label.setText("Failed to capture image.")
            return
        self.cur_frame = cur_frame
        cur_frame, new_height = resize(cur_frame)
        cool_frame = background_change(self.background_image, cur_frame, self.blur_switch.switch.isChecked(),
                                       self.chromakey, input_session=self.model)
        cool_frame = pad(cool_frame, new_height)
        height, width, channel = cool_frame.shape
        cool_frame = cv2.cvtColor(cool_frame, cv2.COLOR_RGB2BGR)
        step = channel * width
        try:
            feed_frame_to_vir_cam(self.akv_cam_proc, cool_frame)

        except Exception as e:
            logging.info(f"An error occurred1: {e}")

        q_img = QImage(cool_frame.data, width, height, step, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(q_img))

    def stop_camera(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()

    def select_camera_source(self, index):
        self.stop_camera()
        if index == len(self.cameras):
            index = self.pre_path + 'videos/output1.mp4'
        self.start_camera(index)

    def switch_bg_selection(self, mode):
        if mode == "included":
            self.bg_included_button.setChecked(True)
            self.bg_local_button.setChecked(False)
            self.folder_dropdown.setVisible(True)
            self.select_directory_button.setVisible(False)
            self.update_folder_list(self.pre_path + 'images')
        else:
            self.bg_included_button.setChecked(False)
            self.bg_local_button.setChecked(True)
            self.folder_dropdown.setVisible(False)
            self.select_directory_button.setVisible(True)
            self.select_local_bg_folder()

    def select_local_bg_folder(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec():
            folder_path = dialog.selectedFiles()[0]
            if folder_path:
                self.background_image = None
                self._pool.submit(self.update_image_list, folder_path)

    def folder_selection_changed(self, index):
        folder_name = self.folder_dropdown.itemText(index)
        if folder_name:
            selected_folder = folder_name
            self._pool.submit(self.update_image_list, selected_folder)
            # self.update_image_list(selected_folder)

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

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.tray_icon.hide()

    def exit_application(self):
        self.close()
