from openai import OpenAI
import os
from typing import List, Dict
import dotenv

# Load environment variables
dotenv.load_dotenv()

class AIAgent:
    def __init__(self, name: str, role: str, initial_context: str):
        """
        Initialize an AI agent with a name, role, and initial context.
        
        :param name: Name of the agent
        :param role: Specific role or perspective of the agent
        :param initial_context: Initial context or background for the agent
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.name = name
        self.role = role
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
            {"role": "system", "content": f"You are {self.name}, {self.role}. {self.context}. " 
             "Provide a concise, complete thought in one sentence. Do not continue a previous sentence. "
             "Ensure your response is a full, grammatically complete sentence."},
        ] + [
            {"role": "user" if msg['sender'] != self.name else "assistant", 
             "content": msg['content']} 
            for msg in self.conversation_history
        ] + [
            {"role": "user", "content": f"Previous context: {previous_message}. " 
             "Provide your perspective in a single, complete sentence."}
        ]

        # Generate response using OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=50,  # Increased to allow for a full sentence
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

def start_discussion(agents: List[AIAgent], initial_prompt: str, max_turns: int = 5) -> None:
    """
    Facilitate a discussion between multiple AI agents.
    
    :param agents: List of AI agents participating in the discussion
    :param initial_prompt: Starting topic or question
    :param max_turns: Maximum number of conversation turns
    """
    # Start with the initial prompt
    current_message = initial_prompt
    current_speaker_index = 0

    print(f"Discussion Topic: {initial_prompt}\n")

    # Run the discussion for specified number of turns
    for turn in range(max_turns):
        # Current speaking agent
        current_agent = agents[current_speaker_index]
        
        # Generate response
        response = current_agent.generate_response(current_message)
        
        # Print the response
        print(f"{current_agent.name} ({current_agent.role}):")
        print(response + "\n")

        # Add response to all agents' conversation histories
        for agent in agents:
            agent.add_to_history(current_agent.name, response)

        # Update current message and speaker
        current_message = response
        current_speaker_index = (current_speaker_index + 1) % len(agents)

def main():
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    # Create AI agents with different roles and contexts (same as before)
    agents = [
        AIAgent(
            name="CEO",
            role="Moderate the debate",
            initial_context="We need to decide whether to bring everyone back into the office and eliminate remote work. \
                The key concerns are productivity, company culture, and the long-term impact on our talent retention. \
                The decision must balance the need for stronger collaboration with the operational costs. \
                I'm particularly concerned about the future of our company culture and employee satisfaction, so I'm leaning towards a model that includes flexibility."
        ),
        AIAgent(
            name="CFO",
            role="Favorable to in-office work",
            initial_context= "I am concerned about the financial impact of remote work, and I believe we should bring everyone back to the office. \
                My arguments against remote work are: Cost savings on office space will be lost if we continue remote work—there are significant expenses tied to maintaining home-office stipends and remote work infrastructure. \
                Lower operational efficiency: With fewer people in the office, we've seen a decline in spontaneous collaboration and productivity, which could negatively impact overall performance. \
                Long-term financial sustainability: Maintaining a remote workforce may limit opportunities for growth and expansion that a full in-office team could provide, such as easier communication and stronger teamwork. \
                From a financial perspective, the return on investment in remote work is diminishing, and we need to consider the overall cost to the company's long-term success."
        ),
        AIAgent(
            name="CTO",
            role="Favorable to remote work",
            initial_context="I think the technology infrastructure supports remote work well. Our teams have been effective remotely, and we've maintained productivity with the right tools in place. However, I do believe that in-person meetings for brainstorming and innovation could be beneficial. My arguments for remote work are: \
                No need for additional office space or equipment. We've seen increased focus and efficiency in remote work. \
                Remote work allows us to attract a broader range of tech talent, including people outside of our geographical location. \
                My concern is that we may lose some innovation and creativity that benefits from face-to-face collaboration."
        )
    ]

    # Start the discussion
    start_discussion(
        agents, 
        initial_prompt="The issue we need to resolve is whether to bring everyone back to the office and end remote work.",
        max_turns=6
    )

if __name__ == "__main__":
    main()