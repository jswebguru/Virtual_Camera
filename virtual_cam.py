import cv2
import subprocess
import re


def feed_frame_to_vir_cam(proc, frame):
    try:

        # Convert the frame to RGB24
        if frame.shape[2] == 4:  # In case it's RGBA
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Write frame data as bytes to the AkVCamManager stdin
        proc.stdin.write(frame.tobytes())

    except Exception as exx:
        print(f"An error occurred: {exx}")


def get_device_format():
    # Run the command
    cmd = ["akvcammanager", "formats", "AkVCamVideoDevice0"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()

        # Regular expression to match the format "0: RGB24 640x480 30/1 FPS"
        pattern = r"(\d+):\s+\w+\s+(\d+x\d+)"

        # Find all matches
        matches = re.findall(pattern, output)

        # Convert matches to dictionary
        formats_dict = {int(match[0]): match[1] for match in matches}

        return formats_dict

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == '__main__':

    # akv_cam_command = [
    #     'AkVCamManager',
    #     'stream',
    #     '--fps', '30',
    #     'VirtualCamera0',
    #     'RGB24',
    #     '640', '480'
    # ]
    format_dict = get_device_format()
    print('640x480' in format_dict.values())
    # Start the AkVCamManager process
    # akv_cam_proc = subprocess.Popen(akv_cam_command, stdin=subprocess.PIPE)
    # cap = cv2.VideoCapture(0)  # Change to the appropriate video source if necessary
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
