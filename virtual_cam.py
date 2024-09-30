import cv2
import subprocess


def feed_frame_to_vir_cam(proc, frame):
    try:
        # Resize the frame to 640x480 if it's not already that size
        frame = cv2.resize(frame, (640, 480))

        # Convert the frame to RGB24
        if frame.shape[2] == 4:  # In case it's RGBA
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Write frame data as bytes to the AkVCamManager stdin
        proc.stdin.write(frame.tobytes())

    except Exception as exx:
        print(f"An error occurred: {exx}")


if __name__ == '__main__':

    akv_cam_command = [
        'AkVCamManager',
        'stream',
        '--fps', '30',
        'VirtualCamera0',
        'RGB24',
        '640', '480'
    ]

    # Start the AkVCamManager process
    akv_cam_proc = subprocess.Popen(akv_cam_command, stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(0)  # Change to the appropriate video source if necessary

    try:
        while True:
            ret, current_frame = cap.read()
            if not ret:
                break

            feed_frame_to_vir_cam(akv_cam_proc, current_frame)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        akv_cam_proc.stdin.close()
        akv_cam_proc.wait()
