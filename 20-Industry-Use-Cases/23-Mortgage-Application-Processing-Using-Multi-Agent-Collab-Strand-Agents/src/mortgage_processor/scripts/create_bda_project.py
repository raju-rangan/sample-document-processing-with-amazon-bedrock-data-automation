from typing import List
import boto3

# Initialize the correct Boto3 client
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
        print(f"✅ Created project: {project_arn}")
        return project_arn
    except client.exceptions.ConflictException:
        print(f"Project IRLA_V2 exists")
        return None

def create_blueprints(): 
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

underwriter_note_SCHEMA = "{\"$schema\":\"http://json-schema.org/draft-07/schema#\",\"description\":\"Blueprint for extracting key information from mortgage underwriter's notes\",\"class\":\"Mortgage Underwriter Notes\",\"type\":\"object\",\"definitions\":{\"evaluation\":{\"type\":\"object\",\"properties\":{\"value\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Numerical value associated with the metric\"},\"assessment\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Underwriter's qualitative assessment (e.g., strong, high, robust)\"},\"impact\":{\"enum\":[\"POSITIVE\",\"NEGATIVE\",\"NEUTRAL\"],\"instruction\":\"Impact on application (POSITIVE: strengthens application, NEGATIVE: weakens application, NEUTRAL: no significant impact)\",\"inferenceType\":\"explicit\"},\"notes\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Additional notes or context about this metric\"}}}},\"properties\":{\"ltv_ratio\":{\"$ref\":\"#/definitions/evaluation\",\"instruction\":\"Loan-to-Value ratio assessment including percentage and qualitative evaluation\"},\"dti_ratio\":{\"$ref\":\"#/definitions/evaluation\",\"instruction\":\"Debt-to-Income ratio assessment including percentage and qualitative evaluation\"},\"liquid_assets\":{\"$ref\":\"#/definitions/evaluation\",\"instruction\":\"Assessment of applicant's liquid assets including dollar amount and qualitative evaluation\"},\"payment_shock_present\":{\"type\":\"boolean\",\"inferenceType\":\"explicit\",\"instruction\":\"Indicates if there is payment shock when comparing current rent to projected mortgage payment\"},\"payment_shock_notes\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Details about payment shock assessment or comparison between current housing costs and projected mortgage\"},\"credit_history_clean\":{\"type\":\"boolean\",\"inferenceType\":\"explicit\",\"instruction\":\"Indicates if the credit history is clean with no derogatory events\"},\"credit_history_notes\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Additional notes about credit history quality and impact on application\"},\"asset_diversity\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Assessment of the applicant's asset diversity and what it indicates about financial responsibility\"},\"employment_industry\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Industry where the applicant works (e.g., tech, healthcare, education)\"},\"employment_years\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Number of years the applicant has been employed in their current industry\"},\"income_stability_notes\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Assessment of income stability and its impact on creditworthiness\"},\"primary_concerns\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Primary issues or concerns identified by the underwriter\"},\"required_actions\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Actions or strategies required to address concerns or strengthen the application\"}}}"
urla_information_SCHEMA = "{\"$schema\":\"http://json-schema.org/draft-07/schema#\",\"description\":\"Comprehensive extraction of mortgage loan application including personal details, employment, financial status, and property information for loan underwriting and approval.\",\"class\":\"Complete Mortgage Loan Application\",\"type\":\"object\",\"definitions\":{\"contact_information_details\":{\"type\":\"object\",\"properties\":{\"home_phone\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Home phone number from Contact Information section on page 1\"},\"cell_phone\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Cell phone number from Contact Information section on page 1\"},\"work_phone\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Work phone number from Contact Information section on page 1\"},\"email_address\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Email address from Contact Information section on page 1\"}}}},\"properties\":{\"applicant_name\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Full name of applicant (first, middle, last, and suffix) from Personal Information section on page 1\"},\"ssn\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"9-digit Social Security Number from Personal Information section on page 1\"},\"alternate_names\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Any other names the applicant is known by from Personal Information section on page 1\"},\"date_of_birth\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Date of birth in mm/dd/yyyy format from Personal Information section on page 1\"},\"citizenship_status\":{\"enum\":[\"USC\",\"PRA\",\"NPRA\"],\"instruction\":\"Citizenship status (USC: U.S. Citizen, PRA: Permanent Resident Alien, NPRA: Non-Permanent Resident Alien) from Personal Information section on page 1\",\"inferenceType\":\"explicit\"},\"credit_application\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Type of credit (Individual or Joint) and total number of borrowers if joint application from Personal Information section on page 1\"},\"marital_status\":{\"enum\":[\"M\",\"S\",\"U\"],\"instruction\":\"Marital status (M: Married, S: Separated, U: Unmarried) from Personal Information section on page 1\",\"inferenceType\":\"explicit\"},\"dependents\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Number and ages of dependents (e.g., '2 dependents: ages 4, 7') from Personal Information section on page 1\"},\"contact_information\":{\"$ref\":\"#/definitions/contact_information_details\",\"instruction\":\"Contact information including home phone, cell phone, work phone and email address from Contact Information section on page 1\"},\"current_address\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Complete current address including street, unit, city, state, zip and country from Current Address section on page 1\"},\"current_address_duration\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Time at current address (years and months) from Current Address section on page 1\"},\"housing\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Housing status (Own, Rent, or No primary housing expense) and monthly payment amount from Housing section on page 1\"},\"employment_status\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"If employment section applies and whether applicant is business owner/self-employed from Current Employment section on page 2\"},\"employer_name\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Name of employer or business from Current Employment section on page 2\"},\"employer_phone\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Phone number of the employer from Current Employment section on page 2\"},\"employer_address\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Complete employer address including street, unit, city, state, zip and country from Current Employment section on page 2\"},\"employment_details\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Position title, start date, and duration in this line of work from Current Employment section on page 2\"},\"income_base\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Base monthly income in dollars from Monthly Income section on page 2\"},\"income_overtime\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Overtime monthly income in dollars from Monthly Income section on page 2\"},\"income_bonus\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Bonus monthly income in dollars from Monthly Income section on page 2\"},\"income_commission\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Commission monthly income in dollars from Monthly Income section on page 2\"},\"income_military\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Military entitlements monthly income in dollars from Monthly Income section on page 2\"},\"income_other\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Other monthly income in dollars from Monthly Income section on page 2\"},\"income_total\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Total gross monthly income in dollars from Monthly Income section on page 2\"},\"total_assets_value\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Total value of all assets from Financial Information section on page 3\"},\"total_liabilities_amount\":{\"type\":\"number\",\"inferenceType\":\"explicit\",\"instruction\":\"Total amount of all liabilities from Financial Information section on page 3\"},\"loan_details\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Loan amount and purpose (Purchase, Refinance, or Other with description) from Loan and Property Information section on page 4\"},\"property_address\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Complete property address including street, unit, city, state, zip and county from Loan and Property Information section on page 4\"},\"property_characteristics\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Number of units and estimated property value in dollars from Loan and Property Information section on page 4\"},\"property_occupancy\":{\"enum\":[\"PRIMARY_RESIDENCE\",\"SECOND_HOME\",\"INVESTMENT_PROPERTY\",\"FHA_SECONDARY_RESIDENCE\"],\"instruction\":\"How the property will be occupied from Loan and Property Information section on page 4\",\"inferenceType\":\"explicit\"},\"property_usage\":{\"type\":\"string\",\"inferenceType\":\"explicit\",\"instruction\":\"Whether property is mixed-use and/or a manufactured home from Loan and Property Information section on page 4\"}}}"

if __name__ == "__main__":
    main()