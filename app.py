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

# Event: When a user sends a message in a channel
@app.event("message")
def handle_message_events(body, say):
    user = body["event"].get("user")
    text = body["event"].get("text")
    print(body)
    if user:  # Ignore bot messages
        say(f"Hey <@{user}>, you said: {text}")

# Event: When a user reacts with an emoji
@app.event("reaction_added")
def handle_reaction_events(body, say):
    print(body)
    user = body["event"]["user"]
    reaction = body["event"]["reaction"]
    say(f"<@{user}> added a reaction: :{reaction}:")

# In-memory state to track ongoing conversations
user_state = {}

@app.event("app_mention")
def handle_app_mention_events(body, say, client):
    user_id = body["event"]["user"]
    text = body["event"]["text"].lower().strip()
    channel_id = body["event"]["channel"]

    # Initialize user state if it doesn't exist
    if user_id not in user_state:
        user_state[user_id] = {"step": None, "goals": None, "attendees": None}

    # Retrieve the user's current state
    state = user_state[user_id]

    # Step 1: Detect initial meeting setup
    if state["step"] is None and "meeting" in text:
        state["step"] = "collect_goals"
        say("Sure thing! I'll schedule a meeting for you. What are the goals for the meeting?")
        return

    # Step 2: Collect meeting goals
    if state["step"] == "collect_goals":
        if any(keyword in text for keyword in ["goal", "objectives", "target"]):
            state["goals"] = text
            state["step"] = "collect_attendees"
            say("Perfect! Who should be invited to the meeting?")
            return
        else:
            say("I didn't catch the goals. Could you clarify what the meeting is about?")
            return

    # Step 3: Collect attendees
    if state["step"] == "collect_attendees":
        if any(keyword in text for keyword in ["invite", "attendees", "participants"]):
            state["attendees"] = text
            state["step"] = "done"
            say(f"Great! I've set up the meeting with the following:\n- **Goals:** {state['goals']}\n- **Attendees:** {state['attendees']}")

            # TODO
            # Clean state
            user_state[user_id] = {"step": None, "goals": None, "attendees": None}

            return
        else:
            say("Could you specify who should be invited?")
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

    # Handle the Slack URL verification challenge
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Pass the request to Bolt handler for event processing
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
