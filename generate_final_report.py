from openai import OpenAI
import os
import glob
from typing import List, Dict
import json

import dotenv

dotenv.load_dotenv()

class FinalAnalysisBot:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.ai_summary: str = ""
        self.leadership_report: str = ""
        self.team_member_reports: Dict[str, str] = {}
        self.final_analysis: Dict = {}

    def load_all_documents(self) -> None:
        """Load all relevant documents."""
        # Load AI agents summary
        try:
            with open("summary_of_ai.txt", 'r') as f:
                self.ai_summary = f.read()
        except Exception as e:
            print(f"Error loading AI summary: {e}")
            return

        # Load leadership report
        try:
            report_files = glob.glob("leadership_report_*.txt")
            if report_files:
                with open(max(report_files), 'r') as f:
                    self.leadership_report = f.read()
        except Exception as e:
            print(f"Error loading leadership report: {e}")

        # Load team member reports
        try:
            member_files = glob.glob("team_member_report_*.txt")
            for file in member_files:
                with open(file, 'r') as f:
                    member_name = file.split('_')[3]  # Extract name from filename
                    self.team_member_reports[member_name] = f.read()
        except Exception as e:
            print(f"Error loading team member reports: {e}")

    def generate_analysis(self) -> None:
        """Generate comprehensive analysis using OpenAI."""
        prompt = f"""
        Analyze the following information and create a comprehensive report:

        AI Agents Discussion:
        {self.ai_summary}

        Leadership Report:
        {self.leadership_report}

        Team Member Reports:
        {json.dumps(self.team_member_reports, indent=2)}

        Please provide:
        1. Top 3 arguments FOR returning to office
        2. Top 3 arguments AGAINST returning to office
        3. Main misunderstandings identified in the discussions
        4. Key clarifications needed
        5. Personalized feedback for CEO, CTO, and CFO regarding their communication and understanding gaps

        Format the response as JSON with the following structure:
        {{
            "common_analysis": {{
                "arguments_for": [],
                "arguments_against": [],
                "misunderstandings": [],
                "clarifications": []
            }},
            "personalized_feedback": {{
                "CEO": "",
                "CTO": "",
                "CFO": ""
            }}
        }}
        Remove ```json and similar from the response.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert analyst synthesizing multiple perspectives on workplace policy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            print(response.choices[0].message.content)
            self.final_analysis = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return None

    def save_reports(self) -> None:
        """Generate and save individual reports for each stakeholder."""
        for role in ["CEO", "CTO", "CFO"]:
            report = self.generate_individual_report(role)
            filename = f"final_report_{role}.txt"
            
            with open(filename, 'w') as f:
                f.write(report)
            print(f"Saved report for {role} to {filename}")

    def generate_individual_report(self, role: str) -> str:
        """Generate a personalized report for each stakeholder."""
        common = self.final_analysis["common_analysis"]
        personal = self.final_analysis["personalized_feedback"][role]
        
        report = f"""
=== Final Analysis Report for {role} ===

COMMON FINDINGS:

Arguments FOR Returning to Office:
{chr(10).join('- ' + arg for arg in common['arguments_for'])}

Arguments AGAINST Returning to Office:
{chr(10).join('- ' + arg for arg in common['arguments_against'])}

Key Misunderstandings Identified:
{chr(10).join('- ' + m for m in common['misunderstandings'])}

Necessary Clarifications:
{chr(10).join('- ' + c for c in common['clarifications'])}

PERSONALIZED FEEDBACK:
{personal}

This report was generated based on all team discussions and AI analysis.
Please review these points before the next meeting.
"""
        return report

def main():
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    bot = FinalAnalysisBot()
    
    # Load all documents
    print("Loading all documents...")
    bot.load_all_documents()
    
    # Generate analysis
    print("Generating comprehensive analysis...")
    bot.generate_analysis()
    
    # Save individual reports
    print("Generating and saving individual reports...")
    bot.save_reports()
    
    print("\nAll reports have been generated and saved.")

if __name__ == "__main__":
    main()
