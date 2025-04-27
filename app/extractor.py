from firecrawl import FirecrawlApp
from pydantic import BaseModel, create_model
from typing import List, Dict, Any


# 🔧 Function to dynamically build a Pydantic class using exec
def build_model_class(name: str, fields: Dict[str, str]):
    class_code = f"class {name}(BaseModel):\n"
    for field, field_type in fields.items():
        class_code += f"    {field}: {field_type}\n"
    namespace = {}
    exec(class_code, globals(), namespace)
    print("model classes is builded ")
    return namespace[name]


class FirecrawlDataExtractor:
    def __init__(self, api_key: str):
        self.app = FirecrawlApp(api_key=api_key)

    def extract_leads(self, url_patterns: List[str], prompt: str, selected_fields: Dict[str, bool], enable_web_search: bool = True):
        available_fields = {
            "company_name": "str",
            "funding": "str",
            "industry": "str",
            "company_size": "str",
            "revenue_range": "str",
            "headquarters": "str",
            "website_url": "str",
            "founding_year": "str",
            "description": "str",
            "tech_stack": "str",
            "linkedin_company_url": "str",
            "twitter_url": "str",
            "contact_name": "str",
            "email": "str",
            "email_type": "str",
            "phone_number": "str",
            "source_url": "str",
            "page_title": "str",
            "date_scraped": "str",
            "lead_score": "float",
            "recent_news": "str",
            "services_offered": "str",
            "product_list": "str",
            "cta_type": "str",
            "pricing_page_detected": "bool",
            "blog_page_detected": "bool",
        }

        # Create a dynamic model based on selected fields
        fields = {}
        for field, is_selected in selected_fields.items():
            if is_selected and field in available_fields:
                field_type = available_fields[field]
                if field_type == "str":
                    fields[field] = "str"
                elif field_type == "float":
                    fields[field] = "float"
                elif field_type == "bool":
                    fields[field] = "bool"


        # final_fields = {
        #     field: available_fields[field]
        #     for field in selected_fields
        #     if selected_fields[field]
        # }
        print(fields)
        print()
        LeadModel = build_model_class("LeadModel", fields)

        class ExtractSchema(BaseModel):
            leads: List[LeadModel]

        schema = ExtractSchema.model_json_schema()
        print(schema)
        print("going for data ")
        data = self.app.extract(
            url_patterns,
            {'prompt': prompt, 'schema': schema, 'enable_web_search': enable_web_search}
        )
        print("done for data ")
        return data

    def extract_leads_enhanced(self, url_patterns: List[str], prompt: str, specific_fields: Dict[str, str], enable_web_search: bool = True):
        """
        Enhanced version of extract_leads that dynamically creates a schema based on provided fields.
        specific_fields should be a dictionary with field names as keys and field types as values.
        Field types can be: str, bool, number
        """
        # Convert field types to Python types
        type_mapping = {
            "str": "str",
            "bool": "bool",
            "number": "float"  # Using float for number type
        }

        # Create a dynamic model based on specific fields
        fields = {}
        for field, field_type in specific_fields.items():
            # Convert the field type to the appropriate Python type
            python_type = type_mapping.get(field_type.lower(), "str")  # Default to str if type not recognized
            fields[field] = python_type

        print("Building model with fields:", fields)
        LeadModel = build_model_class("LeadModel", fields)

        class ExtractSchema(BaseModel):
            leads: List[LeadModel]

        schema = ExtractSchema.model_json_schema()
        print("Schema:", schema)
        print("Extracting data with prompt:", prompt)

        data = self.app.extract(
            url_patterns,
            {'prompt': prompt, 'schema': schema, 'enable_web_search': enable_web_search}
        )
        print("Data extraction completed")
        return data
