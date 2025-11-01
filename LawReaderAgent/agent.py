import pandas as pd
import os
import boto3
from markitdown import MarkItDown
from jsonschema import validate, ValidationError
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
    
    def get_laws_info(self):
        laws_info = []
        for file in self.files:
            text = self.get_text_from_file(file)
            chunked_text = self.chunk_text(text)
            response = self.summarize_text_content(chunked_text)
            parsed_response = self.parse_text_response(response)
            if self.is_valid_schema(parsed_response):
                laws_info.append(json.loads(parsed_response))
            else:
                print(f"Error loading file {file}")
        return laws_info
    
    def get_text_from_file(self, file):
        return str(self.markdown.convert(file))
    
    def chunk_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=180000,     
            chunk_overlap=1000   
        )
        return text_splitter.split_text(text)
    
    def summarize_text_content(self, text_chunks):
        cumulative_output = ""
        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}")
            response = self.client.converse(
            modelId="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text" : f"""Analyze the following document (chunk {i+1}/{len(text_chunks)}): {chunk}. 
                                Output ONLY a json with the following format relating to the effects
                                of the laws passed in regards to specific sectors, companies and countries.
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
                                }}
                                Consider your previous cumulative output : {cumulative_output} (may be empty).
                                You can remove, add and edit informations of the previous output based on information
                                redundancy and relevance:
                                """}]
                }
            ],
            inferenceConfig={
                "temperature": 0.5,
            })

            chunk_output = response["output"]["message"]["content"][0]["text"]
            cumulative_output = chunk_output

        return cumulative_output
        
    
    def parse_text_response(self, text) -> str:
    
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

agnet = LawReaderAgent()
print(agnet.get_laws_info())