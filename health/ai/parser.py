import json
import re

from .exceptions import AIExtractionError


class JSONParser:

    @staticmethod
    def clean_response(response):

        response = response.strip()

        response = re.sub(
            r"```json",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = response.replace(
            "```",
            ""
        )

        return response.strip()

    @classmethod
    def parse(cls, response):

        response = cls.clean_response(
            response
        )

        try:

            start = response.find("{")

            end = response.rfind("}")

            if start == -1 or end == -1:

                raise AIExtractionError(
                    "JSON not found."
                )

            response = response[
                start:end + 1
            ]

            return json.loads(response)

        except Exception as error:

            raise AIExtractionError(
                str(error)
            )