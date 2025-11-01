import pandas as pd
import os
import boto3
from markitdown import MarkItDown
from jsonschema import validate, ValidationError
import json

class LawReaderAgent:

    schema = {
    "type": "object",
    "properties": {
        "countryOfEffect": {"type": "string"},
        "positivelyAffected": {
            "type": "object",
            "properties": {
                "specificCompanies": {"type": "array", "items": {"type": "string"}},
                "specificSectors": {"type": "array", "items": {"type": "string"}},
                "lawsPassed": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["specificCompanies", "specificSectors", "lawsPassed"]
        },
        "negativelyAffected": {
            "type": "object",
            "properties": {
                "specificCompanies": {"type": "array", "items": {"type": "string"}},
                "specificSectors": {"type": "array", "items": {"type": "string"}},
                "lawsPassed": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["specificCompanies", "specificSectors", "lawsPassed"]
        },
        "timelineOfChanges": {"type": "object"}
    },
    "required": ["countryOfEffect", "timelineOfChanges"]
    }

    def __init__(self, directory="directives/", model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"):
        self.directory = directory
        self.model_id = model_id
        self.files = [directory + file for file in os.listdir(self.directory)]
        self.markdown = MarkItDown(enable_plugins=False)
        self.client = boto3.client("bedrock-runtime")
    
    def get_text_from_file(self, file):
        return self.markdown.convert(file)
    
    def summarize_text_content(self, text):
        response = self.client.converse(
        modelId="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text" : f"""Analyze the following document: {text}. 
                            Output ONLY a json with the following format relating to the effects
                            of the laws passed in regards to specific :
                            {{"countryOfEffect" : "country",
                            "positivelyAffected": {{ // LEAVE EMPTY IF ONLY NEGATIVE EFFECTS
                                "specificCompanies" : ["list", "of", "affectedCompanies"], // LEAVE EMPTY IF NO COMPANIES ARE MENTIONNED
                                "specificSectors" : ["list, "of", "sectors],
                                "lawsPassed": ["list", "of the laws that cause the positive effects] // LIMIT TO 15 WORDS
                            }},
                            "negativelyAffected": {{ // LEAVE EMPTY IF ONLY POSITIVE EFFECTS
                                "specificCompanies": ["list", "of", "affectedCompanies"], // LEAVE EMPTY IF NO COMPANIES ARE MENTIONNED
                                "specificSectors": ["list, "of", "sectors],
                                "lawsPassed": ["list", "of the laws that cause the negative effects] // LIMIT TO 15 WORDS
                            }},
                            "timelineOfChanges" : {{ // LIMIT TO THE 5 MOST IMPORTANT DATES
                            "date#1" : "effect in question"
                            "date#2" : "",
                            "etc..." :""
                            }}
                            }}"""}]
            }
        ],
        inferenceConfig={
            "temperature": 0.5,
        })
        return response["output"]["message"]["content"][0]["text"]
        
    
    def parse_text_response(self, text) -> str:
    
        start = text.find('{')
        end = text.rfind('}')

        if start == -1 or end == -1 or start >= end:
            raise ValueError("No valid JSON object found in text.")

        return text[start:end + 1]
    
    def verify_output_schema(self, output: str):
        try:
            data = json.loads(output)
            validate(instance=data, schema=LawReaderAgent.schema)
            print("Model output is valid JSON and fits schema.")
        except json.JSONDecodeError:
            print("Model did not return valid JSON.")
        except ValidationError as e:
            print("JSON structure invalid:", e.message)

# agent = LawReaderAgent()
# text = agent.get_text_from_file(agent.files[0])
# response = agent.summarize_text_content(text)
# print(response)
# parsed_response = agent.parse_text_response(response)
# isvalid = print(agent.verify_output_schema(parsed_response))
