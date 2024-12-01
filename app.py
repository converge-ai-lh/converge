import os
from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from leader_discussion import LeadershipDiscussionBot
from team_member_discussion import TeamMemberDiscussionBot
from agents import *
from utils.transcribe_voice_input import process_speech_bytes_to_text
from utils.extract_text_from_pdf import extract_text_from_pdf_url
import re
import glob

# Load environment variables from .env file
load_dotenv()

# Initialize the Slack app with authentication tokens
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Dictionary to track conversation state for each user
user_state = {}

@app.event("message")
def handle_message_events(body, say, client):
    """
    Main message event handler for Slack messages.
    Processes incoming messages, manages conversation flow, and coordinates AI agents.
    
    Args:
        body: Message event payload from Slack
        say: Function to send messages to Slack
        client: Slack client instance
    """
    # Ignore bot messages to prevent loops
    if "subtype" in body["event"] and body["event"]["subtype"] == "bot_message":
        return
    if "subtype" in body["event"] and body["event"]["subtype"] == "message_changed":
        return

    #print(body["event"])
    user_id = body["event"]["user"]
    text = body["event"]["text"].lower().strip()
    thread_ts = body["event"].get("thread_ts", body["event"]["ts"])

    # Process any attached audio or PDF files
    if 'files' in body["event"] and body["event"]["files"]:
        for file in body["event"]["files"]:
            if "audio" in file["mimetype"]:
                headers = {
                    'Authorization': f'Bearer {os.getenv("SLACK_BOT_TOKEN")}'
                }
        
                transcript = process_speech_bytes_to_text(
                    file_type='m4a',
                    url=file['url_private_download'],
                    headers=headers
                )
                text += f'{transcript} '
            elif "pdf" in file["mimetype"]:
                headers = {
                    'Authorization': f'Bearer {os.getenv("SLACK_BOT_TOKEN")}'
                }
        
                text += f'{extract_text_from_pdf_url(file["url_private_download"], headers)} '

    # Initialize state for new users
    if user_id not in user_state:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] 
        user_state[user_id] = {"step": None, "bot": None, "conversation": None, "real_name": user_name, "thread_ts": None}

    # Get or create DM conversation with user
    if user_state[user_id]['conversation'] is None:
        conversations = client.conversations_list(types="im")["channels"]
        user_conversation = next((conv for conv in conversations if conv["user"] == user_id), None)
        
        if user_conversation:
            user_state[user_id]['conversation'] = user_conversation['id']
        else:
            ch = client.conversations_open(users=[user_id])
            user_state[user_id]['conversation'] = ch['channel']['id']
    
    if user_state[user_id]['thread_ts'] is None:
        user_state[user_id]['thread_ts'] = thread_ts

    # Start new conversation flow
    if user_state[user_id]["step"] is None:
        user_state[user_id]["step"] = "start_conversation"

        user_state[user_id]["bot"] = LeadershipDiscussionBot()
        
        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Please describe the situation and decision you need help with. Include context, key concerns, and any initial thoughts.",
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )
        return
    
    elif user_state[user_id]["step"] == "start_conversation":
        user_state[user_id]["step"] = "ask_clarifying_questions"

        user_state[user_id]["bot"].collect_initial_situation(text)

        ai_message = user_state[user_id]["bot"].ask_clarifying_questions()
        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text=ai_message,
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )

        return

    elif user_state[user_id]["step"] == "ask_clarifying_questions":
        user_state[user_id]["step"] = "generate_final_report"

        user_state[user_id]["bot"].handle_clarifying_response(text)

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Who do you want to include in the meting?",
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )
        return

    elif user_state[user_id]["step"] == "generate_final_report":
        # Extract mentioned users and filter out the bot
        mentioned_users = re.findall(r"<@([a-zA-Z0-9]+)>", text)
        bot_user_id = client.auth_test()['user_id']
        mentioned_users = [user.strip().upper() for user in mentioned_users if user != bot_user_id] + [user_id]

        report = user_state[user_id]["bot"].generate_final_report()

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Thanks, the report was saved and shared with the team.",
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )

        # Share report with all mentioned users
        for user in mentioned_users:
            try:
                target_user_id = user
                dm_channel = client.conversations_open(users=[target_user_id], return_im=True)

                # Initialize state for new target users
                if target_user_id not in user_state:
                    user_info = client.users_info(user=target_user_id)
                    user_name = user_info["user"]["real_name"] 
                    conv = dm_channel['channel']['id']
                    user_state[target_user_id] = {"step": None, "bot": None, "conversation": conv, "real_name": user_name, "thread_ts": None}
                user_state[target_user_id]["step"] = "initialize_discussion"
                
                # Send report to original user or other team members
                if target_user_id == user_id:
                    # leader is ready to wait for the team members to respond
                    user_state[user_id]["step"] = "start_interagent_discussion"

                    # Create the report based on what he said before
                    user_state[user_id]["bot"].generate_team_member_report(user_state[user_id]["real_name"])

                    client.chat_postMessage(
                        channel=user_state[user_id]['conversation'],
                        text=f"Thanks for sharing your thoughts. here is the report : {report}. I'll go discuss with other AI agents now!",
                        thread_ts=user_state[user_id]['thread_ts'],
                        username=f"{user_state[user_id]["real_name"]} Agent",
                        icon_emoji=":robot_face:"
                    )
                else:
                    client.chat_postMessage(
                        channel=dm_channel['channel']['id'],
                        text=f"Hello! New meeting scheduled, your thoughts are needed! {report} What are your thoughts?",
                        username=f"{user_state[target_user_id]["real_name"]} Agent",
                        icon_emoji=":robot_face:"
                    )

            except Exception as e:
                print(f"Error sending DM: {e}")

        return
    
    elif user_state[user_id]["step"] == "initialize_discussion":
        user_state[user_id]["step"] = "answer_agent_questions"

        user_state[user_id]["bot"] = TeamMemberDiscussionBot()
        user_state[user_id]["bot"].initialize_discussion(user_state[user_id]["real_name"])
        user_state[user_id]["bot"].collect_initial_opinion(text)

        ai_message = user_state[user_id]["bot"].ask_clarifying_questions()

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text=ai_message,
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )
        return
        
    elif user_state[user_id]["step"] == "answer_agent_questions":
        user_state[user_id]["step"] = "start_interagent_discussion"

        user_state[user_id]["bot"].handle_clarifying_response(text)
        #print(f"User state{user_state[user_id]}")
        user_state[user_id]["bot"].generate_team_member_report(user_state[user_id]["real_name"])

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Thanks for sharing your thoughts! I need to go discuss with other AI agents now!",
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )

        # Wait for all users to complete their responses
        all_ready = all(user_state[user]["step"] == "start_interagent_discussion" for user in user_state)
        if not all_ready:
            return

        # Initialize AI agents for discussion
        agents = []
        for user in user_state:
            try:
                report_files = glob.glob(f"team_member_report_{user_state[user]['real_name']}_*.txt")
                if not report_files:
                    raise FileNotFoundError("No leadership report found")
                
                latest_report = max(report_files)
                with open(latest_report, 'r') as f:
                    initial_context = f.read()
            except Exception as e:
                print(f"Error reading leadership report: {e}")
                return

            agent = AIAgent(
                name=user_state[user]["real_name"],
                initial_context=initial_context
            )
            agents.append(agent)

        # Create discussion channel
        try:
            result = client.conversations_create(
                name="agents_discussion",
                is_private=False
            )

        except SlackApiError as e:
            print("Error creating conversation: {}".format(e))

        # Run the agent discussion and send updates
        for item in start_discussion(
                agents, 
                initial_prompt="The issue we need to resolve is how to handle the problematic intern. Make it a conversation as much as possible. And you can be a bit sarcastic.",
                max_turns=6
            ):

            try:
                if 'response' in item:
                    # Post agent responses to discussion channel
                    response = client.chat_postMessage(
                        channel="agents_discussion", 
                        text=item['response'],
                        username=f"{item['agent_name']} Agent",
                    )
                elif 'summary' in item:
                    # Send discussion summaries to users
                    target_user_id = next(user for user in user_state if user_state[user]["real_name"] == item['agent_name'])
                    response = client.chat_postMessage(
                        channel=user_state[target_user_id]['conversation'],
                        text=item['summary'], 
                        thread_ts=user_state[target_user_id]['thread_ts'], 
                        username=f"{item['agent_name']} Agent",
                    )
                elif 'preparation' in item:
                    # Send preparation plans to users
                    target_user_id = next(user for user in user_state if user_state[user]["real_name"] == item['agent_name'])
                    response = client.chat_postMessage(
                        channel=user_state[target_user_id]['conversation'], 
                        text=item['preparation'],
                        thread_ts=user_state[target_user_id]['thread_ts'],
                        username=f"{item['agent_name']} Agent",
                    )
            except SlackApiError as e:
                print(f"Error posting message: {e.response['error']}")
        
        return
    

# Flask app setup for handling Slack requests
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/", methods=["POST"])
def slack_events():
    """Handle incoming Slack events and URL verification"""
    data = request.json

    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
