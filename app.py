import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from leader_discussion import LeadershipDiscussionBot
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

@app.event("app_mention")
def handle_app_mention_events(body, say, client):
    print("RECEIVEED MESSAGE")
    user_id = body["event"]["user"]
    text = body["event"]["text"].lower().strip()
    channel_id = body["event"]["channel"]

    # Initialize user state if it doesn't exist
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "bot": None}

    # Retrieve the user's current state
    # state = user_state[user_id]

    # print("DEBUGGGGG" + text)

    print("STATE: " + str(user_state[user_id]))

    if user_state[user_id]["step"] is None:
        user_state[user_id]["step"] = "start_conversation"

        user_state[user_id]["bot"] = LeadershipDiscussionBot()
        
        say("Please describe the situation and decision you need help with. Include context, key concerns, and any initial thoughts.")

        # Create 
        # say("Sure thing! I'll schedule a meeting for you. What are the goals for the meeting?")
        return
    elif user_state[user_id]["step"] == "start_conversation":
        user_state[user_id]["step"] = "ask_clarifying_questions"

        user_state[user_id]["bot"].collect_initial_situation(text)

        ai_message = user_state[user_id]["bot"].ask_clarifying_questions()

        say(ai_message)

        return

    elif user_state[user_id]["step"] == "ask_clarifying_questions":
        user_state[user_id]["step"] = "generate_final_report"

        user_state[user_id]["bot"].handle_clarifying_response(text)

        say("Who do you want to include in the meting?", username="CEO Bot")
        return

    elif user_state[user_id]["step"] == "generate_final_report":
        # user_state[user_id]["step"] = None

        mentioned_users = re.findall(r"<@([a-zA-Z0-9]+)>", text)
        print(mentioned_users)
        print(text)
        # Remove the bot's own user ID from the list of mentions
        bot_user_id = client.auth_test()['user_id']
        mentioned_users = [user.strip().upper() for user in mentioned_users if user != bot_user_id] + [user_id]

        print(mentioned_users)

        report = user_state[user_id]["bot"].generate_final_report()

        for user in mentioned_users:
            try:
                # DM the first mentioned user (excluding the bot)
                target_user_id = user
                
                # Open a direct message channel
                dm_channel = client.conversations_open(users=[target_user_id])
                
                # Send a DM
                client.chat_postMessage(
                    channel=dm_channel['channel']['id'],
                    text=f"Hello! New meeting scheduled, your thoughts are needed! {report} What are your thoughts?",
                    username="CEO Bot",
                    icon_emoji=":robot_face:"
                )
                
                # Optional: Respond in the original channel
                say(f"I've sent a DM to <@{target_user_id}>")
            except Exception as e:
                print(f"Error sending DM: {e}")
                # say("Sorry, I couldn't send the DM.")

        if not mentioned_users:
            say("Sorry, I couldn't find any users to share the report with.")
        else:
            say("Thanks, the report was saved and shared with the team.")

        return

    # # Default response for unhandled cases
    # say("I'm not sure what you're asking. Could you clarify?")


# Flask app setup for handling Slack requests
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/", methods=["POST"])
def slack_events():
    # Parse the request payload
    data = request.json
    print(data)

    # Handle the Slack URL verification challenge
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Pass the request to Bolt handler for event processing
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
