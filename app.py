import os
from slack_bolt import App
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from leader_discussion import LeadershipDiscussionBot
from team_member_discussion import TeamMemberDiscussionBot
from agents import *
from transcribe_voice_input import process_speech_bytes_to_text
from extract_text_from_pdf import extract_text_from_pdf_url
import re
import glob

# Load environment variables
load_dotenv()

# Initialize the Slack app with the token and signing secret
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)


# In-memory state to track ongoing conversations
user_state = {}

@app.event("message")
def handle_message_events(body, say, client):
    if "subtype" in body["event"] and body["event"]["subtype"] == "bot_message":
        return

    print(body["event"])
    user_id = body["event"]["user"]
    text = body["event"]["text"].lower().strip()
    thread_ts = body["event"].get("thread_ts", body["event"]["ts"])

    # Add audio transcriptions to the text
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

    # Initialize user state if it doesn't exist
    if user_id not in user_state:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] 
        user_state[user_id] = {"step": None, "bot": None, "conversation": None, "real_name": user_name, "thread_ts": None}

    if user_state[user_id]['conversation'] is None:
        # Check if there's already an open conversation with the user
        conversations = client.conversations_list(types="im")["channels"]
        user_conversation = next((conv for conv in conversations if conv["user"] == user_id), None)
        
        if user_conversation:
            user_state[user_id]['conversation'] = user_conversation['id']
        else:
            ch = client.conversations_open(users=[user_id])
            user_state[user_id]['conversation'] = ch['channel']['id']
    
    if user_state[user_id]['thread_ts'] is None:
        user_state[user_id]['thread_ts'] = thread_ts

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
        mentioned_users = re.findall(r"<@([a-zA-Z0-9]+)>", text)
        # Remove the bot's own user ID from the list of mentions
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

        for user in mentioned_users:
            try:
                # DM the first mentioned user (excluding the bot)
                target_user_id = user
                
                # Open a direct message channel
                dm_channel = client.conversations_open(users=[target_user_id])

                if target_user_id not in user_state:
                    user_info = client.users_info(user=target_user_id)
                    user_name = user_info["user"]["real_name"] 
                    conv = dm_channel['channel']['id']
                    user_state[target_user_id] = {"step": None, "bot": None, "conversation": conv, "real_name": user_name, "thread_ts": None}
                user_state[target_user_id]["step"] = "initialize_discussion"
                
                # Send a DM
                if target_user_id == user_id:
                    client.chat_postMessage(
                        channel=user_state[user_id]['conversation'],
                        text=f"Hello! New meeting scheduled, your thoughts are needed! {report} What are your thoughts?",
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

        #if not mentioned_users:
        #    say("Sorry, I couldn't find any users to share the report with.")
        #else:
        #    client.chat_postMessage(
        #        channel=user_state[user_id]['conversation'],
        #        text="Thanks report saved and shared with the team.",
        #        thread_ts=user_state[user_id]['thread_ts'],
        #        username=f"{user_state[user_id]["real_name"]} Agent",
        #        icon_emoji=":robot_face:"
        #   )

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
        print(f"User state{user_state[user_id]}")
        user_state[user_id]["bot"].generate_team_member_report(user_state[user_id]["real_name"])

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Thanks for sharing your thoughts! I need to go discuss with other AI agents now!",
            thread_ts=user_state[user_id]['thread_ts'],
            username=f"{user_state[user_id]["real_name"]} Agent",
            icon_emoji=":robot_face:"
        )

        # Check if all mentioned users are in the "start_interagent_discussion" state
        all_ready = all(user_state[user]["step"] == "start_interagent_discussion" for user in user_state)
        if not all_ready:
            return

        # Start the inter-agent discussion
        agents = []
        for user in user_state:
            # Find the latest file for the user
            try:
                # Get the most recent leadership report file
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

        # create a new discussion with the bot itself
        try:
            result = client.conversations_create(
                # The name of the conversation
                name="agents_discussion",
                is_private=False
            )

        except SlackApiError as e:
            print("Error creating conversation: {}".format(e))

        for item in start_discussion(
                agents, 
                initial_prompt="The issue we need to resolve is how to handle the problematic intern. Make it a conversation as much as possible. And you can be a bit sarcastic.",
                max_turns=6
            ):

            try:
                if 'response' in item:
                    # Post a message to a channel
                    response = client.chat_postMessage(
                        channel="agents_discussion", 
                        text=item['response'],
                        username=f"{item['agent_name']} Agent",
                    )
                elif 'summary' in item:
                    # Send summaries to the corresponding user in DM
                    target_user_id = next(user for user in user_state if user_state[user]["real_name"] == item['agent_name'])
                    # The conversation ID and thread_ts are stored in user_state when the original conversation starts
                    # See line 71 where conversation is stored and line 83 where thread_ts is first used
                    response = client.chat_postMessage(
                        channel=user_state[target_user_id]['conversation'],
                        text=item['summary'], 
                        thread_ts=user_state[target_user_id]['thread_ts'], 
                        username=f"{item['agent_name']} Agent",
                    )
                elif 'preparation' in item:
                    # Send preparation plans to the corresponding user in DM
                    target_user_id = next(user for user in user_state if user_state[user]["real_name"] == item['agent_name'])
                    #dm_channel = client.conversations_open(users=[target_user_id])
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
    # Parse the request payload
    data = request.json

    # Handle the Slack URL verification challenge
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Pass the request to Bolt handler for event processing
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
