import json
import re
import time
from datetime import datetime

from health.ai import AIValidator
from health.ai.prompt_builder import PromptBuilder
from health.agents import AgentOrchestrator, DocumentClassifierAgent

from .ai_service import AIService


class DocumentService:
    CONFIDENCE_THRESHOLD = 0.65
    DATE_FORMATS = (
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    )

    @staticmethod
    def _parse_date(value):
        value = str(value or "").strip()
        for date_format in DocumentService.DATE_FORMATS:
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                continue
        return ""

    @staticmethod
    def _frequency_from_dosage(dosage):
        dosage_lower = str(dosage or "").lower().replace("moming", "morning")
        frequency = []
        markers = (
            ("morning", "Morning"),
            ("morn", "Morning"),
            ("afternoon", "Afternoon"),
            ("aft", "Afternoon"),
            ("evening", "Evening"),
            ("eve", "Evening"),
            ("night", "Night"),
        )
        for marker, label in markers:
            if re.search(rf"\b{re.escape(marker)}\b", dosage_lower) and label not in frequency:
                frequency.append(label)
        return frequency

    @staticmethod
    def _food_instruction_from_text(value):
        value_lower = str(value or "").lower()
        if "before food" in value_lower:
            return "Before Food"
        if "after food" in value_lower:
            return "After Food"
        if "with food" in value_lower:
            return "With Food"
        return ""

    @staticmethod
    def _clean_document_row(value):
        value = str(value or "").replace("Moming", "Morning").replace("moming", "morning")
        value = value.replace("Tot:", "T:").replace("Tott:", "T:")
        return re.sub(r"\s+", " ", value).strip(" -:")

    @classmethod
    def _medicine_from_row_text(cls, row_text):
        row_text = cls._clean_document_row(row_text)
        row_text = re.sub(r"^\d+\)\s*", "", row_text).strip()
        name_match = re.match(
            r"(?P<name>(?:(?:TAB|CAP|SYP|SYR|INJ)\.?\s*)?[A-Z0-9][A-Z0-9 .&/-]*?)(?=\s+\d+(?:/\d+)?\s*(?:Morning|Moming|Morn|Aft|Afternoon|Eve|Evening|Night)\b)",
            row_text,
            re.IGNORECASE,
        )
        duration_match = re.search(
            r"(?P<duration>\d+\s*(?:Days?|Weeks?|Months?)\s*(?:\([^)]*\))?)",
            row_text,
            re.IGNORECASE,
        )

        if not name_match or not duration_match:
            return None

        name = cls._clean_document_row(name_match.group("name"))
        dosage = cls._clean_document_row(row_text[name_match.end():duration_match.start()])
        duration = cls._clean_document_row(duration_match.group("duration"))
        trailing_instruction = cls._clean_document_row(row_text[duration_match.end():])
        food_instruction = cls._food_instruction_from_text(f"{dosage} {duration} {trailing_instruction}")

        if not name or not dosage:
            return None

        return {
            "medicine_name": name,
            "dosage": dosage,
            "quantity": "1",
            "frequency": cls._frequency_from_dosage(dosage),
            "food_instruction": food_instruction,
            "duration": duration,
            "strength": "",
            "special_instruction": "",
        }

    @classmethod
    def _parse_numbered_medicine_rows(cls, text):
        rows = []
        matches = list(re.finditer(r"(?m)(?:^|\n)\s*\d+\)\s*", text))
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            row_text = text[start:end]
            row_text = re.split(
                r"\n\s*(?:Advice\s+Given|Follow\s*Up|Charts|Signature)\b",
                row_text,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]
            medicine = cls._medicine_from_row_text(row_text)
            if medicine:
                rows.append(medicine)
        return rows

    @classmethod
    def _parse_printed_prescription_text(cls, text, document_type="Prescription"):
        text = str(text or "")
        medicines = []
        row_pattern = re.compile(
            r"\b\d+\)\s*"
            r"(?P<name>(?:(?:TAB|CAP|SYP|SYR|INJ)\.?\s*)?[A-Z0-9][A-Z0-9 .&/-]*?)\s+"
            r"(?P<dosage>(?:\d+(?:/\d+)?\s*(?:Morning|Moming|Morn|Aft|Afternoon|Eve|Evening|Night)"
            r"[^\n]*?))\s+"
            r"(?P<duration>\d+\s*(?:Days?|Weeks?|Months?)\s*(?:\([^)]*\))?)",
            re.IGNORECASE,
        )

        for match in row_pattern.finditer(text):
            name = cls._clean_document_row(match.group("name"))
            dosage = cls._clean_document_row(match.group("dosage"))
            duration = cls._clean_document_row(match.group("duration"))
            if not name:
                continue
            trailing_instruction = cls._clean_document_row(text[match.end(): match.end() + 80])
            food_instruction = cls._food_instruction_from_text(f"{dosage} {duration} {trailing_instruction}")
            medicines.append(
                {
                    "medicine_name": name,
                    "dosage": dosage,
                    "quantity": "1",
                    "frequency": cls._frequency_from_dosage(dosage),
                    "food_instruction": food_instruction,
                    "duration": duration,
                    "strength": "",
                    "special_instruction": "",
                }
            )

        if not medicines:
            medicines = cls._parse_numbered_medicine_rows(text)

        date_match = re.search(
            r"\bDate\s*:\s*([0-9]{1,2}[-/][A-Za-z0-9]{2,9}[-/][0-9]{4})",
            text,
            re.IGNORECASE,
        )
        follow_up_match = re.search(
            r"\bFollow\s*Up\s*:\s*([0-9]{1,2}[-/][A-Za-z0-9]{1,9}[-/][0-9]{4})",
            text,
            re.IGNORECASE,
        )
        doctor_match = re.search(r"\bDr\.?\s*([A-Z][A-Z .-]*)", text, re.IGNORECASE)
        advice_match = re.search(
            r"Advice\s+Given\s*:?\s*(.+?)(?:\n\s*Follow\s*Up|\n\s*Charts|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        return {
            "document_type": document_type or "Prescription",
            "classification": "printed",
            "confidence": 0.72 if medicines else 0.0,
            "needs_review": True,
            "doctor_name": f"Dr. {doctor_match.group(1).strip()}" if doctor_match else "",
            "hospital_name": "",
            "diagnosis": "",
            "prescription_date": cls._parse_date(date_match.group(1)) if date_match else "",
            "review_date": cls._parse_date(follow_up_match.group(1)) if follow_up_match else "",
            "appointment_date": "",
            "appointment_time": "",
            "department": "",
            "purpose": "",
            "report_title": "",
            "report_summary": "",
            "findings": "",
            "recommendations": "",
            "report_date": "",
            "notes": re.sub(r"\s+", " ", advice_match.group(1)).strip() if advice_match else "",
            "medicines": medicines,
        }

    @staticmethod
    def _merge_prescription_payload(parsed, fallback):
        parsed = dict(parsed or {})
        fallback = dict(fallback or {})
        if fallback.get("medicines") and not parsed.get("medicines"):
            parsed["medicines"] = fallback["medicines"]
        for key, value in fallback.items():
            if key == "medicines":
                continue
            if value not in ("", [], None) and parsed.get(key) in ("", [], None):
                parsed[key] = value
        return parsed

    @staticmethod
    def _default_payload(document_type="Other"):
        return AIValidator.validate(
            {
                "document_type": document_type or "Other",
                "classification": "printed",
                "confidence": 0.0,
                "vision_confidence": 0.0,
                "needs_review": True,
                "medicines": [],
            }
        )

    @classmethod
    def _build_llm_payload(cls, file_path, document_type="Other", classification="printed"):
        ai_service = AIService()
        try:
            parsed = ai_service.analyze_image(
                prompt=PromptBuilder.document_prompt("", document_type=document_type or "Other"),
                file_path=file_path,
                system_prompt=(
                    "Extract structured data directly from this medical document image or PDF. "
                    "Support both handwritten and computer-printed medical documents. "
                    "For prescriptions, extract every medicine into the medicines array with medicine name, dosage, "
                    "frequency, duration, food instruction, quantity, strength, and special instruction when visible. "
                    "For appointments, extract doctor, hospital, department, appointment date, appointment time, purpose, and notes. "
                    "For reports and scans, extract report title, report date, summary, findings, recommendations, and notes. "
                    "Do not skip medicine rows that appear in a table. Return only validated JSON."
                ),
            )
        except Exception:
            fallback = cls._default_payload(document_type=document_type)
            fallback["classification"] = classification
            return fallback, json.dumps(fallback, indent=2), 0.0

        try:
            parsed["vision_confidence"] = float(parsed.get("confidence") or 0.0)
        except (TypeError, ValueError):
            parsed["vision_confidence"] = 0.0
        parsed["ocr_confidence"] = 0.0
        parsed["classification"] = classification
        parsed["needs_review"] = parsed["vision_confidence"] < cls.CONFIDENCE_THRESHOLD
        validated = AIValidator.validate(parsed)
        return validated, json.dumps(validated, indent=2), parsed["vision_confidence"]

    @staticmethod
    def _should_auto_process(payload):
        if not isinstance(payload, dict):
            return False
        if payload.get("medicines"):
            return True
        document_type = str(payload.get("document_type", "")).strip()
        if document_type == "Appointment":
            return True
        if document_type in {"Blood Report", "MRI", "ECG", "X-Ray", "Other"} and (
            payload.get("report_title")
            or payload.get("report_summary")
            or payload.get("findings")
            or payload.get("recommendations")
            or payload.get("notes")
        ):
            return True
        if payload.get("appointment_date") or payload.get("appointment_time") or payload.get("purpose"):
            return True
        if payload.get("report_title") or payload.get("report_summary") or payload.get("findings"):
            return True
        return False

    @staticmethod
    def _resolve_document_type(document, payload):
        if payload.get("medicines"):
            return "Prescription"
        if payload.get("appointment_date") or payload.get("appointment_time") or payload.get("purpose"):
            return "Appointment"
        if payload.get("report_title") or payload.get("report_summary") or payload.get("findings"):
            return "Other"
        return document.document_type or "Prescription"

    @staticmethod
    def _run_workflow(patient, document, payload):
        orchestrator = AgentOrchestrator()
        return orchestrator.process(
            patient=patient,
            document=document,
            ai_data={
                "document_type": DocumentService._resolve_document_type(document, payload),
                **payload,
            },
        )

    @staticmethod
    def process_document(document):
        start_time = time.time()

        try:
            document.status = "Processing"
            document.save(update_fields=["status", "updated_at"])

            classifier = DocumentClassifierAgent()
            try:
                classification = classifier.classify(document.file.path)
            except Exception:
                classification = {
                    "classification": "printed",
                    "confidence": 0.0,
                    "reason": "Classifier failed",
                }

            payload, extracted_text, confidence = DocumentService._build_llm_payload(
                document.file.path,
                document.document_type,
                classification.get("classification", "printed"),
            )

            document.extracted_text = extracted_text
            resolved_document_type = DocumentService._resolve_document_type(document, payload)
            document.document_type = resolved_document_type
            document.classification = classification["classification"]
            document.classification_confidence = classification["confidence"]
            document.vision_confidence = payload.get("vision_confidence", 0.0)
            document.needs_review = payload.get("needs_review", False)
            document.structured_payload = payload
            document.save(
                update_fields=[
                    "extracted_text",
                    "document_type",
                    "classification",
                    "classification_confidence",
                    "vision_confidence",
                    "needs_review",
                    "structured_payload",
                    "updated_at",
                ]
            )

            workflow_result = None
            if DocumentService._should_auto_process(payload):
                workflow_result = DocumentService._run_workflow(document.patient, document, payload)

            document.status = "Completed"
            document.save(update_fields=["status", "updated_at"])

            processing_time = round(time.time() - start_time, 2)

            return {
                "success": True,
                "document": document,
                "processing_time": processing_time,
                "workflow_result": workflow_result or {},
                "ai_data": payload,
                "classification": classification,
                "confidence": confidence,
                "needs_review": payload.get("needs_review", False),
                "extracted_text": extracted_text,
            }
        except Exception as exc:
            document.status = "Failed"
            document.save(update_fields=["status", "updated_at"])

            return {
                "success": False,
                "error": str(exc),
            }
