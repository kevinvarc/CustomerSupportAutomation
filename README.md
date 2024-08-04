# CustomerSupportAutomation
Automation of customer support using Go High Level API and OpenAI's Assistant API. It receives data from two webhooks sent by GHL to initiate the conversation and generate a response from the model of your choice.

In this case, I use Supabase, but you can change it to use function calling with the database of your choice.

Go High Level API V1 is used. It won't work with other CRMs, so you must make the necessary changes based on your CRM's documentation.

You need to create the corresponding automation workflow in High Level to receive the webhook request via POST and parse the necessary JSON values.