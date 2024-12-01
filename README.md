# Converge - AI-Powered Meeting Assistant

Converge is a Slack bot that helps facilitate better meetings by:
- Collecting and analyzing input from team members
- Facilitating AI-powered discussions between virtual agents representing team members
- Generating comprehensive reports and summaries
- Providing personalized preparation guidance to individual team members

## Features
- Voice message transcription
- PDF document analysis
- Multi-agent discussions
- Personalized meeting preparation
- Automated report generation

## Demo

Video coming soon

## Setup
1. Install dependencies:

```
pip install -r requirements.txt
```

2. Create a .env file with:

```
OPENAI_API_KEY=your_key
SLACK_BOT_TOKEN=your_token
SLACK_SIGNING_SECRET=your_secret
LLAMA_CLOUD_API_KEY=your_key
```

3. Run the Flask server:

```
python app.py
```

4. Connect this Slack app to your Slack workspace

4.1 Set Up Bot Token and Permissions
Go to the OAuth & Permissions section in the left-hand menu. Under the Scopes section, add the following bot token scopes:
- app_mentions:read
- channels:history
- chat:write
- im:history
- users:read
- Click Save Changes.

4.2 Install the App
Navigate to the Install App section in the left-hand menu. Click Install to Workspace and authorize the app for your workspace. Copy the Bot User OAuth Token provided after installation.

4.3 Configure the Signing Secret
In the Basic Information section, locate the Signing Secret under App Credentials. Copy this value for use in your environment variables.

4.4 Set Up Event Subscriptions
Go to the Event Subscriptions section and toggle the Enable Events button to On. Under Request URL, enter the public URL of your server (e.g., from ngrok). The URL should end with the route that handles Slack requests, e.g., https://your-public-url.com/. Ensure your server is running to verify the request. Subscribe to events like app_mention or message.im under the Subscribe to Bot Events section.

## Architecture

- app.py - Main Slack bot application
- agents.py - AI agent implementation
- leader_discussion.py - Leadership discussion handler
- team_member_discussion.py - Team member discussion handler
- generate_final_report.py - Final report generation
- Support utilities: 
    - transcribe_voice_input.py 
    - extract_text_from_pdf.py
