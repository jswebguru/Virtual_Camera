import logging
from rembg import remove, new_session
import cv2
import numpy as np
import time
from replace_with_chroma import create_mask


def background_change(new_background_image, source_image, blur_checked, chromakey, input_session=None):
    if (blur_checked is False) and (new_background_image is None):
        return source_image
    # Remove the background from source image
    height, width, _ = source_image.shape
    if chromakey is not None:
        mask = create_mask(source_image, chromakey, 30)
        alpha_mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        foreground = source_image * mask[:, :, np.newaxis]

    else:
        start = time.time()
        if input_session is not None:
            foreground = remove(source_image, session=input_session)
        else:
            foreground = remove(source_image)
        # foreground with alpha channel
        eta_time = time.time() - start
        logging.info(f'ETA time for changing the background is {eta_time}.')
        # Ensure the new background is the same size as the foreground
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
