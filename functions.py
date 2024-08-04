import requests
import pkg_resources
import subprocess
import sys
import os
import json
from datetime import datetime
from openai import OpenAI
from supabase import create_client, Client


SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_API_KEY = os.environ.get('SUPABASE_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=OPENAI_API_KEY)

def upgrade_open_ai_library ():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "openai"])
        print("OpenAI library has been successfully upgraded.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to upgrade the OpenAI library: {e}")

def get_openai_version():
    try:
        # Get the distribution information for the 'openai' package
        openai_version = pkg_resources.get_distribution("openai").version
        return openai_version
    except pkg_resources.DistributionNotFound:
        # Handle the case where the 'openai' package is not installed
        print("OpenAI library is not installed in the current environment.")



def maintenance_date(phone):
    """
    Your database logic
    """
   


def find_invoices_by_phone(phone=None):
    
    """
    Your database logic
    """



def create_assistant(client):
    assistant_path = 'assistant.json'

    if os.path.exists(assistant_path):
      with open(assistant_path, 'r') as file:
        assistant_data = json.load(file)
        assistant_id = assistant_data['assistant_id']
        print("Loaded existing assistant ID.")
    else:
       
        """
            Define the criteria to create your assistant
        """

with open(assistant_path, 'w') as file:
    
    json.dump({'assistant_id': assistant.id}, file)
    print("Created a new assistant and saved the ID.")
    assistant_id = assistant.id
        
    return assistant_id
