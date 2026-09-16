import cv2
import numpy as np


class ImageProcessor:
    @staticmethod
    def _to_grayscale(image):
        if image is None:
            raise ValueError("Image data is required for OCR.")

        if len(image.shape) == 2:
            return image
        if image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def _resize(image, max_width=1800):
        height, width = image.shape[:2]
        if width <= max_width:
            return image
        scale = max_width / float(width)
        return cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _remove_noise(gray):
        return cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    @staticmethod
    def _enhance_contrast(gray):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    @staticmethod
    def _deskew(gray):
        coords = np.column_stack(np.where(gray < 255))
        if coords.size == 0:
            return gray
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 0.5:
            return gray

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    @staticmethod
    def _threshold(gray):
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )

    @staticmethod
    def preprocess(image):
        gray = ImageProcessor._to_grayscale(image)
        gray = ImageProcessor._resize(gray)
        gray = ImageProcessor._remove_noise(gray)
        gray = ImageProcessor._enhance_contrast(gray)
        gray = ImageProcessor._deskew(gray)
        thresh = ImageProcessor._threshold(gray)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
