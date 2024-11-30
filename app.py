import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv

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
def handle_app_mention_events(body, say):
    user_id = body["event"]["user"]
    text = body["event"]["text"].lower().strip()
    channel_id = body["event"]["channel"]

    # Initialize user state if it doesn't exist
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "goals": None, "attendees": None}

    # Retrieve the user's current state
    state = user_state[user_id]

    if state["step"] is None:
        state["step"] = "start_conversation"

        # Create 
        say("Sure thing! I'll schedule a meeting for you. What are the goals for the meeting?")
        return

    # Default response for unhandled cases
    say("I'm not sure what you're asking. Could you clarify?")


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
