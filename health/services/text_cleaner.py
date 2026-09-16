import re


class TextCleaner:
    @staticmethod
    def clean(text):
        text = str(text or "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def remove_duplicate_lines(text):
        lines = []
        seen = set()
        for line in str(text or "").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(cleaned)
        return "\n".join(lines)

    @staticmethod
    def merge_prescription_lines(text):
        lines = []
        buffer = ""

        for raw_line in str(text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith(("(", "-", "•")):
                buffer = f"{buffer} {line}".strip()
                continue

            if buffer:
                lines.append(buffer.strip())
            buffer = line

        if buffer:
            lines.append(buffer.strip())

        return "\n".join(lines)
