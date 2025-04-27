# FireLead API Documentation

## Overview
FireLead provides RESTful APIs for lead generation and data extraction. This document outlines the two main extraction endpoints and their usage.

## Base URL
```
http://localhost:5000
```

## Authentication
All API requests require an API key to be included in the request header:
```http
Authorization: Bearer YOUR_FIRECRAWL_API_KEY
```

## Rate Limits
- 100 requests per hour per API key
- Maximum 50 URLs per batch request
- Average processing time: 3-4 minutes per URL

## Endpoints

### 1. Single URL Extraction
Extract data from a single URL.

```http
POST /extract_firecrawl
```

#### Request Body
```json
{
    "url": "https://example.com",
    "selected_fields": {
        "company_name": true,
        "email": true,
        "phone_number": true,
        "website_url": true,
        "industry": true,
        "employee_count": true,
        "technologies": true,
        "social_links": true
    }
}
```

#### Success Response
```json
{
    "status": "success",
    "data": {
        "company_name": "Example Corp",
        "email": "contact@example.com",
        "phone_number": "+1-123-456-7890",
        "website_url": "https://example.com",
        "industry": "Technology",
        "employee_count": "51-200",
        "technologies": ["Python", "React", "AWS"],
        "social_links": {
            "linkedin": "https://linkedin.com/company/example-corp",
            "twitter": "https://twitter.com/examplecorp"
        }
    }
}
```

#### Error Response
```json
{
    "status": "error",
    "error": {
        "code": "INVALID_URL",
        "message": "The provided URL is invalid or inaccessible"
    }
}
```

### 2. Batch URL Processing
Process multiple URLs from a file.

```http
POST /extract_enhanced
```

#### Request
- Content-Type: multipart/form-data

#### Parameters
| Name | Type | Description |
|------|------|-------------|
| file | File | CSV/Excel file containing URLs |
| url_column | String | Name of the column containing URLs |

#### Example using cURL
```bash
curl -X POST http://localhost:5000/extract_enhanced \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@urls.csv" \
  -F "url_column=website_url"
```

#### Success Response
```json
{
    "status": "success",
    "message": "Data extraction completed",
    "filename": "extracted_data_2025-04-10.xlsx",
    "summary": {
        "total_urls": 10,
        "successful": 8,
        "failed": 2,
        "extracted_data": [
            {
                "company_name": "Example Corp",
                "email": "contact@example.com",
                "phone_number": "+1-123-456-7890",
                "website_url": "https://example.com",
                "industry": "Technology"
            },
            {
                "company_name": "Test Inc",
                "email": "info@test.com",
                "phone_number": "+1-987-654-3210",
                "website_url": "https://test.com",
                "industry": "Software"
            }
        ]
    }
}
```

#### Error Response
```json
{
    "status": "error",
    "error": {
        "code": "INVALID_FILE",
        "message": "The uploaded file is invalid or missing required column"
    }
}
```

## SDK Examples

### Python SDK

#### 1. Single URL Extraction
```python
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# Initialize the app
app = FirecrawlApp(API_KEY)

# Define data model
class CompanyData(BaseModel):
    company_name: str
    email: Optional[str]
    phone_number: Optional[str]
    website_url: str
    industry: Optional[str]
    employee_count: Optional[str]
    technologies: Optional[List[str]]
    social_links: Optional[Dict[str, str]]

# Extract data
result = app.extract(
    ["https://example.com"],
    {
        'schema': CompanyData.model_json_schema(),
        'enable_web_search': True
    }
)

print(result.data)
```

#### 2. Batch Processing
```python
import pandas as pd

# Read URLs from CSV
urls_df = pd.read_csv('urls.csv')
urls = urls_df['website_url'].tolist()

# Define batch extraction
class BatchExtractSchema(BaseModel):
    companies: List[CompanyData]

# Extract data in batches
results = app.extract(
    urls,
    {
        'schema': BatchExtractSchema.model_json_schema(),
        'enable_web_search': True,
        'batch_size': 50
    }
)

# Convert to DataFrame
extracted_df = pd.DataFrame([
    company.dict() 
    for company in results.data.companies
])

# Save to Excel
extracted_df.to_excel('extracted_data.xlsx', index=False)
```

### JavaScript SDK

#### 1. Single URL Extraction
```javascript
const { FirecrawlApp } = require('firecrawl');

// Initialize the app
const app = new FirecrawlApp(API_KEY);

// Extract data
async function extractCompanyData(url) {
    try {
        const result = await app.extract([url], {
            schema: {
                type: 'object',
                properties: {
                    company_name: { type: 'string' },
                    email: { type: 'string' },
                    phone_number: { type: 'string' },
                    website_url: { type: 'string' },
                    industry: { type: 'string' },
                    technologies: { type: 'array', items: { type: 'string' } }
                },
                required: ['company_name', 'website_url']
            },
            enable_web_search: true
        });
        
        console.log(result.data);
    } catch (error) {
        console.error('Extraction failed:', error);
    }
}
```

#### 2. Batch Processing
```javascript
// Batch processing
async function batchExtractCompanies(urls) {
    try {
        const result = await app.extract(urls, {
            schema: {
                type: 'object',
                properties: {
                    companies: {
                        type: 'array',
                        items: {
                            type: 'object',
                            properties: {
                                company_name: { type: 'string' },
                                email: { type: 'string' },
                                phone_number: { type: 'string' },
                                website_url: { type: 'string' },
                                industry: { type: 'string' }
                            }
                        }
                    }
                }
            },
            enable_web_search: true,
            batch_size: 50
        });

        return result.data.companies;
    } catch (error) {
        console.error('Batch extraction failed:', error);
        return [];
    }
}

// Usage
const urls = ['https://example.com', 'https://test.com'];
batchExtractCompanies(urls).then(companies => {
    console.log('Extracted companies:', companies);
});
```

## Error Handling

### Common Error Codes
| Code | Description |
|------|-------------|
| INVALID_URL | The provided URL is invalid or inaccessible |
| RATE_LIMIT_EXCEEDED | API rate limit has been exceeded |
| INVALID_FILE | The uploaded file is invalid or corrupted |
| MISSING_FIELDS | Required fields are missing in the request |
| API_ERROR | General API error |

## Best Practices

1. **Rate Limiting**
   - Implement exponential backoff for failed requests
   - Keep track of remaining API calls
   - Use batch processing for multiple URLs

2. **Data Quality**
   - Always validate extracted data
   - Handle missing fields gracefully
   - Implement retry logic for failed extractions

3. **Performance**
   - Use appropriate batch sizes (max 50)
   - Account for 3-4 minute processing time per URL
   - Implement proper error handling and timeouts
