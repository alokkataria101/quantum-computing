"""
ai_report.py

Generates AI-assisted investment reports using IBM watsonx.

Version : 2.6.0
"""

from __future__ import annotations

import json
from pathlib import Path

from prompt_builder import PromptBuilder
from watsonx_client import WatsonXClient

from config import (
    OUTPUT_REPORT_DIR,
    PORTFOLIO_JSON,
    AI_PROMPT_FILE,
    AI_REPORT_MARKDOWN,
    AI_REPORT_JSON,
)


class AIReport:

    def __init__(self):

        self.client = WatsonXClient()

    # ---------------------------------------------------------

    def generate(self):

        portfolio_file = (
            OUTPUT_REPORT_DIR /
            PORTFOLIO_JSON
        )

        if not portfolio_file.exists():

            print()

            print(
                "[AI] Portfolio JSON not found."
            )

            print(
                "[AI] Run portfolio analysis first."
            )

            print()

            return False

        #
        # Load Portfolio JSON
        #

        with open(

            portfolio_file,

            "r",

            encoding="utf-8"

        ) as fp:

            portfolio = json.load(fp)

        #
        # Build Prompt
        #

        builder = PromptBuilder(

            portfolio

        )

        prompt = builder.build()

        #
        # Save Prompt
        #

        prompt_file = (

            OUTPUT_REPORT_DIR /

            AI_PROMPT_FILE

        )

        builder.save(

            prompt_file

        )

        print()

        print(

            f"Prompt saved : {prompt_file}"

        )

        #
        # AI Disabled
        #

        if not self.client.is_enabled():

            print()

            print(

                "[AI] AI report skipped."

            )

            print()

            return False

        #
        # Generate Report
        #

        response = self.client.generate(

            prompt

        )

        if response is None:

            return False

        #
        # Save Markdown
        #

        markdown_file = (

            OUTPUT_REPORT_DIR /

            AI_REPORT_MARKDOWN

        )

        with open(

            markdown_file,

            "w",

            encoding="utf-8"

        ) as fp:

            fp.write("# AI Portfolio Report\n\n")

            fp.write(response)

        #
        # Save JSON
        #

        json_file = (

            OUTPUT_REPORT_DIR /

            AI_REPORT_JSON

        )

        with open(

            json_file,

            "w",

            encoding="utf-8"

        ) as fp:

            json.dump(

                {

                    "provider":
                        "IBM watsonx",

                    "model":
                        "Granite",

                    "report":
                        response

                },

                fp,

                indent=4

            )

        print()

        print(

            f"AI Markdown Report : {markdown_file}"

        )

        print(

            f"AI JSON Report : {json_file}"

        )

        print()

        return True
