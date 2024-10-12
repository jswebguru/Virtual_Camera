import argparse
import cv2
from paddleseg.utils import logger
from ai_engine import Predictor


def parse_args():
    parser = argparse.ArgumentParser(
        description='PP-HumanSeg inference for video')
    parser.add_argument(
        "--config",
        help="The config file of the inference model.",
        type=str,
        default='model/deploy.yaml')

    parser.add_argument(
        '--bg_img_path',
        help='Background image path for replacing. If not specified, a white background is used',
        type=str,
        default='data/images/bg_2.jpg')
    parser.add_argument(
        '--bg_video_path', help='Background video path for replacing', type=str)

    parser.add_argument(
        '--use_post_process', help='Use post process.', action='store_true')

    return parser.parse_args()


def background_removal(img, bg, predictor):
    out = predictor.run(img, bg)
    return out


if __name__ == "__main__":
    args = parse_args()
    bg = cv2.imread(args.bg_img_path)
    logger.info("Input: camera")
    logger.info("Create predictor...")
    predictor = Predictor(args)

    logger.info("Start predicting...")
    img = cv2.imread('family-pier-man-woman-39691.png')
    out = background_removal(img, bg, predictor)
    cv2.imwrite('result.jpg', out)
    cv2.imshow('PP-HumanSeg', out)
    cv2.waitKey(0)
