import cv2
import numpy as np
from rembg import remove


def find_dominant_colors(image, k=3):

    pixels = image.reshape((-1, 3))

    # Convert to float32 for kmeans
    pixels = np.float32(pixels)

    # Define criteria and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)

    # Convert centers to integer
    centers = np.uint8(centers)

    # Count frequency of pixels in each cluster
    counts = np.bincount(labels.flatten())

    # Sort the colors by frequency
    sorted_indices = np.argsort(-counts)
    sorted_centers = centers[sorted_indices]

    return sorted_centers[0]


def create_mask(image, chroma_key_color, threshold):

    yCrCb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
    transform_matrix = np.array([
        [0.299, 0.587, 0.114],
        [-0.1687, -0.3313, 0.5],
        [0.5, -0.4187, -0.0813]
    ])
    chroma = transform_matrix @ chroma_key_color + np.array([0, 128, 128])
    chroma = chroma.astype(np.float32)
    distance = np.sqrt((yCrCb[:, :, 1] - chroma[1]) ** 2 + (yCrCb[:, :, 2] - chroma[2]) ** 2)
    # Create a binary mask: 0 for background, 1 for foreground
    mask = (distance > threshold).astype(np.uint8)
    return mask


if __name__ == "__main__":
    input_path = 'images/image.jpg'
    input_image = cv2.imread(input_path)
    input_image_rgb = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)

    # Create the initial mask
    initial_mask = remove(input_image, only_mask=True).astype(float) / 255.0

    # Extract original background using the initial mask
    original_background = input_image * (1 - initial_mask[:, :, np.newaxis])

    # Find the most dominant color assuming it's the background chromakey
    chromakey_color = find_dominant_colors(original_background)
    # Refine the mask using the chroma key
    refined_mask = create_mask(input_image_rgb, chromakey_color, 30)
    cv2.imwrite('refined_mask.jpg', refined_mask * 255)
    # Apply the refined mask
    separated_foreground = input_image * refined_mask[:, :, np.newaxis]
    # Save/Display the result
    cv2.imwrite('refined_foreground.png', separated_foreground)