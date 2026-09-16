from .exceptions import InvalidMedicineData
from .schemas import DocumentExtractionSchema


class AIValidator:
    FREQUENCY_MAP = {
        "morning": "Morning",
        "afternoon": "Afternoon",
        "evening": "Night",
        "night": "Night",
        "1-0-1": "1-0-1",
        "0-1-0": "0-1-0",
        "1-1-1": "1-1-1",
        "before food": "Before Food",
        "after food": "After Food",
        "with food": "With Food",
        "anytime": "Anytime",
    }

    @classmethod
    def _sanitize_value(cls, value):
        if value is None:
            return ""
        if isinstance(value, dict):
            return {key: cls._sanitize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._sanitize_value(item) for item in value]
        if isinstance(value, tuple):
            return [cls._sanitize_value(item) for item in value]
        return value

    @classmethod
    def _normalize_frequency(cls, value):
        if value in (None, ""):
            return []
        if isinstance(value, str):
            items = [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
        elif isinstance(value, (list, tuple, set)):
            items = [str(item).strip() for item in value if str(item).strip()]
        else:
            items = [str(value).strip()]

        normalized = []
        for item in items:
            key = item.lower()
            normalized.append(cls.FREQUENCY_MAP.get(key, item.title()))
        return list(dict.fromkeys(normalized))

    @classmethod
    def _normalize_payload(cls, data):
        payload = cls._sanitize_value(dict(data or {}))
        payload["classification"] = str(payload.get("classification", "printed") or "printed").lower()
        payload["confidence"] = float(payload.get("confidence") or 0.0)
        payload["ocr_confidence"] = float(payload.get("ocr_confidence") or 0.0)
        payload["vision_confidence"] = float(payload.get("vision_confidence") or 0.0)
        payload["needs_review"] = bool(payload.get("needs_review", False))

        medicines = []
        for item in payload.get("medicines", []) or []:
            if not isinstance(item, dict):
                continue
            normalized_item = dict(item)
            normalized_item["frequency"] = cls._normalize_frequency(normalized_item.get("frequency", []))
            medicines.append(normalized_item)
        payload["medicines"] = medicines
        return payload

    @staticmethod
    def validate(data):
        try:
            normalized = AIValidator._normalize_payload(data)
            validated = DocumentExtractionSchema(**normalized)
            return validated.model_dump()
        except Exception as error:
            raise InvalidMedicineData(str(error))
