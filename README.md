# FireLead - Smart Lead Generation Tool

FireLead is an advanced lead generation tool that extracts comprehensive business information and contact details from websites. Built with Flask and powered by the FireCrawl API, it provides an intuitive interface for both single-URL and batch extractions.

## 🚀 Features

### 1. Dual Extraction Modes
- Single URL extraction with real-time progress
- Batch processing via CSV/Excel files
- Custom field selection
- Comprehensive error handling

### 2. Data Collection
- Company information (name, size, revenue)
- Contact details (email, phone)
- Digital presence (social media, tech stack)
- Business insights (services, products)

### 3. User Experience
- Real-time progress tracking
- Customizable field selection
- Clean, intuitive interface
- One-click data export

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/firelead.git
cd firelead
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file with your API keys
FIRECRAWL_API_KEY=your_api_key_here
PIPEDRIVE_API_KEY=your_pipedrive_key  # Optional for CRM integration
```

## 🚦 Usage

### Web Interface
1. Start the application:
```bash
python run.py
```

2. Access the interface:
- Open `http://localhost:5000` in your browser
- Choose extraction mode (single URL or file upload)
- Select desired fields
- Start extraction

### API Examples

#### Single URL Extraction
```python
import requests

response = requests.post('http://localhost:5000/extract_firecrawl', json={
    'url': 'https://example.com',
    'selected_fields': {
        'company_name': True,
        'email': True,
        'website_url': True,
        'phone_number': True
    }
})
```

#### Batch Processing
```python
import requests

files = {'file': open('urls.csv', 'rb')}
data = {
    'url_column': 'website_url'
}
response = requests.post('http://localhost:5000/extract_enhanced',
                        files=files,
                        data=data)
```

## 📚 API Documentation

### POST /extract_firecrawl
Extract data from a single URL.
**Parameters:**
- `prompt_user`: String - Extraction instructions
- `selected_fields`: Object - Fields to extract


**Request:**
```json
{
    "prompt": "Extract the AI Startup launch in 2024 in India.",
    "selected_fields": {
        "company_name": true,
        "email": true,
        "phone_number": true,
        "website_url": true,
        "industry": true
    }
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "company_name": "Example Corp",
        "email": "contact@example.com",
        "phone_number": "1234567890",
        "website_url": "https://example.com",
        "industry": "Technology"
    }
}
```

### POST /extract_enhanced

Process multiple URLs from a file.

**Parameters:**
- `file`: CSV/Excel file with URLs
- `url_column`: Column name containing URLs
- `prompt_user`: String - Extraction instructions
- `defined_fields`: Object - Fields to extract

**Request Example:**
```http
POST /api/extract/enhanced
Content-Type: multipart/form-data

# Form Data
file=@urls.csv
url_column=website_url
prompt_user=Extract AI startups founded in India during 2024 with funding details
field_specifications=[
    {
        "field_name": "company_name",
        "field_type": "str"
    },
    {
        "field_name": "founding_date",
        "field_type": "date"
    },
    {
        "field_name": "location",
        "field_type": "str"
    },
    {
        "field_name": "funding_amount",
        "field_type": "float"
    },
    {
        "field_name": "funding_round",
        "field_type": "str"
    },
    {
        "field_name": "investors",
        "field_type": "list"
    }
]
```

**Example urls.csv content:**
```csv
website_url
https://example1.com
https://example2.com
https://example3.com
```

**Success Response:**
```json
{
    "status": "success",
    "message": "Data extraction completed",
    "filename": "extracted_data_2025-04-10.xlsx",
    "summary": {
        "total_urls": 3,
        "successful": 2,
        "failed": 1
    }
}
```

**Error Response:**
```json
{
    "status": "error",
    "message": "Invalid file format. Please upload CSV or Excel file"
}
```

**Notes:**
- Maximum file size: 16MB
- Supported formats: .csv, .xlsx, .xls
- Rate limit: 6 requests/minute
- Maximum URLs per batch: 50

## 📁 Project Structure

```
firelead_project/
├── app/
│   ├── __init__.py
│   ├── main.py           # Main application logic
│   └── utils/
│       └── data_saver.py # Data export utilities
├── static/
│   ├── styles.css        # CSS styles
│   └── script.js         # Frontend JavaScript
├── templates/
│   ├── base.html         # Base template
│   ├── tools.html        # Main interface
│   └── results.html      # Results display
├── .env                  # Environment variables
├── requirements.txt      # Project dependencies
└── run.py               # Application entry point
```

## 📊 Feature Testing & Known Limitations

### 1. Data Extraction

✅ **Working Features:**

- URL-based data extraction
- Multi-URL batch processing (up to 50 URLs)
- Custom field selection
- Progress tracking
- Error handling

⚠️ **Limitations:**

- Rate limits: 6 requests/mintue
- Maximum 50 URLs per batch
- Some fields may be missing depending on website
- JavaScript-heavy websites may have limited data

### 2. User Interface

✅ **Working Features:**

- Responsive design
- Field tooltips
- Progress indicators
- Error messages
- Success notifications

⚠️ **Limitations:**

- Mobile view has limited functionality
- Some tooltips may overlap on small screens
- Large forms require scrolling

## 🔧 Common Issues & Solutions

1. **Missing Data:**
   - Verify all required fields are selected
   - Check website accessibility
   - Validate API keys

2. **Slow Performance:**
   - Limit batch size to 50 URLs
   - Use pagination for large datasets
   - Clear browser cache

## 📈 Performance Metrics

- Average extraction time: 3-4 minutes per URL
- API uptime: 99.9%
- Dashboard load time: < 3 seconds

## 🔒 Security

- API keys stored in environment variables
- Rate limiting implemented
- Input validation on all endpoints
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
