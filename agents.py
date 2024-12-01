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
        # Combine conversation history with the agent's context
        messages = [
            {"role": "system", "content": f"You are {self.name} personal AI Agent. You should act exactly like the team member described here : {self.context}. " 
             "And fight for his opinions against the other ones. Provide a concise, complete thought in one sentence. Do not continue a previous sentence. "
             "Write like people speak in a meeting but in an informal way, you can joke and be sarcastic."
             "Also, don't hesitate to ask relevant questions to other agents instead of giving a thought. If you receive a question which you can't answer, just say that you will find out."
             "As the disscussion progresses, you need to come up together with a set of solutions."},
        ] + [
            {"role": "user" if msg['sender'] != self.name else "assistant", 
             "content": msg['content']} 
            for msg in self.conversation_history
        ] + [
            {"role": "user", "content": f"Previous context: {previous_message}. " 
             "Provide your perspective or question in a single sentence."}
        ]

        # Generate response using OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=100,  # Increased to allow for a full sentence
                temperature=0.7
            )
            
            # Extract and return the response
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
    # Start with the initial prompt
    current_message = initial_prompt
    current_speaker_index = 0

    # Run the discussion for the specified number of turns
    for turn in range(max_turns):
        # Current speaking agent
        current_agent = agents[current_speaker_index]
        
        # Generate response
        if turn == max_turns - 1:
            specific_prompt = "Now, based on the discussion, propose your unique solution that relates to your initial opinions to handle the problematic intern. You can decide to disagree with the other agents."
            current_message += f" {specific_prompt}"
        response = current_agent.generate_response(current_message)
        
        # Prepare response dictionary
        response_dict = {
            'turn': turn,
            'agent_name': current_agent.name,
            'response': response
        }
        
        # Yield the response for immediate access
        yield response_dict

        # Add response to all agents' conversation histories
        for agent in agents:
            agent.add_to_history(current_agent.name, response)

        # Update current message and speaker
        current_message = response
        current_speaker_index = (current_speaker_index + 1) % len(agents)

    # After the discussion, prompt the first agent for a summary of the discussion
    summary_prompt = (
        "Provide a concise summary of the entire discussion in one sentence. "
        "This should capture the key points made by each participant and any conclusions reached."
    )
    shared_summary = agents[0].generate_response(summary_prompt)

    # Yield the shared summary for all agents
    for agent in agents:
        yield {
            'agent_name': agent.name,
            'summary': shared_summary
        }

    # Ask each agent for their individual preparation plan
    for agent in agents:
        preparation_prompt = (
            "Based on the discussion with the other AI agents, what should you tell your owner to prepare for the real meeting."
            "Focus on your role and what is expected from you."
            "Adress yourself directly to your owner as you."
        )
        preparation = agent.generate_response(preparation_prompt)
        yield {
            'agent_name': agent.name,
            'preparation': preparation
        }