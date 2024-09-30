import logging

from rembg import remove, new_session
import cv2
import numpy as np
import time


def blur_background(source_image, input_session=None):
    # Remove the background from source image, segmenting the person
    start = time.time()

    if input_session is not None:
        foreground = remove(source_image, session=input_session)
    else:
        foreground = remove(source_image)

    eta_time = time.time() - start
    # Convert foreground image to have four channels if not already
    if foreground.shape[2] == 3:
        foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2BGRA)

        # Create the alpha mask from the alpha channel
    alpha_channel = foreground[:, :, 3] / 255.0  # Normalized alpha channel
    alpha_mask = np.repeat(alpha_channel[:, :, np.newaxis], 3, axis=2)

    # Split channels
    foreground_rgb = foreground[:, :, :3]

    # Create a blurred version of the source image
    blurred_background = cv2.GaussianBlur(source_image, (21, 21), 0)

    # Blend the images: Keep the foreground unchanged, blend the blurred background
    combined = (foreground_rgb * alpha_mask + blurred_background * (1 - alpha_mask)).astype(np.uint8)

    return combined

if __name__ == '__main__':

    background_path = 'fred.jpg'
    unet2p_session = new_session('unet2p')
    background_image = cv2.imread(background_path)
    output_image = blur_background(background_image, unet2p_session)

    # Save the result
    cv2.imwrite('output.jpg', output_image)