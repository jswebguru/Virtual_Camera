import logging
from rembg import remove, new_session
import cv2
import numpy as np
import time
from replace_with_chroma import detect_dominant_color


def background_change(new_background_image, source_image, blur_checked, chroma_checked, input_session=None):
    if (blur_checked is False) and (new_background_image is None) and chroma_checked is False:
        return source_image
    # Remove the background from source image

    start = time.time()
    if input_session is not None:
        foreground = remove(source_image, session=input_session)
    else:
        foreground = remove(source_image)
    # foreground with alpha channel
    eta_time = time.time() - start
    logging.info(f'ETA time for changing the background is {eta_time}.')
    print(eta_time)
    # Ensure the new background is the same size as the foreground
    height, width, _ = source_image.shape
    if foreground.shape[2] == 3:
        foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2BGRA)

    # Prepare masks for blending
    alpha_channel = foreground[:, :, 3] / 255.0  # Normalized alpha channel
    alpha_mask = np.repeat(alpha_channel[:, :, np.newaxis], 3, axis=2)
    if new_background_image is None:
        new_background_image = cv2.resize(source_image, (width, height))
    else:
        new_background_image = cv2.resize(new_background_image, (width, height))
    if blur_checked:
        # Create a blurred version of the source image
        new_background_image = cv2.GaussianBlur(new_background_image, (21, 21), 0)
    if chroma_checked:
        new_background_image = np.full_like(source_image, detect_dominant_color(source_image, mask=alpha_mask),
                                            dtype=np.uint8)

    # Convert foreground image to have four channels if not already

    # Split channels
    foreground_rgb = foreground[:, :, :3]

    # Blend the images
    combined = (foreground_rgb * alpha_mask + new_background_image * (1 - alpha_mask)).astype(np.uint8)

    return combined


if __name__ == '__main__':
    input_path = 'images/image1.jpg'
    background_path = 'images/image2.jpg'
    unet2p_session = new_session('unet2p')

    # Load images
    front_image = cv2.imread(input_path)
    background_image = cv2.imread(background_path)

    # Replace background
    output_image = background_change(background_image, front_image, True, True, False)

    # Save the result
    cv2.imwrite('output.jpg', output_image)
