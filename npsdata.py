import requests
import pandas as pd
import requests

url = "https://mcml.contegris.com/formBuilder/formData/6823387906ff2ff487c8ebd8/search?from=2025-08-16 11:30:00&to=2025-09-16 12:30:00&offset=10&limit=10000"

payload = {}
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJ1c2VyMSIsImlhdCI6MTc0NDI2OTk2MiwiZXhwIjoxNzQ0MjczNTYyfQ.CNfM5sBnw3aZgz81snBF-HV4FdIC4OvTnfPlFLjLe4g'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

# if response.status_code == 200:
records = response.json().get('records', [])
if records:
    data = pd.DataFrame(records)
    data = data[~data['job_id'].isnull()]
    data = data.rename(columns={'job_id': 'jobcardnumber'})
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
    print(f"Found {len(data)} new survey responses.")
data.to_csv('NPS.csv')
#     return data
# else:
#     print("No new survey responses found.")
#     return None
# else:
# print(f"API request failed: {response.status_code}")
# return None
# except Exception as e:
# print(f"Error fetching survey data: {e}")
# return None