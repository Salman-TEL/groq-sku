import csv
import os
import urllib.parse as urlparse
import requests
from google.oauth2 import service_account
from flask import Flask, jsonify, redirect, request, url_for, session, render_template
import gspread

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use an environment variable for secret key

# Constants for Google OAuth
CLIENT_ID = os.environ.get('CLIENT_ID')  # Your CLIENT_ID
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')  # Your CLIENT_SECRET
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://127.0.0.1:8000/callback')

# Define the scope for Google Sheets API and Drive API
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load the service account credentials
SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SHEET_CREDENTIALS')
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("TEL-sku").sheet1  # Open your Google Sheet

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login/google')
def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{google_auth_url}?{urlparse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Missing Authorization Code", 400

    # Exchange authorization code for access token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=data)
    token_info = response.json()
    access_token = token_info.get('access_token')

    if not access_token:
        return "Error retrieving access token", 400

    # Fetch user info
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)

    if user_info_response.status_code != 200:
        return "Error retrieving user information", 400

    user_info = user_info_response.json()

    # Handle user info (e.g., save to Google Sheet)
    handle_user_info(user_info)

    # Redirect to the index page after successful login
    return redirect(url_for('index'))

def handle_user_info(user_info):
    # Extract relevant user data
    name = user_info.get('name')
    email = user_info.get('email')
    picture = user_info.get('picture')

    # Append user info to Google Sheet
    if name and email:
        sheet.append_row([name, email, picture])  # Ensure the name and email are present
    else:
        print("User information is incomplete, not saving to sheet.")


@app.route('/login')
def index():
    return render_template('form.html')  




# Load the Groq API key
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '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')
def check_spelling(text):
    """Function to check spelling using Groq API."""
    try:
        response = requests.post(
            'https://api.groq.com/v1/process-text',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={"text": text}
        )
        
        # Print the response to debug
        print(f"API Response JSON: {result}", flush=True)

        if response.status_code == 200:
            result = response.json()
            return result.get("processed_text", text)  # Return corrected text if available
        else:
            return text  # Return original text if API error occurs
    except Exception as e:
        print(f"Error with Groq API: {e}")
        return text  # Return original text if an exception occurs




@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Collect form data
    data = {
        "production_date": request.form['production_date'],
        "code": request.form['code'],
        "green_coffee_name": request.form['green_coffee_name'],
        "tel_name": request.form['tel_name'],
        "origin": request.form['origin'],
        "producer": request.form['producer'],
        "process": request.form['process'],
        "elevation": request.form['elevation'],
        "region": request.form['region'],
        "variety": request.form['variety'],
        "tasting_notes": request.form['tasting_notes'],
        "tags": request.form['tags'],
        "filter_wholesale_price_2lb": request.form['filter_wholesale_price_2lb'],
        "espresso_wholesale_price_2lb": request.form['espresso_wholesale_price_2lb'],
        "filter_wholesale_price_8oz": request.form['filter_wholesale_price_8oz'],
        "espresso_wholesale_price_8oz": request.form['espresso_wholesale_price_8oz'],
        "filter_retail_price_8oz": request.form['filter_retail_price_8oz'],
        "espresso_retail_price_8oz": request.form['espresso_retail_price_8oz'],
        "retail_with_box_price_8oz": request.form['retail_with_box_price_8oz'],
        "jar_with_box_price_40gr": request.form['jar_with_box_price_40gr'],
        "jar_normal_price_40gr": request.form['jar_normal_price_40gr'],
        "price_100g": request.form['price_100g']
    }

    # Check spelling of 'tasting_notes' field
    data['tasting_notes'] = check_spelling(data['tasting_notes'])

    # Define the CSV file path
    csv_file = 'data.csv'
    file_exists = os.path.isfile(csv_file)

    # Write to the CSV file
    with open(csv_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())

        # Write header if file does not exist
        if not file_exists:
            writer.writeheader()

        # Write the form data to the CSV
        writer.writerow(data)

    return redirect(url_for('index'))  # Redirect to the form page after submission













# Replace with your actual Groq API key
GROQ_API_KEY = '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'


def process_text_with_groq(text):
    try:
        endpoint = 'https://api.groq.com/openai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',  # Your API key
            'Content-Type': 'application/json'
        }

        # Specify the model in the payload
        payload = {
            "model": "llama3-groq-8b-8192-tool-use-preview",
            "messages": [
                {"role": "user", "content": text}
            ]
        }

        response = requests.post(endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            processed_text = response.json().get('choices', [{}])[0].get('message', {}).get('content', text)
            return processed_text, None  # Return processed text and None for error
        else:
            return None, response.text  # Return None for processed text and error message
    except Exception as e:
        return None, str(e)  # Return None for processed text and the exception message
    

    
@app.route('/process', methods=['POST'])
def process_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text']
    processed_text, error = process_text_with_groq(text)
    
    if error:
        return jsonify({'error': error or 'Processing failed'}), 500

    return jsonify({'processed_text': processed_text})














@app.route('/process', methods=['GET'])
def process_page():
    return render_template('index.html')  # Assuming you want to render index.html here





# # Replace with your actual Groq API key
# GROQ_API_KEY = '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'

# def check_spelling(text):
#     """Function to check spelling using Groq API."""
#     try:
#         print(f"Requesting spelling correction for: {text}")  # Debugging line
#         response = requests.post(
#             'https://api.groq.com/openai/v1/chat/completions',
#             headers={
#                 'Authorization': f'Bearer {GROQ_API_KEY}',
#                 'Content-Type': 'application/json'
#             },
#             json={
#                 "model": "llama3-groq-8b-8192-tool-use-preview",
#                 "messages": [{"role": "user", "content": text}]
#             }
#         )

#         print(f"API Status Code: {response.status_code}")  # Debugging line
#         print(f"API Response JSON: {response.json() if response.content else 'No Content'}", flush=True)

#         if response.status_code == 200:
#             result = response.json()
#             return result.get("choices", [{}])[0].get("message", {}).get("content", text)  # Extract the corrected text
#         else:
#             return text  # Return original text if API error occurs
#     except Exception as e:
#         print(f"Error with Groq API: {e}")
#         return text  # Return original text if an exception occurs

    
# @app.route('/process', methods=['POST'])
# def process_text():
#     data = request.get_json()
#     if not data or 'text' not in data:
#         return jsonify({'error': 'No text provided'}), 400

#     text = data['text']
#     processed_text, error = process_text_with_groq(text)
    
#     if error:
#         return jsonify({'error': error or 'Processing failed'}), 500

#     return jsonify({'processed_text': processed_text})














# @app.route('/process', methods=['GET'])
# def process_page():
#     return render_template('index.html')  # Assuming you want to render index.html here









if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)  
