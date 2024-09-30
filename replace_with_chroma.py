import cv2
import numpy as np


def detect_dominant_color(image, mask=None, k=3, attempts=10):
    if mask is not None:
        image = image[mask == 0]

    if len(image) == 0:
        return np.array([0, 255, 0])

        # Reshape the image to a 2D array of pixels
    pixels = image.reshape(-1, 3).astype(np.float32)

    # Define criteria and apply kmeans()  
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, attempts, cv2.KMEANS_PP_CENTERS)

    # Compute the number of pixels assigned to each cluster  
    _, counts = np.unique(labels, return_counts=True)

    # Find the cluster with the maximum number of pixels (dominant color)  
    dominant_index = np.argmax(counts)
    dominant_color = centers[dominant_index]

    return dominant_color.astype(np.int8)


