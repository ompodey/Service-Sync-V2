import pandas as pd
import requests

# Path to your refined Excel file
file_path = "refined_service_providers.xlsx"  # Adjust path if necessary

# Read the Excel file
data = pd.read_excel(file_path)

# URL of the Flask endpoint
api_url = "http://127.0.0.1:5000/registration/professional"  # Adjust URL as per your setup

# Iterate over each entry in the DataFrame and send POST requests
for index, row in data.iterrows():
    try:
        # Prepare the data for the POST request
        payload = {
            "name": row["name"],
            "professionaltype": row["professionaltype"],
            "servicetype": row["servicetype"],
            "servicename": row["servicename"],
            "description": row["description"],
            "address": row["address"],
            "pincode": row["pincode"],
            "email": row["email"],
            "contact": row["contact"],
            "experience": row["experience"],
            "timerequired": row["timerequired"],
            "bookingcharge": row["bookingcharge"],
            "tags": row["tags"],
            "password": row["password"]
        }

        # Simulate file uploads (replace these with actual file paths for testing)
        files = {
            "photo": (row["photo"], open(f"photos/{row['photo']}", "rb")),
            "lisence": (row["lisence"], open(f"licenses/{row['lisence']}", "rb"))
        }

        # Make the POST request
        response = requests.post(api_url, data=payload, files=files)

        # Print response for each request
        if response.status_code == 200:
            print(f"Successfully added: {row['servicename']}")
        else:
            print(f"Failed to add: {row['servicename']} - {response.text}")

    except Exception as e:
        print(f"Error processing entry {row['servicename']}: {e}")
