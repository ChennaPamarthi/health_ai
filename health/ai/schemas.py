from typing import List

from pydantic import BaseModel, Field


class MedicineSchema(BaseModel):
    medicine_name: str = ""
    dosage: str = ""
    quantity: str = ""
    frequency: List[str] = Field(default_factory=list)
    food_instruction: str = ""
    duration: str = ""
    strength: str = ""
    special_instruction: str = ""


class DocumentExtractionSchema(BaseModel):
    document_type: str = "Other"
    classification: str = "printed"
    confidence: float = 0.0
    ocr_confidence: float = 0.0
    vision_confidence: float = 0.0
    needs_review: bool = False
    doctor_name: str = ""
    hospital_name: str = ""
    diagnosis: str = ""
    prescription_date: str = ""
    review_date: str = ""
    appointment_date: str = ""
    appointment_time: str = ""
    department: str = ""
    purpose: str = ""
    report_title: str = ""
    report_summary: str = ""
    findings: str = ""
    recommendations: str = ""
    report_date: str = ""
    notes: str = ""
    medicines: List[MedicineSchema] = Field(default_factory=list)
