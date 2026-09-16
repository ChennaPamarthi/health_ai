import os

os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "False")

import fitz
import numpy as np
import cv2

from PIL import Image
from paddleocr import PaddleOCR

from .file_service import FileService
from .image_processor import ImageProcessor
from .text_cleaner import TextCleaner


class OCRService:
    _ocr = None

    @classmethod
    def get_model(cls):
        if cls._ocr is None:
            cls._ocr = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                engine="onnxruntime",
            )
        return cls._ocr

    @staticmethod
    def _extract_text_from_result(result):
        lines = []
        confidences = []

        if not result:
            return "", 0.0

        for page in result:
            if not page:
                continue

            if isinstance(page, dict):
                texts = page.get("rec_texts") or []
                scores = page.get("rec_scores") or []
                for index, text_chunk in enumerate(texts):
                    confidence = scores[index] if index < len(scores) else 0
                    if confidence >= 0.50 and text_chunk:
                        lines.append(str(text_chunk))
                        confidences.append(float(confidence))
                continue

            for item in page:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue

                text_info = item[1]
                if not isinstance(text_info, (list, tuple)) or len(text_info) < 2:
                    continue

                text_chunk = text_info[0] or ""
                confidence = text_info[1] or 0

                if confidence < 0.50 or not text_chunk:
                    continue

                lines.append(text_chunk)
                confidences.append(float(confidence))

        text = "\n".join(lines)
        text = TextCleaner.clean(text)
        text = TextCleaner.remove_duplicate_lines(text)
        text = TextCleaner.merge_prescription_lines(text)
        average_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        return text, average_confidence

    @classmethod
    def extract_image(cls, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Unable to read image file for OCR.")

        processed = ImageProcessor.preprocess(image)
        result = cls.get_model().ocr(processed)
        text, _ = cls._extract_text_from_result(result)
        return text

    @classmethod
    def extract_image_with_confidence(cls, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Unable to read image file for OCR.")

        processed = ImageProcessor.preprocess(image)
        result = cls.get_model().ocr(processed)
        text, confidence = cls._extract_text_from_result(result)
        return {
            "text": text,
            "confidence": confidence,
        }

    @classmethod
    def extract_pdf(cls, pdf_path):
        lines = []
        confidences = []
        model = cls.get_model()

        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                page_text = page.get_text("text").strip()
                if page_text:
                    lines.append(page_text)
                    confidences.append(1.0)
                    continue

                pix = page.get_pixmap(dpi=300)
                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples,
                )
                image_array = np.array(image)
                processed = ImageProcessor.preprocess(image_array)
                result = model.ocr(processed)
                page_text, page_confidence = cls._extract_text_from_result(result)
                if page_text:
                    lines.append(page_text)
                    confidences.append(page_confidence)

        text = "\n".join(lines)
        text = TextCleaner.clean(text)
        text = TextCleaner.remove_duplicate_lines(text)
        text = TextCleaner.merge_prescription_lines(text)
        average_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        return {
            "text": text,
            "confidence": average_confidence,
        }

    @classmethod
    def extract_text(cls, file_path):
        if FileService.is_pdf(file_path):
            return cls.extract_pdf(file_path)["text"]

        if FileService.is_image(file_path):
            return cls.extract_image(file_path)

        return ""

    @classmethod
    def extract_text_with_confidence(cls, file_path):
        if FileService.is_pdf(file_path):
            return cls.extract_pdf(file_path)

        if FileService.is_image(file_path):
            return cls.extract_image_with_confidence(file_path)

        return {"text": "", "confidence": 0.0}
