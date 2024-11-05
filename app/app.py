import csv
import os
import urllib.parse as urlparse
import requests
from google.oauth2 import service_account
from flask import Flask, flash, jsonify, redirect, request, url_for, session, render_template
import gspread
import re 
import pandas as pd  # Ensure pandas is imported
import logging
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use an environment variable for secret key

# Constants for Google OAuth
CLIENT_ID = os.environ.get('CLIENT_ID')  # Your CLIENT_ID
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')  # Your CLIENT_SECRET
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://127.0.0.1:8000/callback')


logging.basicConfig(level=logging.DEBUG)

# Example usage
logging.debug("This is a debug message.")
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

# def format_checked_spelling(corrected_text):
#     """Formats the corrected spelling into a readable format."""
#     formatted_texts = []
    
#     # Split the corrected text into individual notes (if you expect multiple notes)
#     notes = [note.strip() for note in corrected_text.splitlines() if note.strip()]  # Split by lines and remove empty lines
    
#     print("Original Notes:", notes)  # Debugging line to see the original notes

#     for note in notes:
#         # Check if the note is a string and strip whitespace
#         if isinstance(note, str):
#             note = note.strip()
#             if note:  # If not an empty line
#                 # Replace 'and' with '&' to match the requested format
#                 note = note.replace(' and ', ' & ')
                
#                 # Further customize how we want to format each note
#                 formatted_note = note.capitalize() + '.'  # Capitalize and add a period at the end
                
#                 # Print the formatted note for debugging
#                 print(f"Formatted Note: {formatted_note}")  # Debugging line
                
#                 formatted_texts.append(formatted_note)
#             else:
#                 formatted_texts.append('')  # Maintain blank lines as is
#         else:
#             formatted_texts.append('')  # Append empty if not a string (like NaN)

#     print("Final Formatted Texts:", formatted_texts)  # Debugging line to see final formatted texts
#     return formatted_texts


# def check_spelling(text):
#     """Function to check spelling using Groq API."""
#     try:
#         print(f"Requesting spelling correction for: {text}")  # Debugging line
        
#         # Prepare the refined prompt for the API request
#         prompt = f"Please correct the spelling of the following list items text. In your response, only provide the corrected spelling. If the spelling is already corrected items, simply return the original text without any changes (important :no other response required , dont add any other response .): '{text}'."

#         # Send request to Groq API
#         response = requests.post(
#             'https://api.groq.com/openai/v1/chat/completions',
#             headers={
#                 'Authorization': f'Bearer {GROQ_API_KEY}',
#                 'Content-Type': 'application/json'
#             },
#             json={
#                 "model": "llama3-groq-8b-8192-tool-use-preview",
#                 "messages": [{"role": "user", "content": prompt}]
#             }
#         )

#         print(f"API Status Code: {response.status_code}")  # Debugging line
#         print(f"API Response JSON: {response.json() if response.content else 'No Content'}", flush=True)

#         if response.status_code == 200:
#             result = response.json()
#             corrected_text = result.get("choices", [{}])[0].get("message", {}).get("content", text)  # Extract the corrected text
            
#             # Directly format the corrected text
#             formatted_texts = []
#             notes = [note.strip() for note in corrected_text.splitlines() if note.strip()]  # Split by lines and remove empty lines
            
#             print("Original Notes:", notes)  # Debugging line to see the original notes

#             for note in notes:
#                 if isinstance(note, str):
#                     note = note.strip()
#                     if note:  # If not an empty line
#                         note = note.replace(' and ', ' & ')  # Replace 'and' with '&'
#                         formatted_note = note.capitalize() + '.'  # Capitalize and add a period
#                         print(f"Formatted Note: {formatted_note}")  # Debugging line
#                         formatted_texts.append(formatted_note)
#                     else:
#                         formatted_texts.append('')  # Maintain blank lines as is
#                 else:
#                     formatted_texts.append('')  # Append empty if not a string

#             print("Final Formatted Texts:", formatted_texts)  # Debugging line to see final formatted texts
            
#             # Print the formatted text
#             for formatted_note in formatted_texts:
#                 print(formatted_note)
                
#             return formatted_texts  # Return formatted texts if needed
#         else:
#             # If API error occurs, return the original text formatted
#             formatted_texts = []
#             notes = [note.strip() for note in text.splitlines() if note.strip()]  # Split by lines and remove empty lines
            
#             for note in notes:
#                 if isinstance(note, str):
#                     note = note.strip()
#                     if note:
#                         note = note.replace(' and ', ' & ')
#                         formatted_note = note.capitalize() + '.'
#                         formatted_texts.append(formatted_note)
#                     else:
#                         formatted_texts.append('')
#                 else:
#                     formatted_texts.append('')

#             for formatted_note in formatted_texts:
#                 print(formatted_note)
                
#             return formatted_texts
#     except Exception as e:
#         print(f"Error with Groq API: {e}")
#         formatted_texts = []
#         notes = [note.strip() for note in text.splitlines() if note.strip()]  # Split by lines and remove empty lines
        
#         for note in notes:
#             if isinstance(note, str):
#                 note = note.strip()
#                 if note:
#                     note = note.replace(' and ', ' & ')
#                     formatted_note = note.capitalize() + '.'
#                     formatted_texts.append(formatted_note)
#                 else:
#                     formatted_texts.append('')
#             else:
#                 formatted_texts.append('')

#         for formatted_note in formatted_texts:
#             print(formatted_note)
        
#         return formatted_texts  # Return formatted original text if an exception occurs





# def check_spelling(text):
#     """Function to check spelling using Groq API."""
#     try:
#         print(f"Requesting spelling correction for: {text}")  # Debugging line
        
#         # Define a prompt that specifies the required output
#         # prompt = f"Correct the spelling in the following text and return only the corrected text: '{text}'. No additional responses."
#     # Prepare the refined prompt for the API request
#         # prompt = f"Please correct the spelling of the following text. In your response, only provide the corrected spelling. If the spelling is already correct, simply return the original text without any changes : '{text}'."
#         prompt = f"Please correct the spelling of the following list items text. In your response, only provide the corrected spelling. If the spelling is already corrected items, simply return the original text without any changes (important :no other response required , dont add any other response or characters.): '{text}'."

#         # Send request to Groq API  
#         response = requests.post(
#             'https://api.groq.com/openai/v1/chat/completions',
#             headers={
#                 'Authorization': f'Bearer {GROQ_API_KEY}',
#                 'Content-Type': 'application/json'
#             },
#             json={
#                 "model": "llama3-groq-8b-8192-tool-use-preview",
#                 "messages": [{"role": "user", "content": prompt}]
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




def check_spelling(text):
    """Function to check spelling using Groq API."""
    try:
        print(f"Requesting spelling correction for: '{text}'")  # Debugging line
        
        prompt = (
            f"Please correct the spelling of the following list items text. "
            f"In your response, only provide the corrected spelling. "
            f"If the spelling is already correct, simply return the original text without any changes. "
            f"(Important: no other response required, don't add any other response or characters and also dont change the format): '{text}'."
        )

        # Send request to Groq API  
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                "model": "llama3-groq-8b-8192-tool-use-preview",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        print(f"API Status Code: {response.status_code}")  # Debugging line
        
        if response.status_code == 200:
            result = response.json()
            corrected_text = result.get("choices", [{}])[0].get("message", {}).get("content", text)
            print(f"Corrected Text: '{corrected_text}'")  # Print the corrected text
            return corrected_text
        else:
            print(f"Error: Received unexpected status code {response.status_code} - {response.text}")
            return text  # Return original text if API error occurs

    except Exception as e:
        print(f"Error with Groq API: {e}")
        return text  # Return original text if an exception occurs











# Define the format_elevation function
def format_elevation(elevation):
    """Formats the elevation values."""
    elevation_str = str(elevation)
    numbers = [int(num) for num in re.findall(r'\d+', elevation_str)]
    
    if len(numbers) == 2:
        return f"{numbers[0]:,} - {numbers[1]:,} m"
    if len(numbers) == 1:
        return f"{numbers[0]:,} m"
    return elevation


@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Collecting data from the form
    data = {
        'production_date': request.form.get('production_date'),
        'code': request.form.get('code'),
        'green_coffee_name': request.form.get('green_coffee_name'),
        'tel_name': request.form.get('tel_name'),
        'origin': request.form.get('origin'),
        'producer': request.form.get('producer'),
        'process': request.form.get('process'),
        'elevation': format_elevation(request.form.get('elevation')),
        'region': request.form.get('region'),
        'variety': request.form.get('variety'),
        'tasting_notes': request.form.get('tasting_notes'),
        'tags': request.form.get('tags'),
        'filter_wholesale_price_2lb': request.form.get('filter_wholesale_price_2lb'),
        'espresso_wholesale_price_2lb': request.form.get('espresso_wholesale_price_2lb'),
        'filter_wholesale_price_8oz': request.form.get('filter_wholesale_price_8oz'),
        'espresso_wholesale_price_8oz': request.form.get('espresso_wholesale_price_8oz'),
        'filter_retail_price_8oz': request.form.get('filter_retail_price_8oz'),
        'espresso_retail_price_8oz': request.form.get('espresso_retail_price_8oz'),
        'retail_with_box_price_8oz': request.form.get('retail_with_box_price_8oz'),
        'jar_with_box_price_40gr': request.form.get('jar_with_box_price_40gr'),
        'jar_normal_price_40gr': request.form.get('jar_normal_price_40gr'),
        'price_100g': request.form.get('price_100g')
    }
    
    print("Collected Data:", data)  # Debug print

    # Create a DataFrame from the collected form data
    form_df = pd.DataFrame([data])

    # Load existing data from CSV or create an empty DataFrame if the file doesn't exist
    try:
        df = pd.read_csv('data.csv')
    except FileNotFoundError:
        df = pd.DataFrame()  # Create an empty DataFrame if the file does not exist





    # Add new columns if they do not exist in the DataFrame
    new_columns = ['SKU', 'DESCRIPTION', 'CATEGORY', 'SUB-CATEGORY', 'TYPE', 'SIZE']
    for col in new_columns:
        if col not in df.columns:
            df[col] = ""  # Initialize new columns with empty strings

    # Check for duplicates based on 'code'
    if not df[df['code'] == data['code']].empty:
        flash('Data with this code already exists. Please use a different code.', 'error')
        return redirect(url_for('index'))






    
    # Process tasting notes as a list initially
    tasting_notes = request.form.get('tasting_notes')
    tasting_notes_list = [note.strip() for note in tasting_notes.strip("'\"").split(',')]
    tasting_notes_str = ', '.join(tasting_notes_list)  # Convert list to a single string

    # Run the spelling check on the joined string
    corrected_tasting_notes_str = check_spelling(tasting_notes_str)

    # Convert the corrected string back to a list and capitalize each item
    corrected_tasting_notes_list = [note.strip().capitalize() for note in corrected_tasting_notes_str.split(',')]

    # Format tasting notes with ' & ' before the last item
    if len(corrected_tasting_notes_list) > 1:
        formatted_tasting_notes = ', '.join(corrected_tasting_notes_list[:-1]) + ' & ' + corrected_tasting_notes_list[-1]
    else:
        formatted_tasting_notes = corrected_tasting_notes_list[0] if corrected_tasting_notes_list else ''

    # Assign the formatted notes back to `data` and `form_df` for CSV storage
    data['tasting_notes'] = corrected_tasting_notes_list
    form_df['tasting_notes'] = formatted_tasting_notes


















    # Prepare to expand rows based on variations
    expanded_rows = []
    last_serial = df['SKU'].apply(lambda x: int(x.split('-')[-1]) if isinstance(x, str) and '-' in x else 0).max()
    

























    # Mapping of price columns to variations
    price_mapping = {
        "filter_wholesale_price_2lb": ('2Lb. Filter', 'Coffee', 'Wholesale'),
        "espresso_wholesale_price_2lb": ('2Lb. Espresso', 'Coffee', 'Wholesale'),
        "filter_wholesale_price_8oz": ('8oz. Filter', 'Coffee', 'Wholesale'),
        "espresso_wholesale_price_8oz": ('8oz. Espresso', 'Coffee', 'Wholesale'),
        "filter_retail_price_8oz": ('8oz. Filter', 'Coffee', 'Retail'),
        "espresso_retail_price_8oz": ('8oz. Espresso', 'Coffee', 'Retail'),
        "retail_with_box_price_8oz": ('8oz. Exclusive', 'Coffee', 'Retail'),
        "jar_with_box_price_40gr": ('40g Jar Exclusive', 'Coffee', 'Retail'),
        "jar_normal_price_40gr": ('40g Jar Plain', 'Coffee', 'Retail'),
        "price_100g": ('100g Filter', 'Coffee', 'Retail')
    }

    # Variations for each CODE
    variations = [
        ('2Lb. Filter', 'Coffee', 'Wholesale', 'Filter', '2Lb'),
        ('2Lb. Espresso', 'Coffee', 'Wholesale', 'Espresso', '2Lb'),
        ('8oz. Filter', 'Coffee', 'Retail', 'Filter', '8oz'),
        ('8oz. Espresso', 'Coffee', 'Retail', 'Espresso', '8oz'),
        ('8oz. Exclusive', 'Coffee', 'Retail', 'Filter', '8oz'),
        ('Drip Bags', 'Coffee', 'Retail', 'Drip', '163g'),
        ('40g Jar Exclusive', 'Coffee', 'Retail', 'Filter', '40g'),
        ('40g Jar Plain', 'Coffee', 'Retail', 'Filter', '40g'),
        ('100g Filter', 'Coffee', 'Retail', 'Filter', '100g'),
        ('100g Espresso', 'Coffee', 'Retail', 'Espresso', '100g')
    ]

    # Process each row of form data for variations
    for index, row in form_df.iterrows():
        for variation in variations:
            description, category, sub_category, type_, size = variation

            # Construct the SKU
            sku_elements = [
                str(row['code']) if not pd.isna(row['code']) else 'x',
                str(row['tel_name'])[0] if not pd.isna(row['tel_name']) else 'x',
                str(row['origin'])[0] if not pd.isna(row['origin']) else 'x',
                description[0],
                category[0],
                type_[0],
                size[0]
            ]

            last_serial += 1
            sku = "{}-{}-{:05}".format(sku_elements[0], ''.join(sku_elements[1:]), last_serial)

            # Create a new row based on the current row, but with variations
            new_row = row.copy()
            new_row['SKU'] = sku
            new_row['DESCRIPTION'] = description
            new_row['CATEGORY'] = category
            new_row['SUB-CATEGORY'] = sub_category
            new_row['TYPE'] = type_
            new_row['SIZE'] = size

            # Check for price and add it to the new row
            price = ''
            for price_col, price_variation in price_mapping.items():
                if price_variation[0] == description and price_variation[1:] == (category, sub_category):
                    price_value = form_df.loc[index, price_col]
                    if pd.notna(price_value) and float(price_value) > 0:
                        price = price_value
                    break

            # Special cases for '100g' and '40g Jar' variations
            if (description, category, sub_category) in [('100g Espresso', 'Coffee', 'Retail'),
                                                         ('40g Jar Exclusive', 'Coffee', 'Retail'),
                                                         ('40g Jar Plain', 'Coffee', 'Retail')]:
                if description.startswith('100g'):
                    price_col = "price_100g"
                elif 'Exclusive' in description:
                    price_col = "jar_with_box_price_40gr"
                else:
                    price_col = "jar_normal_price_40gr"

                price_value = form_df.loc[index, price_col]
                if pd.notna(price_value) and float(price_value) > 0:
                    price = price_value

            new_row['PRICE'] = price  # Add price to the new row
            expanded_rows.append(new_row)  # Append the new row to expanded rows list

    # Create a new DataFrame from the expanded rows
    expanded_df = pd.DataFrame(expanded_rows)

    # Append new form data to the DataFrame
    df = pd.concat([df, expanded_df], ignore_index=True)

    try:
        df.to_csv('data.csv', mode='w', header=True, index=False)  # Overwrite the file
        print("Data saved successfully.")
    except Exception as e:
        print("Error saving data:", e)  # Catch any errors during saving

    flash('Form submitted successfully!')  # Flash a success message
    return redirect(url_for('index'))  # Redirect back to the index page








if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)  
