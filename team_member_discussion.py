from openai import OpenAI
import os
from typing import List, Dict
import glob
import time

import dotenv

dotenv.load_dotenv()

class TeamMemberDiscussionBot:
    """
    A bot that facilitates discussions with team members about leadership decisions.
    
    This bot collects team member perspectives on leadership reports, asks clarifying
    questions to understand their views, and generates comprehensive summaries of 
    their feedback and suggestions.
    """
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history: List[Dict] = []
        self.team_member_name: str = ""
        self.leadership_report: str = ""
        self.team_member_report: str = ""

    def get_latest_leadership_report(self) -> str:
        """Find and read the most recent leadership report."""
        try:
            # Get the most recent leadership report file
            report_files = glob.glob("leadership_report_*.txt")
            if not report_files:
                raise FileNotFoundError("No leadership report found")
            
            latest_report = max(report_files)
            with open(latest_report, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading leadership report: {e}")
            return None

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

    def initialize_discussion(self, user_name) -> None:
        """
        Initialize the discussion with a team member.
        
        Args:
            user_name: Name of the team member
        """
        # Read the leadership report
        self.leadership_report = self.get_latest_leadership_report()
        if not self.leadership_report:
            print("Error: Cannot proceed without leadership report")
            return
        
        # Initialize conversation history
        self.conversation_history = [
            {"role": "system", "content": f"""You are facilitating a discussion with team member {self.team_member_name} 
             about the situation described in this leadership report: {self.leadership_report}
             Your goal is to understand their perspective deeply and create a comprehensive summary of their views."""},
        ]

    def collect_initial_opinion(self, opinion) -> None:
        """
        Collect the team member's initial opinion on the situation.
        
        Args:
            opinion: The team member's initial thoughts and feedback
        """
        self.conversation_history.append({"role": "user", "content": opinion + "\n\nPlease provide one clarifying question to understand better my true priotities and preferences."})

    def ask_clarifying_questions(self) -> None:
        """
        Have the AI ask a clarifying question about the team member's perspective.
        
        Returns:
            The AI's question as a string
        """
        ai_message = self.get_ai_response(self.conversation_history)
        self.conversation_history.append({"role": "assistant", "content": ai_message})
        return ai_message

    def handle_clarifying_response(self, response) -> None:
        """
        Handle the team member's response to a clarifying question.
        
        Args:
            response: The team member's response text
        """
        self.conversation_history.append({"role": "user", "content": response})

    def generate_team_member_report(self, name) -> None:
        """
        Generate a report summarizing the team member's perspective.
        
        Args:
            name: Name of the team member for the report filename
        """
        report_prompt = {
            "role": "user",
            "content": "Based on our discussion, please generate a comprehensive summary of the team member's perspective that includes: "
                      "1. Key Points and Opinions\n"
                      "2. Main Concerns\n"
                      "3. Suggested Solutions\n"
                      "4. Additional Insights\n"
                      "Format it professionally for integration with other team members' feedback."
        }
        
        self.conversation_history.append(report_prompt)
        self.team_member_report = self.get_ai_response(self.conversation_history)
        
        # Save individual team member report
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"team_member_report_{name}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(self.team_member_report)

        # Save conversation context for future AI agent interactions
        context_filename = f"team_member_context_{self.team_member_name}_{timestamp}.txt"
        with open(context_filename, 'w') as f:
            f.write(str(self.conversation_history))
