import json
import requests
import functions
import os
import threading
import openai
import time
from openai import OpenAI 
from flask import Flask, request, jsonify, after_this_request
from supabase import create_client, Client
from packaging import version

required_version = version.parse(functions.get_openai_version())
current_version = version.parse(openai.__version__)

# Change it for your database to add proper validation

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_API_KEY = os.environ.get('SUPABASE_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
GHL_API_KEY = os.environ['GHL_API_KEY']  

if current_version < required_version:
    functions.upgrade_open_ai_library()
else:
    print("OpenAI version is compatible.")

app = Flask(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


ghl_api_base_url = "https://rest.gohighlevel.com/v1"  # Adjust if needed

assistant_id = functions.create_assistant(client)

@app.route('/start', methods=['POST'])
def start_conversation():
    data = request.json
    print("Received data:", json.dumps(data, indent=4))

    thread_id = data.get('Thread_id')
    contact_id = data.get('contact_id')

    if not thread_id:
        # No Thread_id provided, create a new thread
        print("No Thread_id provided, creating a new thread...")
        thread = client.beta.threads.create()
        new_thread_id = thread.id
        print(f"New thread created with ID: {new_thread_id}")

        # Define a local function to update the custom field
        def update_custom_field_local(contact_id, field_id, new_value):
            """Update a specific custom field for a contact in Go High Level."""
            url = f"https://rest.gohighlevel.com/v1/contacts/{contact_id}"
            headers = {
                "Authorization": f"Bearer {GHL_API_KEY}",
                "Content-Type": "application/json"
            }
            data = json.dumps({
                "customField": {
                    field_id: new_value
                }
            })

            response = requests.put(url, headers=headers, data=data)
            if response.status_code == 200:
                print(f"Custom field '{field_id}' updated successfully with value '{new_value}'.")
                return response.json()
            else:
                print(f"Failed to update custom field '{field_id}': {response.status_code} - {response.text}")
                return None

        # Update the custom field 'Thread_id' with the new thread ID
        print("Updating custom field with new thread ID...")
        update_custom_field_local(contact_id, 'ID_of_the_custom_field', new_thread_id)

        # Return response with new thread ID
        return jsonify({"thread_id": new_thread_id, "message": "New thread created and custom field updated."}), 200
    else:
        # Thread_id is provided, validate and return confirmation
        print(f"Thread_id '{thread_id}' provided, no new thread creation needed.")
        return jsonify({"message": "Thread validated"}), 200




@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    print("Received data:", json.dumps(data, indent=4))

    thread_id = data.get('Thread_id')
    user_input = data.get('message', {}).get('body', '')
    contact_id = data.get('contact_id')
    phone = data.get('phone')

    print(f"Thread ID: {thread_id}")
    print(f"User Input: {user_input}")
    print(f"Contact ID: {contact_id}")
    print(f"Phone: {phone}")

    # Remove '+1' prefix
    if phone.startswith('+1'):
        phone = phone[2:]

    response_data = {"response": ""}
    try:
        print("Checking phone number in Supabase database...")
        response = supabase.from_('customers').select('phone').eq('phone', phone).execute()
        print(f"Supabase response: {response.data}")
        if not response.data:
            print("Phone number not found in the database.")
            response_data["response"] = "Sorry, but your number is not present in our registers. If you think this is an error, reply 'human support'."
            # Send response immediately
            result = jsonify(response_data)
            result.status_code = 200

            # Start a new thread to update the custom field after sending the response
            def update_custom_field_task():
                print("Waiting before updating custom field...")
                time.sleep(1.5)  # Add delay to ensure response is sent
                print("Updating custom field...")
                update_contact_custom_field(contact_id, 'ID_of_the_custom_field', response_data['response'])

            threading.Thread(target=update_custom_field_task).start()
            return result
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return jsonify({"response": "An error occurred while verifying your phone number. Please try again later."})

    try:
        print(f"Attempting to send message: '{user_input}' for thread ID: {thread_id}")
        message_response = client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)
        print(f"Message sent response: {message_response}")

        print("Creating run...")
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
        print(f"Run created with ID: {run.id}")

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            print(f"Checking run status: {run_status.status}")

            if run_status.status == 'completed':
                print("Run completed successfully.")
                break
            elif run_status.status == 'requires_action':
                for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                    if tool_call.function.name == "find_invoices_by_phone":
                        
                        print(f"Executing function call: {tool_call.function.name}")
                      
                    arguments = json.loads(tool_call.function.arguments)
                    output = functions.find_invoices_by_phone(phone)
                    client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                                   run_id=run.id,
                                                                   tool_outputs=[{
                                                                       "tool_call_id":
                                                                       tool_call.id,
                                                                       "output":
                                                                       json.dumps(output)
                                                                   }])

        print("Retrieving assistant response...")
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        assistant_response = messages.data[0].content[0].text.value
        print(f"Assistant response: {assistant_response}")

        response_data = {"response": assistant_response}
    except Exception as e:
        print(f"Error in chat workflow: {e}")
        response_data = {"response": "An error occurred during the workflow. Please try again later. Reply 'Human support' for assistance."}

    # Return response to client
    print("Returning response to client.")
    result = jsonify(response_data)
    result.status_code = 200

    # Start a new thread to update the custom field after sending the response
    def update_custom_field_task():
        print("Waiting before updating custom field...")
        time.sleep(1)  # Add delay to ensure response is sent
        print("Updating custom field...")
        update_contact_custom_field(contact_id, 'ID_of_the_custom_field', response_data['response'])

    threading.Thread(target=update_custom_field_task).start()

    return result

def update_contact_custom_field(contact_id, field_id, new_value):
    """Update a specific custom field for a contact in Go High Level."""
    url = f"https://rest.gohighlevel.com/v1/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "customField": {
            field_id: new_value
        }
    })

    response = requests.put(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Custom field updated successfully.")
        return response.json()
    else:
        print(f"Failed to update custom field: {response.status_code} - {response.text}")
        return None



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
