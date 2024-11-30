from openai import OpenAI
import os
from typing import List, Dict
import glob
import time

import dotenv

dotenv.load_dotenv()

class TeamMemberDiscussionBot:
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
        print("\n=== Team Member Discussion ===")
        # self.team_member_name = input("Please enter your name: ")
        
        # Read the leadership report
        self.leadership_report = self.get_latest_leadership_report()
        if not self.leadership_report:
            print("Error: Cannot proceed without leadership report")
            return

        print("\n=== Leadership Report ===")
        print(self.leadership_report)
        
        # Initialize conversation history
        self.conversation_history = [
            {"role": "system", "content": f"""You are facilitating a discussion with team member {self.team_member_name} 
             about the situation described in this leadership report: {self.leadership_report}
             Your goal is to understand their perspective deeply and create a comprehensive summary of their views."""},
        ]

    def collect_initial_opinion(self, opinion) -> None:
        # print("\n=== Your Opinion ===")
        # print("Please share your thoughts and opinions about this situation.")
        # print("Feel free to express any concerns, ideas, or suggestions you have.\n")
        
        # opinion = input("Your thoughts: ") + "\n\nPlease provide one clarifying question to understand better my true priotities and preferences."
        self.conversation_history.append({"role": "user", "content": opinion + "\n\nPlease provide one clarifying question to understand better my true priotities and preferences."})

    def ask_clarifying_questions(self) -> None:
        print("\n=== Clarifying Discussion ===")
        
        # while True:
        # Get AI's next question or response
        ai_message = self.get_ai_response(self.conversation_history)
        
        # if "UNDERSTANDING_COMPLETE" in ai_message:
        #     # AI indicates it has enough information
        #     self.conversation_history.append({"role": "assistant", "content": ai_message})
        #     break
            
        # print(f"\nAI: {ai_message}")
        
        # # Get user's response
        # user_response = input("\nYour response (or type 'finish' to complete): ")
        
        # if user_response.lower() == 'finish':
        #     break
            
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": ai_message})
        return ai_message
        # self.conversation_history.append({"role": "user", "content": user_response})

    def handle_clarifying_response(self, response) -> None:
        self.conversation_history.append({"role": "user", "content": response})
        
        # if "FINAL_REPORT" in ai_message:
        #     # AI indicates it has enough information
        #     self.conversation_history.append({"role": "assistant", "content": ai_message})
        #     break
            
        # print(f"\nAI: {ai_message}")
        
        # # Get user's response
        # user_response = input("\nYour response (or type 'generate report' to finish): ")
        
        # if user_response.lower() == 'generate report':
        #     break
            
        # # Add to conversation history
        # self.conversation_history.append({"role": "assistant", "content": ai_message})
        # self.conversation_history.append({"role": "user", "content": user_response})

    def generate_team_member_report(self) -> None:
        print("\n=== Generating Team Member Report ===")
        
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
        filename = f"team_member_report_{self.team_member_name}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(self.team_member_report)
        
        print("\n=== Team Member Report ===")
        print(self.team_member_report)
        print(f"\nReport saved to: {filename}")

        # Save conversation context for future AI agent interactions
        context_filename = f"team_member_context_{self.team_member_name}_{timestamp}.txt"
        with open(context_filename, 'w') as f:
            f.write(str(self.conversation_history))

def main():
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    bot = TeamMemberDiscussionBot()
    
    # Step 1: Initialize discussion and show leadership report
    bot.initialize_discussion()
    
    # Step 2: Collect initial opinion
    bot.collect_initial_opinion()
    
    # Step 3: Ask clarifying questions
    bot.ask_clarifying_questions()
    
    # Step 4: Generate and save team member report
    bot.generate_team_member_report()

if __name__ == "__main__":
    main()
