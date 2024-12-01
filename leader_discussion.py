from openai import OpenAI
import os
from typing import List, Dict
import time

import dotenv

dotenv.load_dotenv()


class LeadershipDiscussionBot:
    """
    A bot that helps facilitate leadership discussions and decision making.
    
    This bot uses OpenAI's GPT model to understand leadership situations,
    ask clarifying questions, and generate comprehensive reports with 
    recommendations.
    """
    def __init__(self):
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history: List[Dict] = []
        
    def get_ai_response(self, messages: List[Dict]) -> str:
        """
        Get a response from the OpenAI API.
        
        Args:
            messages: List of conversation messages in OpenAI chat format
            
        Returns:
            The AI's response text, or None if there was an error
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return None

    def collect_initial_situation(self, situation) -> None:
        """
        Initialize the conversation with the leadership situation.
        
        Args:
            situation: Description of the leadership situation/decision
        """
        self.conversation_history = [
            {"role": "system", "content": "You are a leadership advisor helping executives make important decisions. First understand their situation, then ask one clarifying question if needed, and finally provide a comprehensive report."},
            {"role": "user", "content": situation}
        ]

    def ask_clarifying_questions(self) -> None:
        """
        Have the AI ask a clarifying question about the situation.
        
        Returns:
            The AI's question as a string
        """
        ai_message = self.get_ai_response(self.conversation_history)
        self.conversation_history.append({"role": "assistant", "content": ai_message})
        return ai_message
    
    def handle_clarifying_response(self, response) -> None:
        """
        Handle the user's response to a clarifying question.
        
        Args:
            response: The user's response text
        """
        self.conversation_history.append({"role": "user", "content": response})

    def generate_final_report(self) -> None:
        """
        Generate a final report summarizing the situation and recommendations.
        
        Returns:
            The generated report text
        """
        report_prompt = {
            "role": "user",
            "content": "Based on our discussion, please generate a really concise report that includes the situation overview in one sentence. \n "
                      "Format it professionally for sharing with team members. Only include the report, no headers or footers, and don't style the text."
        }
        
        self.conversation_history.append(report_prompt)
        report = self.get_ai_response(self.conversation_history)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"leadership_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        return report

    def include_in_meeting(self) -> None:
        """
        Generate a list of recommended meeting attendees based on the discussion.
        Saves the list to a timestamped file.
        """
        self.conversation_history.append(report_prompt)
        report = self.get_ai_response(self.conversation_history)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"meeting_attendees_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
