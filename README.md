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

TODO

## Architecture

- app.py - Main Slack bot application
- agents.py - AI agent implementation
- leader_discussion.py - Leadership discussion handler
- team_member_discussion.py - Team member discussion handler
- generate_final_report.py - Final report generation
- Support utilities: 
    - transcribe_voice_input.py 
    - extract_text_from_pdf.py
