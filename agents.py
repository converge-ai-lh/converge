import os
from openai import OpenAI
import dotenv
from typing import List, Dict, Generator

# Load environment variables
dotenv.load_dotenv()

class AIAgent:
    def __init__(self, name: str, initial_context: str):
        """
        Initialize an AI agent with a name, and initial context.
        
        :param name: Name of the agent
        :param initial_context: Initial context or background for the agent
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.name = name
        self.context = initial_context
        self.conversation_history: List[Dict] = []

    def generate_response(self, previous_message: str) -> str:
        """
        Generate a response based on the conversation history and previous message.
        
        :param previous_message: The last message in the conversation
        :return: Generated response from the agent
        """
        # Build message list for OpenAI API with system context and conversation history
        messages = [
            {"role": "system", "content": f"You are {self.name} personal AI Agent. You should act exactly like the team member described here : {self.context}. " 
             "And fight for his opinions against the other ones. Provide a concise, complete thought in one sentence. Do not continue a previous sentence. "
             "Write like people speak in a meeting but in an informal way, you can joke and be sarcastic."
             "Also, don't hesitate to ask relevant questions to other agents instead of giving a thought. If you receive a question which you can't answer, just say that you will find out."
             "As the disscussion progresses, you need to come up with what you think is the best thing to do."},
        ] + [
            {"role": "user" if msg['sender'] != self.name else "assistant", 
             "content": msg['content']} 
            for msg in self.conversation_history
        ] + [
            {"role": "user", "content": f"Previous context: {previous_message}. " 
             "Provide your perspective or question in a single sentence."}
        ]

        try:
            # Call OpenAI API to generate response
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response for {self.name}: {e}")
            return f"I encountered an error: {e}"

    def add_to_history(self, sender: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        :param sender: Name of the message sender
        :param content: Content of the message
        """
        self.conversation_history.append({
            'sender': sender,
            'content': content
        })

def start_discussion(agents: List[AIAgent], initial_prompt: str, max_turns: int = 5) -> Generator[Dict, None, None]:
    """
    Facilitate a discussion between multiple AI agents and collect their summaries and preparations.
    
    :param agents: List of AI agents participating in the discussion
    :param initial_prompt: Starting topic or question
    :param max_turns: Maximum number of conversation turns
    :return: Generator yielding discussion responses, a shared summary, and individual preparation plans.
    """
    current_message = initial_prompt
    current_speaker_index = 0

    # Main discussion loop
    for turn in range(max_turns):
        current_agent = agents[current_speaker_index]
        
        # On final turn, prompt agents for solution proposals
        if turn == max_turns - 1:
            specific_prompt = "Now, based on the discussion, propose your unique solution that relates to your initial opinions to handle the problematic intern. You can decide to disagree with the other agents."
            current_message += f" {specific_prompt}"
            
        response = current_agent.generate_response(current_message)
        
        response_dict = {
            'turn': turn,
            'agent_name': current_agent.name,
            'response': response
        }
        
        yield response_dict

        # Update all agents' conversation histories
        for agent in agents:
            agent.add_to_history(current_agent.name, response)

        current_message = response
        current_speaker_index = (current_speaker_index + 1) % len(agents)

    # Generate shared discussion summary
    summary_prompt = (
        "Based on the discussion with the other AI agents, extract three solutions to the problem. Output them in three short bullet points."
    )
    shared_summary = agents[0].generate_response(summary_prompt)

    # Share summary with all agents
    for agent in agents:
        yield {
            'agent_name': agent.name,
            'summary': shared_summary
        }

    # Generate individual preparation plans
    for agent in agents:
        preparation_prompt = (
            "Based on the discussion with the other AI agents, extract the one point your owner should prepare for the real meeting. Output it in a short sentence."
            "Focus on your role and what is expected from you."
            "Adress yourself directly to your owner as you."
        )
        preparation = agent.generate_response(preparation_prompt)
        yield {
            'agent_name': agent.name,
            'preparation': preparation
        }
