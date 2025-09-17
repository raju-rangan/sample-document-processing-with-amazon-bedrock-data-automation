from typing import List
import boto3
from pathlib import Path

client = boto3.client('bedrock-data-automation', region_name='us-east-1')

def create_project(blueprint_arns: List[str]):
    try:
        resp = client.create_data_automation_project(
            projectName="IRLA_V2",
            projectDescription="",
            projectStage="LIVE",
            standardOutputConfiguration={
                    "document": {
                        "extraction": {
                            "granularity": {"types": ["PAGE", "ELEMENT"]},
                            "boundingBox": {"state": "DISABLED"}
                        },
                        "generativeField": {"state": "DISABLED"},
                        "outputFormat": {
                            "textFormat": {"types": ["MARKDOWN"]},
                            "additionalFileFormat": {"state": "DISABLED"}
                        }
                    },
                    "image": {
                        "extraction": {
                            "category": {"state": "ENABLED", "types": ["TEXT_DETECTION"]},
                            "boundingBox": {"state": "ENABLED"}
                        },
                        "generativeField": {"state": "ENABLED", "types": ["IMAGE_SUMMARY"]}
                    },
                    "video": {
                        "extraction": {
                            "category": {"state": "ENABLED", "types": ["TEXT_DETECTION"]},
                            "boundingBox": {"state": "ENABLED"}
                        },
                        "generativeField": {
                            "state": "ENABLED",
                            "types": ["VIDEO_SUMMARY", "CHAPTER_SUMMARY"]
                        }
                    },
                    "audio": {
                        "extraction": {"category": {"state": "ENABLED", "types": ["TRANSCRIPT"]}},
                        "generativeField": {"state": "DISABLED"}
                    }
                },
                overrideConfiguration={
                    "document": {
                        "splitter": {"state": "ENABLED"},
                        "modalityProcessing": {"state": "ENABLED"}
                    },
                    "image": {"modalityProcessing": {"state": "ENABLED"}},
                    "video": {"modalityProcessing": {"state": "ENABLED"}},
                    "audio": {"modalityProcessing": {"state": "ENABLED"}},
                    "modalityRouting": {}
                },
                customOutputConfiguration={
                    'blueprints': [{"blueprintArn": arn, 'blueprintStage': 'LIVE'} for arn in blueprint_arns]
                },
            )
        project_arn = resp["projectArn"]
        print(f"Created project: {project_arn}")
        return project_arn
    except client.exceptions.ConflictException:
        print(f"Project IRLA_V2 exists")
        return None

def create_blueprints(): 

    blueprints_dir = Path("blueprints")

    underwriter_note_SCHEMA = (blueprints_dir / "underwriter_note_schema.json").read_text(encoding="utf-8")
    urla_information_SCHEMA = (blueprints_dir / "urla_information_schema.json").read_text(encoding="utf-8")

    blueprint_schemas = {
        "underwriter-note": underwriter_note_SCHEMA,
        "urla-information": urla_information_SCHEMA,
    }

    arns = []
    for name, schema in blueprint_schemas.items():
        try:
            resp = client.create_blueprint(
                blueprintName=name,
                type="DOCUMENT",
                schema=schema
            )
            arn = resp["blueprint"]["blueprintArn"]
            print(f"Blueprint created: {name} -> {arn}")
            arns.append(arn)
        except client.exceptions.ConflictException:
            print(f"Blueprint {name} exists")
    return arns

def main():
    blueprint_arns = create_blueprints()
    blueprint_arns += [
       'arn:aws:bedrock:us-east-1:aws:blueprint/bedrock-data-automation-public-bank-statement',
       'arn:aws:bedrock:us-east-1:aws:blueprint/bedrock-data-automation-public-payslip',
       'arn:aws:bedrock:us-east-1:aws:blueprint/bedrock-data-automation-public-us-bank-check',
       'arn:aws:bedrock:us-east-1:aws:blueprint/bedrock-data-automation-public-us-driver-license',
       'arn:aws:bedrock:us-east-1:aws:blueprint/bedrock-data-automation-public-w2-form' 
    ]
    project_arn = create_project(blueprint_arns=blueprint_arns)
    print(project_arn)

if __name__ == "__main__":
    main()