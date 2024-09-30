import cv2
from cv2_enumerate_cameras import enumerate_cameras


def get_cameras():
    cameras = []
    for camera_info in enumerate_cameras(cv2.CAP_DSHOW):
        cameras.append(camera_info.name)

    return cameras


def open_camera(index):
    cap = cv2.VideoCapture(index)
    return cap


if __name__ == "__main__":
    print(get_cameras())
