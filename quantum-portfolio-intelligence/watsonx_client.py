"""
watsonx_client.py

IBM watsonx.ai client wrapper.

Version : 2.6.0

The AI integration is OPTIONAL.

If IBM watsonx credentials are not configured,
the application will continue to work normally.
"""

from __future__ import annotations

from config import (
    WATSONX_API_KEY,
    WATSONX_URL,
    WATSONX_PROJECT_ID,
    WATSONX_MODEL,
    WATSONX_MAX_NEW_TOKENS,
    WATSONX_TEMPERATURE,
    WATSONX_TOP_P,
    WATSONX_REPETITION_PENALTY,
)


class WatsonXClient:

    def __init__(self):

        self.enabled = False
        self.model = None

        #
        # AI disabled
        #

        if (
            not WATSONX_API_KEY
            or not WATSONX_PROJECT_ID
        ):

            print()

            print(
                "[AI] IBM watsonx credentials not configured."
            )

            print(
                "[AI] AI report generation skipped."
            )

            print(
                "[AI] Update config.py later to enable AI."
            )

            print()

            return

        #
        # Import SDK only if needed
        #

        try:

            from ibm_watsonx_ai import Credentials

            from ibm_watsonx_ai.foundation_models import (
                ModelInference
            )

        except ImportError:

            print()

            print(
                "[AI] ibm-watsonx-ai SDK not installed."
            )

            print(
                "[AI] Run:"
            )

            print(
                "pip install ibm-watsonx-ai"
            )

            print()

            return

        try:

            credentials = Credentials(

                url=WATSONX_URL,

                api_key=WATSONX_API_KEY

            )

            self.model = ModelInference(

                model_id=WATSONX_MODEL,

                credentials=credentials,

                project_id=WATSONX_PROJECT_ID,

                params={

                    "max_new_tokens":
                        WATSONX_MAX_NEW_TOKENS,

                    "temperature":
                        WATSONX_TEMPERATURE,

                    "top_p":
                        WATSONX_TOP_P,

                    "repetition_penalty":
                        WATSONX_REPETITION_PENALTY,

                }

            )

            self.enabled = True

            print("[AI] IBM watsonx initialized.")

        except Exception as ex:

            print()

            print(
                "[AI] Unable to initialize IBM watsonx."
            )

            print(ex)

            print()

            self.enabled = False

    # -----------------------------------------------------

    def is_enabled(self):

        return self.enabled

    # -----------------------------------------------------

    def generate(self, prompt: str):

        if not self.enabled:

            return None

        try:

            response = self.model.generate_text(

                prompt=prompt

            )

            return response.strip()

        except Exception as ex:

            print()

            print(
                "[AI] Error generating response."
            )

            print(ex)

            print()

            return None
