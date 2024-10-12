import cv2
import numpy as np


def resize(image, target_width=640, target_height=480):
    # Get current dimensions
    if image.shape[2] == 4:  # In case it's RGBA
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

    original_height, original_width = image.shape[:2]

    # Calculate the scaling factor to match the target width
    scale_factor = target_width / original_width
    new_width = target_width
    new_height = int(original_height * scale_factor)
    frame_rgb = cv2.resize(image, (new_width, new_height))
    frame_padded = np.zeros((target_height, target_width, 4), dtype=np.uint8)

    # Overlay the resized frame on the middle of the canvas
    y_offset = (target_height - new_height) // 2
    x_offset = 0

    # Convert BGR to RGB and add alpha channel, set alpha to 255 (opaque)
    frame_rgba = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2RGBA)
    frame_rgba[:, :, 3] = 255  # Set alpha channel to fully opaque

    # Place the resized RGBA frame onto the center of the padded frame
    frame_padded[y_offset:y_offset + new_height, x_offset:x_offset + target_width] = frame_rgba
    final_frame = cv2.cvtColor(frame_padded, cv2.COLOR_RGBA2RGB)

    return final_frame


def feed_frame_to_vir_cam(proc, frame):
    try:

        # Resize the frame to 640x480 if it's not already that size

        proc.stdin.write(frame.tobytes())
        # proc.stdin.flush()
        # proc.communicate(frame.tobytes())
    except Exception as exx:
        print(f"An error occurred : {exx}")


if __name__ == '__main__':
    # akv_cam_proc = None
    # akv_cam_command = [
    #     'AkVCamManager',
    #     'stream',
    #     '--fps', '30',
    #     'AkVCamVideoDevice0',
    #     'RGB24',
    #     '640', '480'
    # ]
    # # cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Change to the appropriate video source if necessary
    # cap = cv2.VideoCapture('videos/output.mp4')
    #     # Start the AkVCamManager process
    # akv_cam_proc = subprocess.Popen(akv_cam_command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE)
    #
    # try:
    #     while True:
    #         ret, current_frame = cap.read()
    #         if not ret:
    #             break
    #
    #         feed_frame_to_vir_cam(akv_cam_proc, current_frame)
    #
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #
    # finally:
    #     cap.release()
    #     cv2.destroyAllWindows()
    #     akv_cam_proc.stdin.close()
    #     akv_cam_proc.wait()
    pass
