from openai import OpenAI
import os
from typing import List, Dict
import time

import dotenv

dotenv.load_dotenv()


class LeadershipDiscussionBot:
    def __init__(self):
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history: List[Dict] = []
        
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

    def collect_initial_situation(self, situation) -> None:
        # print("\n=== Leadership Discussion Assistant ===")
        # print("Please describe the situation and decision you need help with.")
        # print("Include context, key concerns, and any initial thoughts.\n")
        
        # if situation == None:
        #     situation = input("Your situation: ")
        
        self.conversation_history = [
            {"role": "system", "content": "You are a leadership advisor helping executives make important decisions. First understand their situation, then ask one clarifying question if needed, and finally provide a comprehensive report."},
            {"role": "user", "content": situation}
        ]

    def ask_clarifying_questions(self) -> None:
        #print("\n=== Clarifying Questions ===")
        
        # while True:
        # Get AI's next question or response
        ai_message = self.get_ai_response(self.conversation_history)
        self.conversation_history.append({"role": "assistant", "content": ai_message})
        return ai_message
    
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

    def generate_final_report(self) -> None:
        #print("\n=== Generating Final Report ===")
        
        report_prompt = {
            "role": "user",
            "content": "Based on our discussion, please generate a short report that includes: "
                      "1. Situation Overview\n"
                      "2. Potential solutions\n"
                      "Format it professionally for sharing with team members. Only include the report, no headers or footers, and don't style the text."
        }
        
        self.conversation_history.append(report_prompt)
        report = self.get_ai_response(self.conversation_history)
        
        #print("\n=== Final Report ===")
        #print(report)
        
        # Save report to file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"leadership_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        #print(f"\nReport saved to: {filename}")
        return report

    def include_in_meeting(self) -> None:
        #print("\n=== Including in Meeting ===")
        
        self.conversation_history.append(report_prompt)
        report = self.get_ai_response(self.conversation_history)
        
        #print("\n=== Meeting Attendees ===")
        #print(report)
        
        # Save report to file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"meeting_attendees_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        #print(f"\nMeeting attendees saved to: {filename}")

def main():
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    bot = LeadershipDiscussionBot()
    
    # Step 1: Collect initial situation
    bot.collect_initial_situation()
    
    # Step 2: Ask clarifying questions
    bot.ask_clarifying_questions()
    
    # Step 3: Generate final report
    bot.generate_final_report()

if __name__ == "__main__":
    main()
