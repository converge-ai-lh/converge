import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from leader_discussion import LeadershipDiscussionBot
from team_member_discussion import TeamMemberDiscussionBot
from transcribe_voice_input import process_speech_bytes_to_text
import re

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
                    url='https://files.slack.com/files-tmb/T08336M9URG-F0830VB3YJZ-a444ce43c3/download/audio_message_audio.mp4', # file['url_private_download'],
                    headers=headers
                )
                text += f'{transcript} '

    # Initialize user state if it doesn't exist
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "bot": None, "conversation": None}

    if user_state[user_id]['conversation'] is None:
        # Check if there's already an open conversation with the user
        conversations = client.conversations_list(types="im")["channels"]
        user_conversation = next((conv for conv in conversations if conv["user"] == user_id), None)
        
        if user_conversation:
            user_state[user_id]['conversation'] = user_conversation['id']
        else:
            ch = client.conversations_open(users=[user_id])
            user_state[user_id]['conversation'] = ch['channel']['id']

    if user_state[user_id]["step"] is None:
        user_state[user_id]["step"] = "start_conversation"

        user_state[user_id]["bot"] = LeadershipDiscussionBot()
        
        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Please describe the situation and decision you need help with. Include context, key concerns, and any initial thoughts.",
            thread_ts=thread_ts,
            username="CEO Bot",
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
            thread_ts=thread_ts,
            username="CEO Bot",
            icon_emoji=":robot_face:"
        )

        return

    elif user_state[user_id]["step"] == "ask_clarifying_questions":
        user_state[user_id]["step"] = "generate_final_report"

        user_state[user_id]["bot"].handle_clarifying_response(text)

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Who do you want to include in the meting?",
            thread_ts=thread_ts,
            username="CEO Bot",
            icon_emoji=":robot_face:"
        )
        return

    elif user_state[user_id]["step"] == "generate_final_report":
        mentioned_users = re.findall(r"<@([a-zA-Z0-9]+)>", text)
        # Remove the bot's own user ID from the list of mentions
        bot_user_id = client.auth_test()['user_id']
        mentioned_users = [user.strip().upper() for user in mentioned_users if user != bot_user_id] + [user_id]

        report = user_state[user_id]["bot"].generate_final_report()

        say("Thanks, the report was saved and shared with the team.")

        for user in mentioned_users:
            try:
                # DM the first mentioned user (excluding the bot)
                target_user_id = user

                print(f"Sending DM to {target_user_id}")
                
                # Open a direct message channel
                dm_channel = client.conversations_open(users=[target_user_id])

                print("DEBUG 1")
                
                # Send a DM
                client.chat_postMessage(
                    channel=dm_channel['channel']['id'],
                    text=f"Hello! New meeting scheduled, your thoughts are needed! {report} What are your thoughts?",
                    username="CEO Bot",
                    icon_emoji=":robot_face:"
                )

                print("DEBUG 2")

                if target_user_id not in user_state:
                    user_state[target_user_id] = {"step": None, "bot": None, "conversation": None}
                user_state[target_user_id]["step"] = "initialize_discussion"

                print("DEBUG 3")
                
                # say(f"I've sent a DM to <@{target_user_id}>")
            except Exception as e:
                print
                print(f"Error sending DM: {e}")

        if not mentioned_users:
            say("Sorry, I couldn't find any users to share the report with.")
        else:
            say("Thanks, the report was saved and shared with the team.")

        return
    elif user_state[user_id]["step"] == "initialize_discussion":
        user_state[user_id]["step"] = "answer_agent_questions"

        user_name = "CEO"

        user_state[user_id]["bot"] = TeamMemberDiscussionBot()
        user_state[user_id]["bot"].initialize_discussion(user_name)
        user_state[user_id]["bot"].collect_initial_opinion(text)

        ai_message = user_state[user_id]["bot"].ask_clarifying_questions()

        # say(ai_message)

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text=ai_message,
            thread_ts=thread_ts,
            username="CEO Bot",
            icon_emoji=":robot_face:"
        )
        return
    elif user_state[user_id]["step"] == "answer_agent_questions":
        user_state[user_id]["step"] = "generate_final_report"

        user_state[user_id]["bot"].handle_clarifying_response(text)

        user_state[user_id]["bot"].generate_team_member_report()

        client.chat_postMessage(
            channel=user_state[user_id]['conversation'],
            text="Thanks for sharing your thoughts! I need to go discuss with other AI agents now!",
            thread_ts=thread_ts,
            username="CEO Bot",
            icon_emoji=":robot_face:"
        )

        return

# Flask app setup for handling Slack requests
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/", methods=["POST"])
def slack_events():
    # Parse the request payload
    data = request.json
    #print(data)

    # Handle the Slack URL verification challenge
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Pass the request to Bolt handler for event processing
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
