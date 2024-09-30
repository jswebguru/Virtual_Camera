import cv2
import win32com.client


def get_camera_details_windows():
    cameras = []
    wmi = win32com.client.GetObject("winmgmts:")
    for item in wmi.InstancesOf("Win32_PnPEntity"):
        # if "camera" in (item.Description or "").lower() or "video" in (item.Description or "").lower():
        cameras.append(item.Name)
        print(item.Name)
    return cameras


def get_available_cameras(max_cameras=3):
    available_cameras = []

    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        # print(i)
        try:
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        except Exception as e:
            print(e, ' has occurred.')
    return available_cameras


def update_camera_descriptions():
    camera_details = get_camera_details_windows()
    # available_cameras = get_available_cameras()
    # mapped_descriptions = []
    # print(camera_details, available_cameras)
    # Attempt to match each available camera to a device description
    # for idx in available_cameras:
    #     description = f"Camera {idx}"
    #     if idx < len(camera_details):
    #         # Assign description based on the index
    #         description_items = list(camera_details.items())
    #         description = description_items[idx][1]
    #         print(description)
    #         mapped_descriptions.append((description, idx))

    return camera_details


import win32com.client


if __name__ == '__main__':
    wmi = win32com.client.GetObject("winmgmts:")
    for usb in wmi.InstancesOf("Win32_USBHub"):
        print(usb.deviceID)
    # print(get_camera_details_windows())
