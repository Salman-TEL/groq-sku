import csv
import io
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



app.debug = True
app.run(debug=True)






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






def check_spelling(text):
    """Function to check spelling using Groq API."""
    try:
        print(f"Requesting spelling correction for: '{text}'")  # Debugging line
        
        prompt = (
            f"Correct only the spelling in the following comma-separated list of items. "
            f"Rules: "
            f"1) Only correct spelling without changing structure, punctuation, or spacing. "
            f"2) Do not add any comments, explanations, or additional text. "
            f"3) Return only the corrected text as a comma-separated list exactly as shown in the input. "
            f"4) If all words are spelled correctly, return them exactly as they appear. "
            f"Text: '{text}'."
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





def get_next_code(df):
    # Retrieve the last code from the DataFrame
    if 'code' not in df.columns or df.empty:
        return 'A01'  # Start from A01 if no codes exist

    last_code = df['code'].max()  # Get the latest code from the DataFrame
    last_prefix = last_code[:-2]  # All except the last two characters
    last_number = int(last_code[-2:])  # Last two digits as a number

    if last_number < 99:  # If the number is less than 99, increment the last two digits
        next_number = last_number + 1
        next_code = f"{last_prefix}{next_number:02d}"  # Format to maintain 2 digits
    else:  # If number reaches 99, move to the next letter in the prefix (i.e., A to B)
        if last_prefix == 'Z':  # If it's already Z, no further code can be generated
            raise ValueError("No more codes can be generated.")
        next_prefix = chr(ord(last_prefix[0]) + 1)  # Increment the first letter of the prefix
        next_code = f"{next_prefix}01"  # Reset the number part to 01 after changing the prefix

    return next_code







@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Collecting data from the form
    data = {
        'production_date': request.form.get('production_date'),
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


    # Load existing data from CSV or create an empty DataFrame if the file doesn't exist
    try:
        df = pd.read_csv('data.csv')
    except FileNotFoundError:
        df = pd.DataFrame()  # Create an empty DataFrame if the file does not exist


    # Generate the next code using the get_next_code function
    try:
        new_code = get_next_code(df)
        data['code'] = new_code  # Assign the generated code to the data
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))



    # Create a DataFrame from the collected form data
    form_df = pd.DataFrame([data])























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

    # Log the output for debugging
    print("Corrected Tasting Notes String:", corrected_tasting_notes_str)  # Debug print

    # Convert the corrected string back to a list
    corrected_tasting_notes_list = [note.strip().title() for note in corrected_tasting_notes_str.split(',')]

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





@app.route('/view_data')
def view_data():
    try:
        # Load data from CSV
        df = pd.read_csv('data.csv')
        
        # Convert DataFrame to HTML
        data_html = df.to_html(classes='table table-striped', index=False)  # Use Bootstrap classes for styling
    except FileNotFoundError:
        data_html = "<p>No data found. Please submit the form first.</p>"
    except Exception as e:
        data_html = f"<p>Error reading data: {str(e)}</p>"

    return render_template('view_data.html', data_html=data_html)







# Define the column mapping from uploaded CSV to data.csv
COLUMN_MAPPING = {
    'Production Date': 'production_date',
    'Green Coffee Name': 'green_coffee_name',
    'TEL NAME': 'tel_name',
    'Origin': 'origin',
    'Producer': 'producer',
    'Process': 'process',
    'Elevation': 'elevation',
    'Region': 'region',
    'Variety': 'variety',
    'Tasting Notes': 'tasting_notes',
    'Tags': 'tags',
    '2Lb Filter Wholesale Price': 'filter_wholesale_price_2lb',
    '2Lb Espresso Wholesale Price': 'espresso_wholesale_price_2lb',
    '8oz Filter Wholesale Price': 'filter_wholesale_price_8oz',
    '8oz Espresso Wholesale Price': 'espresso_wholesale_price_8oz',
    '8oz Filter Retail Price': 'filter_retail_price_8oz',
    '8oz Espresso Retail Price': 'espresso_retail_price_8oz',
    '8oz Retail WITH BOX Price': 'retail_with_box_price_8oz',
    '40gr Jar WITH BOX Price': 'jar_with_box_price_40gr',
    '40gr Jar Normal Price': 'jar_normal_price_40gr',
    '100 grams Price': 'price_100g'
}

# Set the directory for uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the uploads directory exists

@app.route('/upload-csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        logging.debug("Debug: POST request received.")
        
        if 'file-upload' not in request.files:
            flash('No file part')
            logging.debug("Debug: 'file-upload' not found in request files.")
            return redirect(request.url)
        
        file = request.files['file-upload']
        
        if file.filename == '':
            flash('No selected file')
            logging.debug("Debug: File selected is empty.")
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                # Read and decode CSV content
                file_content = file.read().decode("utf-8")
                logging.debug("Debug: File content read successfully.")
                
                data = pd.read_csv(io.StringIO(file_content))
                logging.debug(f"Debug: CSV loaded into DataFrame: {data.head()}")  # Show first few rows for verification
                
                # Strip whitespace from columns
                data.columns = data.columns.str.strip()
                
                # Rename columns based on COLUMN_MAPPING
                data.rename(columns=COLUMN_MAPPING, inplace=True)
                logging.debug(f"Debug: Columns after renaming: {data.columns.tolist()}")
                
                # Check for missing columns
                required_columns = list(COLUMN_MAPPING.values())
                missing_columns = [col for col in required_columns if col not in data.columns]
                
                if missing_columns:
                    flash(f'Missing required columns in CSV: {", ".join(missing_columns)}')
                    logging.debug(f"Debug: Missing required columns: {missing_columns}")
                else:
                    logging.debug("Debug: All required columns are present.")
                
                # Pass the DataFrame to display template
                session['columns'] = data.columns.tolist()
                logging.debug("Debug: Rendering display_csv.html with data.")
                return render_template('display_csv.html', data=data)

            except Exception as e:
                flash(f'Error reading CSV file: {str(e)}')
                logging.debug(f"Debug: Exception during CSV processing: {e}")
                return redirect(request.url)
        else:
            flash('Please upload a valid CSV file')
            logging.debug("Debug: Invalid file type. Only CSV files are accepted.")
            return redirect(request.url)

    # Render upload form on GET request
    logging.debug("Debug: GET request for /upload-csv")
    return render_template('display_csv.html')








@app.route('/save-csv', methods=['POST'])
def save_csv():
    form_data = request.form.getlist('data')

    # Retrieve column names from session
    columns = session.get('columns')
    if not columns:
        flash('Session expired or column data unavailable. Please re-upload the file.')
        return redirect(url_for('upload_csv'))

    # Reshape the form data and create a DataFrame
    num_columns = len(columns)
    reshaped_data = [form_data[i:i + num_columns] for i in range(0, len(form_data), num_columns)]
    uploaded_data = pd.DataFrame(reshaped_data, columns=columns)

    # Check for missing or empty values
    if uploaded_data.isnull().values.any() or (uploaded_data == "").values.any():
        flash('All fields are required. Please fill in all fields before saving.')
        return redirect(url_for('upload_csv'))
    
    # Format elevation values
    uploaded_data['elevation'] = uploaded_data['elevation'].apply(format_elevation)

    # Correct tasting notes format and spelling
    def correct_tasting_notes(tasting_notes):
        tasting_notes_list = [note.strip() for note in tasting_notes.strip("'\"").split(',')]
        tasting_notes_str = ', '.join(tasting_notes_list)  # Convert list to a single string
        corrected_notes_str = check_spelling(tasting_notes_str)
        corrected_notes_list = [note.strip().title() for note in corrected_notes_str.split(',')]
        return ', '.join(corrected_notes_list[:-1]) + ' & ' + corrected_notes_list[-1] if len(corrected_notes_list) > 1 else corrected_notes_list[0]

    # Apply the correct_tasting_notes function to the 'tasting_notes' column
    uploaded_data['tasting_notes'] = uploaded_data['tasting_notes'].apply(correct_tasting_notes)

    # Load existing data from CSV for duplicate checking and SKU generation
    try:
        existing_data = pd.read_csv('data.csv')
    except FileNotFoundError:
        existing_data = pd.DataFrame()

    # Add new columns to existing data if they do not exist
    for col in ['SKU', 'DESCRIPTION', 'CATEGORY', 'SUB-CATEGORY', 'TYPE', 'SIZE']:
        if col not in existing_data.columns:
            existing_data[col] = ""

    # Ensure 'code' column exists in uploaded_data
    if 'code' not in uploaded_data.columns:
        uploaded_data['code'] = None

    # Generate 'code' for any rows without it
    def generate_code_if_missing(row):
        if pd.isna(row['code']) or row['code'] == "":
            row['code'] = get_next_code(existing_data)  # Generate code using existing_data
        return row

    # Apply code generation to rows without a 'code'
    uploaded_data = uploaded_data.apply(generate_code_if_missing, axis=1)

    # Expand rows based on variations and generate SKUs for each
    expanded_rows = []
    last_serial = existing_data['SKU'].apply(lambda x: int(x.split('-')[-1]) if isinstance(x, str) and '-' in x else 0).max()
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

    for _, row in uploaded_data.iterrows():
        for description, category, sub_category, type_, size in variations:
            # Generate SKU
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

            # Prepare expanded row data
            new_row = row.copy()
            new_row['SKU'] = sku
            new_row['DESCRIPTION'] = description
            new_row['CATEGORY'] = category
            new_row['SUB-CATEGORY'] = sub_category
            new_row['TYPE'] = type_
            new_row['SIZE'] = size

            # Map price columns to variations
            price_col = None
            if description.startswith("2Lb") and 'Filter' in description:
                price_col = 'filter_wholesale_price_2lb'
            elif description.startswith("2Lb") and 'Espresso' in description:
                price_col = 'espresso_wholesale_price_2lb'
            elif description.startswith("8oz") and 'Filter' in description:
                price_col = 'filter_wholesale_price_8oz'
            elif description.startswith("8oz") and 'Espresso' in description:
                price_col = 'espresso_wholesale_price_8oz'
            elif 'Exclusive' in description:
                price_col = 'retail_with_box_price_8oz' if '8oz' in description else 'jar_with_box_price_40gr'
            elif 'Plain' in description:
                price_col = 'jar_normal_price_40gr'
            elif '100g' in description:
                price_col = 'price_100g'

            new_row['PRICE'] = row[price_col] if price_col and pd.notna(row[price_col]) and float(row[price_col]) > 0 else ''

            expanded_rows.append(new_row)

    # Append expanded rows to existing data and save
    expanded_data = pd.DataFrame(expanded_rows)
    combined_data = pd.concat([existing_data, expanded_data], ignore_index=True)

    try:
        combined_data.to_csv('data.csv', mode='w', header=True, index=False)
        flash('CSV file processed successfully!')
        logging.debug("Debug: Data saved to data.csv successfully.")
    except Exception as e:
        flash(f'Error saving CSV file: {str(e)}')
        logging.error(f"Error saving CSV file: {str(e)}")

    return redirect(url_for('view_data'))

























@app.route('/save-edits', methods=['POST'])
def save_edits():
    try:
        # Get edited data from the request
        edited_data = request.json.get('data', [])
        
        # Load your existing data to determine the column names
        existing_df = pd.read_csv('/app/data.csv')
        column_names = existing_df.columns.tolist()
        
        # Convert the edited data to a DataFrame with the correct columns
        df = pd.DataFrame(edited_data, columns=column_names)
        
        # Save the edited DataFrame back to `data.csv`
        df.to_csv('/app/data.csv', index=False)
        
        return jsonify({'message': 'Changes saved successfully!'})
    except Exception as e:
        print(f"Error saving changes: {e}")
        return jsonify({'message': 'Error saving changes.'}), 500












if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)  
