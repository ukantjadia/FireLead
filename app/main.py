from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect, Response
from werkzeug.utils import secure_filename
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from .extractor import FirecrawlDataExtractor
from .data_saver import DataSaver
import json
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta
import requests
from collections import defaultdict

# Load environment variables
load_dotenv()

# Get API key from environment variable
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

# Get the current directory
current_dir = Path(__file__).parent
project_root = current_dir.parent

app = Flask(__name__,
           template_folder=str(project_root / 'templates'),
           static_folder=str(project_root / 'static'))

# Configure upload folder and data folder
app.config['UPLOAD_FOLDER'] = str(project_root / 'uploads')
app.config['DATA_FOLDER'] = str(project_root / 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# Initialize data saver
data_saver = DataSaver(app.config['DATA_FOLDER'])

# Progress queue for each session
progress_queues = {}

def send_progress_update(message):
    return f"data: {json.dumps({'message': message})}\n\n"

def update_progress(message):
    """Update progress for the current request context"""
    app.current_progress = message
    # Small delay to ensure frontend receives the update
    time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tools')
def tools():
    return render_template('tools.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/results')
def results():
    # Get the latest saved file
    try:
        saved_files = list(Path(app.config['DATA_FOLDER']).glob('*.xlsx'))
        if not saved_files:
            return render_template('results.html',
                                error="No data available. Please perform an extraction first.")

        # Get the most recent file
        latest_file = max(saved_files, key=lambda x: x.stat().st_mtime)

        # Read the Excel file
        df = pd.read_excel(latest_file)

        # Get sample data (first 5 rows as dictionaries)
        sample_data = df.head().to_dict('records')

        return render_template('results.html',
                             sample_data=sample_data,
                             filename=latest_file.name,
                             total_records=len(df))
    except Exception as e:
        return render_template('results.html',
                             error=f"Error loading results: {str(e)}")

@app.route('/api/progress')
def progress_stream():
    def generate():
        while True:
            if hasattr(app, 'current_progress') and app.current_progress is not None:
                yield send_progress_update(app.current_progress)
                app.current_progress = None
            time.sleep(0.1)  # Reduced wait time for more responsive updates

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/extract/firecrawl', methods=['POST'])
def extract_firecrawl():
    data = request.json
    prompt_user = data.get('prompt_user')
    selected_fields = data.get('selected_fields', {})
    print(selected_fields)
    try:
        # Initialize extractor
        extractor = FirecrawlDataExtractor(api_key=FIRECRAWL_API_KEY)

        # Validate inputs
        if not prompt_user:
            raise ValueError("Prompt is required")
        if not any(selected_fields.values()):
            raise ValueError("At least one field must be selected")

        # Log prompt received
        update_progress(f"Processing prompt: {prompt_user[:50]}...")

        # Generate updated prompt with fields
        selected_field_names = [field for field, selected in selected_fields.items() if selected]
        updated_prompt = f"{prompt_user} Extract the following fields: {', '.join(selected_field_names)}"
        update_progress(f"Generated optimized prompt with specified fields: {updated_prompt}")
        print(selected_field_names)
        # Define default URLs to extract from
        url_patterns = [
            "https://firecrawl.dev/*", "https://tracxn.com/*",
            "https://www.cbinsights.com/*", "https://pitchbook.com/*",
            "https://www.privco.com/*", "https://www.crunchbase.com/*",
            "https://www.owler.com/*", "https://www.zoominfo.com/*"
        ]

        update_progress("Connecting to Firecrawl API...")
        time.sleep(0.5)  # Small delay to show the connection step

        # Extract data
        update_progress("Sending request to Firecrawl API...")
        results = extractor.extract_leads(url_patterns, updated_prompt, selected_fields, enable_web_search=True)

        if not results:
            raise ValueError("No response received from Firecrawl API")

        update_progress("Processing API response...")

        if results and 'data' in results and 'leads' in results['data']:
            lead_count = len(results['data']['leads'])
            update_progress(f"Found {lead_count} leads in the response")

            # Convert to DataFrame and save
            update_progress("Converting data to structured format...")
            df = pd.DataFrame(results['data']['leads'])

            update_progress("Saving extracted data...")
            saved_file = data_saver.save(df)

            update_progress(f"Data saved successfully as '{saved_file.name}'")

            return jsonify({
                'status': 'success',
                'message': 'Data extraction completed',
                'redirect': url_for('results')
            })
        else:
            raise ValueError("No leads found in the extraction results")

    except Exception as e:
        error_msg = str(e)
        update_progress(f"Error: {error_msg}")
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

@app.route('/api/extract/enhanced', methods=['POST'])
def extract_enhanced():
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file uploaded'
        }), 400

    file = request.files['file']
    url_column = request.form.get('url_column')
    prompt_user = request.form.get('prompt_user')
    field_specs = request.form.get('field_specifications')

    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No file selected'
        }), 400

    if not url_column:
        return jsonify({
            'status': 'error',
            'message': 'URL column name is required'
        }), 400

    if not prompt_user:
        return jsonify({
            'status': 'error',
            'message': 'Prompt is required'
        }), 400

    try:
        # Initialize extractor
        extractor = FirecrawlDataExtractor(api_key=FIRECRAWL_API_KEY)

        # Save and process file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        update_progress(f"Receiving file: {filename}")
        file.save(filepath)

        # Read the uploaded file
        update_progress("Loading and validating file contents...")
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

        if url_column not in df.columns:
            raise ValueError(f"Column '{url_column}' not found in the file")

        # Parse field specifications
        specific_fields = {"company_url": "str"}  # Default field
        if field_specs:
            try:
                field_specs_list = json.loads(field_specs)
                specific_fields = {
                    spec["field_name"]: spec["field_type"]
                    for spec in field_specs_list
                }
            except json.JSONDecodeError:
                raise ValueError("Invalid field specifications format")

        # Get unique URLs
        unique_urls = df[url_column].dropna().unique()
        total_urls = len(unique_urls)
        update_progress(f"Found {total_urls} unique URLs to process")

        # Create prompt with field specifications
        current_prompt = f"{prompt_user} Extract the following fields: {', '.join(specific_fields.keys())}"
        update_progress(f"Generated optimized prompt with specified fields: {current_prompt}")

        # Process each URL
        all_extracted_data = []
        for idx, url in enumerate(unique_urls, 1):
            try:
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                formatted_url = base_url + "*"


                # time.sleep(5)
                update_progress(f"Processing URL {idx}/{total_urls}: {base_url}")
                # Extract data for current URL
                extracted_data = extractor.extract_leads_enhanced(
                    [formatted_url],
                    current_prompt,
                    specific_fields,
                    enable_web_search=False
                )

                if extracted_data and 'data' in extracted_data and 'leads' in extracted_data['data']:
                    all_extracted_data.extend(extracted_data['data']['leads'])
                    update_progress(f"Successfully extracted data from {base_url}")
                else:
                    update_progress(f"No data found for {base_url}")

                time.sleep(2)  # Rate limiting
            except Exception as e:
                update_progress(f"Error processing {url}: {str(e)}")
                continue

        if not all_extracted_data:
            raise ValueError("No data could be extracted from any of the URLs")

        # Save results
        update_progress("Processing extracted data...")
        df_results = pd.DataFrame(all_extracted_data)
        saved_file = data_saver.save(df_results)

        update_progress(f"Data saved successfully as '{saved_file.name}'")

        return jsonify({
            'status': 'success',
            'message': 'Data extraction completed',
            'redirect': url_for('results')
        })

    except Exception as e:
        error_msg = str(e)
        update_progress(f"Error: {error_msg}")
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

@app.route('/download_results')
def download_results():
    try:
        # Get the latest saved file
        saved_files = list(Path(app.config['DATA_FOLDER']).glob('*.xlsx'))
        if not saved_files:
            return "No data available for download", 404

        latest_file = max(saved_files, key=lambda x: x.stat().st_mtime)

        return send_file(
            latest_file,
            as_attachment=True,
            download_name=latest_file.name
        )
    except Exception as e:
        return str(e), 500

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    # Load saved leads data
    leads_df = pd.read_csv('leads_data.csv')

    # Calculate metrics
    total_leads = len(leads_df)
    avg_score = leads_df['lead_score'].mean() if 'lead_score' in leads_df else 0

    # Calculate trend (comparing to previous period)
    today = datetime.now()
    last_week = today - timedelta(days=7)

    recent_leads = leads_df[leads_df['date_scraped'] > last_week.strftime('%Y-%m-%d')]
    previous_leads = leads_df[leads_df['date_scraped'] <= last_week.strftime('%Y-%m-%d')]

    trend = ((len(recent_leads) - len(previous_leads)) / len(previous_leads) * 100) if len(previous_leads) > 0 else 0

    # Get recent leads for table
    recent_leads_list = leads_df.tail(10).to_dict('records')

    return jsonify({
        'totalLeads': total_leads,
        'averageScore': round(avg_score, 1),
        'trend': round(trend, 1),
        'recentLeads': recent_leads_list
    })

@app.route('/api/export/<format>', methods=['POST'])
def export_to_crm(format):
    try:
        # Load the leads data
        leads_df = pd.read_csv('leads_data.csv')

        if format == 'csv':
            # Direct CSV download
            return send_file(
                'leads_data.csv',
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'leads_export_{datetime.now().strftime("%Y%m%d")}.csv'
            )

        # Handle CRM-specific exports
        if format == 'hubspot':
            return export_to_hubspot(leads_df)
        elif format == 'salesforce':
            return export_to_salesforce(leads_df)
        elif format == 'pipedrive':
            return export_to_pipedrive(leads_df)

        return jsonify({'status': 'error', 'message': 'Invalid export format'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def export_to_hubspot(leads_df):
    # Configure HubSpot API
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
    if not HUBSPOT_API_KEY:
        return jsonify({'status': 'error', 'message': 'HubSpot API key not configured'})

    success_count = 0
    for _, lead in leads_df.iterrows():
        try:
            # Map lead data to HubSpot format
            contact_data = {
                "properties": {
                    "company": lead['company_name'],
                    "email": lead['email'],
                    "phone": lead['phone_number'],
                    "website": lead['website_url'],
                    "industry": lead['industry'],
                    "description": lead['description']
                }
            }

            # Send to HubSpot API
            response = requests.post(
                'https://api.hubapi.com/crm/v3/objects/contacts',
                headers={
                    'Authorization': f'Bearer {HUBSPOT_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=contact_data
            )

            if response.status_code == 201:
                success_count += 1

        except Exception as e:
            continue

    return jsonify({
        'status': 'success',
        'message': f'Successfully exported {success_count} leads to HubSpot'
    })

def export_to_salesforce(leads_df):
    # Configure Salesforce API
    SF_ACCESS_TOKEN = os.getenv('SF_ACCESS_TOKEN')
    SF_INSTANCE_URL = os.getenv('SF_INSTANCE_URL')

    if not (SF_ACCESS_TOKEN and SF_INSTANCE_URL):
        return jsonify({'status': 'error', 'message': 'Salesforce credentials not configured'})

    success_count = 0
    for _, lead in leads_df.iterrows():
        try:
            # Map lead data to Salesforce format
            lead_data = {
                "Company": lead['company_name'],
                "Email": lead['email'],
                "Phone": lead['phone_number'],
                "Website": lead['website_url'],
                "Industry": lead['industry'],
                "Description": lead['description']
            }

            # Send to Salesforce API
            response = requests.post(
                f'{SF_INSTANCE_URL}/services/data/v52.0/sobjects/Lead',
                headers={
                    'Authorization': f'Bearer {SF_ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                json=lead_data
            )

            if response.status_code == 201:
                success_count += 1

        except Exception as e:
            continue

    return jsonify({
        'status': 'success',
        'message': f'Successfully exported {success_count} leads to Salesforce'
    })

def export_to_pipedrive(leads_df):
    # Configure Pipedrive API
    PIPEDRIVE_API_KEY = os.getenv('PIPEDRIVE_API_KEY')
    if not PIPEDRIVE_API_KEY:
        return jsonify({'status': 'error', 'message': 'Pipedrive API key not configured'})

    success_count = 0
    for _, lead in leads_df.iterrows():
        try:
            # Map lead data to Pipedrive format
            deal_data = {
                "title": lead['company_name'],
                "person_id": create_pipedrive_person(lead),
                "org_id": create_pipedrive_organization(lead),
                "status": "open"
            }

            # Send to Pipedrive API
            response = requests.post(
                'https://api.pipedrive.com/v1/deals',
                params={'api_token': PIPEDRIVE_API_KEY},
                json=deal_data
            )

            if response.status_code == 201:
                success_count += 1

        except Exception as e:
            continue

    return jsonify({
        'status': 'success',
        'message': f'Successfully exported {success_count} leads to Pipedrive'
    })

def create_pipedrive_person(lead):
    # Create person in Pipedrive
    person_data = {
        "name": lead['company_name'],
        "email": lead['email'],
        "phone": lead['phone_number']
    }

    response = requests.post(
        'https://api.pipedrive.com/v1/persons',
        params={'api_token': PIPEDRIVE_API_KEY},
        json=person_data
    )

    if response.status_code == 201:
        return response.json()['data']['id']
    else:
        return None

def create_pipedrive_organization(lead):
    # Create organization in Pipedrive
    org_data = {
        "name": lead['company_name'],
        "address": lead['address']
    }

    response = requests.post(
        'https://api.pipedrive.com/v1/organizations',
        params={'api_token': PIPEDRIVE_API_KEY},
        json=org_data
    )

    if response.status_code == 201:
        return response.json()['data']['id']
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True)
