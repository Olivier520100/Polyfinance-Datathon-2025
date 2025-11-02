import pandas as pd
import os
import boto3
from markitdown import MarkItDown
from jsonschema import validate, ValidationError
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings
from botocore.config import Config


warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

class LawReaderAgent:
    schema = {
    "type": "object",
    "properties": {
        "regionOfEffect": {"type": "string"},
        "sectors": {
            "type": "object",
            "patternProperties": {
                "^(Information Technology|Communication Services|Healthcare|Financials|Consumer Discretionary|Industrials|Energy|Materials|Consumer Staples|Utilities|Real Estate)$": {
                    "type": "object",
                    "properties": {
                        "positiveEffects": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "negativeEffects": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "timeline": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["positiveEffects", "negativeEffects", "timeline"]
                }
            },
            "additionalProperties": False
        }
    },
        "required": ["regionOfEffect", "sectors"]
    }

    config = Config(read_timeout=300)

    def __init__(self, directory="directives/", model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"):
        self.directory = directory
        self.model_id = model_id
        self.files = [directory + file for file in os.listdir(self.directory)]
        self.markdown = MarkItDown(enable_plugins=False)
        self.client = boto3.client("bedrock-runtime", config=LawReaderAgent.config)
    
    def complete_summary(self):
        summaries_list = []
        for file in self.files:
            summaries_list.append(self.single_law_summary(file))
        return summaries_list
    
    def single_law_summary(self, file):
        text = self.retrieve_text_content(file)
        chunked_text = self.chunk_text(text)
        response = self.summarize_text_content(chunked_text)
        parsed_response = self.parse_json_from_response(response)
        if self.is_valid_schema(parsed_response):
            return parsed_response
        else:
            print(f"Invalid file format : {file}")

    
    def retrieve_text_content(self, file):
        html = str(self.markdown.convert(file))
        text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        return text
    
    def chunk_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100000,     
            chunk_overlap=1000   
        )
        return text_splitter.split_text(text)
    
    def summarize_text_content(self, text_chunks):
        cumulative_output = ""
        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}")
            response = self.client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": f"""
                                Analyze the following document (chunk {i+1}/{len(text_chunks)}): {chunk}.
                                Output ONLY a JSON in the following format, relating to the effects of the laws passed in regards to specific sectors and countries.

                                These are the 11 sectors we will use:
                                'Information Technology, Communication Services, Healthcare, Financials, Consumer Discretionary, Industrials, Energy, Materials, Consumer Staples, Utilities, Real Estate'

                                {{
                                "regionOfEffect": "region",
                                "sectors": {{
                                    "Information Technology": {{
                                    "positiveEffects": [
                                        // Each element should mention a law/effect that would have a positive outcome (limit 20 words)
                                        // LEAVE EACH LIST EMPTY IF THE REGULATIONS DON'T APPLY TO THE SECTOR,
                                    ],
                                    "negativeEffects": [
                                        // Each element should mention a law/effect that would have a negative outcome (limit 20 words)
                                    ],
                                    "timeline": [
                                        // Up to 10 (ONLY RELEVANT DATES) key dates that tell us when the effects take place (Example : XXXX-XX-XX : Negative effect #3 takes places
                                        // If the effects take place based on a single law, you can have something like     "2021-11-28: Transposition deadline","2022-05-28: Application date"
                                    ]
                                    }},
                                    "Communication Services": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Healthcare": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Financials": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Consumer Discretionary": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Industrials": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Energy": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Materials": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Consumer Staples": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Utilities": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }},
                                    "Real Estate": {{
                                    "positiveEffects": [],
                                    "negativeEffects": [],
                                    "timeline": []
                                    }}
                                }}
                                }}

                                Consider your previous cumulative output: {cumulative_output} (may be empty).
                                You can remove, add, or edit information from the previous output based on redundancy and relevance.
                                """
                                }]
                }
            ],
            inferenceConfig={
                "temperature": 0.5,
            })

            chunk_output = response["output"]["message"]["content"][0]["text"]
            cumulative_output = chunk_output

        return cumulative_output
        
    
    def parse_json_from_response(self, text) -> str:
    
        start = text.find('{')
        end = text.rfind('}')

        if start == -1 or end == -1 or start >= end:
            raise ValueError("No valid JSON object found in text.")

        return text[start:end + 1]
    
    def is_valid_schema(self, output: str):
        try:
            data = json.loads(output)
            validate(instance=data, schema=LawReaderAgent.schema)
            return True
        except json.JSONDecodeError:
            print("Model did not return valid JSON.")
            return False
        except ValidationError as e:
            print("JSON structure invalid:", e.message)
            return False

