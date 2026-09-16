class PromptBuilder:
    @staticmethod
    def classification_prompt():
        return """
Classify the document as one of:
- printed
- handwritten

Return JSON only with:
{
  "classification": "printed" or "handwritten",
  "confidence": 0.0 to 1.0,
  "reason": ""
}

If uncertain, choose the most likely class and lower the confidence.
"""

    @staticmethod
    def document_prompt(text, document_type="Other"):
        return f"""
You are an expert medical document extraction assistant.

Read the document image/PDF carefully and extract structured prescription, appointment, or report data.
If supplemental extracted text is provided, use it only as supporting context.

Return ONLY valid JSON.
Do not explain anything.
Do not guess missing information.
If something is unreadable, use "uncertain".
Never return null values. Use empty strings or empty lists instead.

JSON format:
{
    "document_type": "{document_type}",
    "classification": "printed",
    "confidence": 0.0,
    "needs_review": false,
    "doctor_name": "",
    "hospital_name": "",
    "diagnosis": "",
    "prescription_date": "",
    "review_date": "",
    "appointment_date": "",
    "appointment_time": "",
    "department": "",
    "purpose": "",
    "report_title": "",
    "report_summary": "",
    "findings": "",
    "recommendations": "",
    "report_date": "",
    "notes": "",
    "medicines": [
        {
            "medicine_name": "",
            "dosage": "",
            "quantity": "",
            "frequency": [],
            "food_instruction": "",
            "duration": "",
            "strength": "",
            "special_instruction": ""
        }
    ]
}

Rules:
- If the document is a prescription, extract medicines, doctor, hospital, diagnosis, dates, and notes.
- Printed prescriptions may use tables with headings like Medicine Name, Dosage, Duration, Advice Given, and Follow Up. Extract each numbered row as one medicine.
- Put text such as "Before Food" or "After Food" in food_instruction, and convert Morning/Afternoon/Evening/Night mentions into the frequency list.
- If the document is an appointment, extract appointment date, time, doctor, hospital, department, purpose, and notes.
- If the document is a report, extract report title, report date, summary, findings, recommendations, and any notable observations.
- Use empty strings when data is missing.
- Keep date format as YYYY-MM-DD.
- Keep time format as HH:MM.

Supplemental extracted text:

{text}
"""

    @staticmethod
    def handwritten_prompt():
        return """
You are extracting information from a handwritten medical prescription image.

Return JSON only. Do not explain anything.
Do not hallucinate.
If anything is unreadable, use "uncertain".
Never return null values. Use empty strings or empty lists instead.

Extract:
- medicine_name
- dosage
- frequency
- duration
- timing
- instructions
- appointments
- reports
- doctor_name
- hospital

Return structure:
{
  "classification": "handwritten",
  "confidence": 0.0,
  "needs_review": false,
  "doctor_name": "",
  "hospital_name": "",
  "diagnosis": "",
  "prescription_date": "",
  "review_date": "",
  "appointment_date": "",
  "appointment_time": "",
  "department": "",
  "purpose": "",
  "report_title": "",
  "report_summary": "",
  "findings": "",
  "recommendations": "",
  "report_date": "",
  "notes": "",
  "medicines": [
    {
      "medicine_name": "",
      "dosage": "",
      "quantity": "",
      "frequency": [],
      "food_instruction": "",
      "duration": "",
      "strength": "",
      "special_instruction": ""
    }
  ]
}
"""
