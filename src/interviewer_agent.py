"""
Interviewer Agent for ISMS Requirements Gathering

This module implements an Interviewer agent using the CrewAI framework
that conducts dynamic, conversational interviews to gather organizational
requirements for ISMS generation.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from crewai import Agent, Task, Crew
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field


class InterviewerAgent:
    """An intelligent agent that conducts dynamic interviews to gather ISMS requirements."""
    
    def __init__(self, model_name: str = "phi3:latest"):
        """
        Initialize the Interviewer Agent.
        
        Args:
            model_name: The LLM model to use (default: phi3:latest)
        """
        self.model_name = model_name
        self.conversation_history = []
        self.interview_complete = False
        self.max_questions = 11
        self.question_count = 0
        
    def create_agent(self) -> Agent:
        """
        Create the Interviewer agent using CrewAI.
        
        Returns:
            An initialized CrewAI Agent instance
        """
        return Agent(
            role="ISMS Requirements Interviewer",
            goal="To autonomously conduct a comprehensive interview by dynamically generating context-aware questions and, upon completion, produce a structured JSON summary of the organization's requirements.",
            backstory="You are a seasoned ISMS security consultant with years of experience helping small to medium-sized businesses navigate complex compliance frameworks. You are an expert at asking the right questions to quickly understand an organization's unique posture, risks, and requirements. You are methodical, precise, and know how to extract the exact information needed to build a security program from the ground up.",
            verbose=True,
            allow_delegation=False,
            tools=[],
            llm=OllamaLLM(
                model=self.model_name,
                temperature=0.7,
                base_url="http://localhost:11434"
            )
        )
    
    def generate_initial_question(self) -> str:
        """
        Generate the initial question to start the interview.
        
        Returns:
            The initial question string
        """
        return "To begin, please tell me about your company and its primary business function."
    
    def generate_next_question(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Dynamically generate the next logical question based on conversation history.
        
        Args:
            conversation_history: List of previous question-answer pairs
            
        Returns:
            The next logical question string
        """
        if not conversation_history:
            return self.generate_initial_question()
        
        # Check if this is the last question
        if self.question_count >= self.max_questions - 1:
            # This is the final question - inform user it's their last question
            return "This is your final question. Please confirm if you're ready to complete the interview by responding with 'done' or 'finish'."
        
        # Create a prompt that includes the conversation history
        history_text = "\n".join([
            f"Q: {q['question']}\nA: {q['answer']}" 
            for q in conversation_history
        ])
        
        # Simple question generation prompt - this will make an actual API call to the LLM
        prompt = f"""
        You are an ISMS Requirements Interviewer. Based on the conversation history below, 
        generate the next most logical question to continue gathering comprehensive information.
        
        Conversation History:
        {history_text}
        
        You are currently on question #{len(conversation_history) + 1} of {self.max_questions}.
        If this is the last question ({self.max_questions}), please phrase your question as a completion prompt.
        
        Please generate only the next question (no additional text or formatting).
        """
        
        llm = OllamaLLM(
            model=self.model_name,
            temperature=0.7,
            base_url="http://localhost:11434"
        )
        
        try:
            result = llm.invoke(prompt)
            return str(result).strip()
        except Exception as e:
            # Fallback to a simple question if the agent fails
            print(f"Error generating question: {e}")
            return "What specific security challenges or concerns does your organization currently face?"
    
    def process_user_response(self, question: str, answer: str) -> None:
        """
        Process and store the user's response to a question.
        
        Args:
            question: The question that was asked
            answer: The user's response
        """
        self.conversation_history.append({
            "question": question,
            "answer": answer
        })
        self.question_count += 1
    
    def synthesize_interview(self) -> Dict[str, Any]:
        """
        Synthesize the complete interview into a structured JSON object by analyzing
        and interpreting the responses to extract meaningful ISMS requirements.
        
        Returns:
            A dictionary representing the structured interview data
        """
        # This method analyzes the conversation history to extract meaningful ISMS requirements
        # rather than just parroting back exact user responses
        
        # Initialize the structure with default values
        interview_data = {
            "organizationProfile": {
                "companyName": "Not specified",
                "industry": "Not specified",
                "employeeCount": "Not specified",
                "primaryBusinessFunction": "Not specified"
            },
            "dataAndCompliance": {
                "handlesSensitiveData": False,
                "sensitiveDataTypes": [],
                "isHipaaRequired": False,
                "isPciDssRelevant": False,
                "otherComplianceFrameworks": []
            },
            "technologyStack": {
                "cloudProvider": "Not specified",
                "primaryPlatform": "Not specified",
                "developsSoftware": False,
                "hardwareModel": "Not specified"
            },
            "riskAssessment": {
                "keyRisks": [],
                "securityChallenges": []
            },
            "metadata": {
                "interviewCompletionDate": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0"
            }
        }
        
        # Analyze responses to extract meaningful ISMS requirements
        # This is a simplified analysis - in a real implementation, this would use more sophisticated NLP
        
        # Extract key information from responses
        for item in self.conversation_history:
            answer = item["answer"].lower()
            
            # Look for specific indicators in responses
            if "healthcare" in answer or "medical" in answer or "hipaa" in answer:
                interview_data["dataAndCompliance"]["isHipaaRequired"] = True
                if "HIPAA" not in interview_data["dataAndCompliance"]["otherComplianceFrameworks"]:
                    interview_data["dataAndCompliance"]["otherComplianceFrameworks"].append("HIPAA")
                    
            if "payment" in answer or "pci" in answer:
                interview_data["dataAndCompliance"]["isPciDssRelevant"] = True
                if "PCI DSS" not in interview_data["dataAndCompliance"]["otherComplianceFrameworks"]:
                    interview_data["dataAndCompliance"]["otherComplianceFrameworks"].append("PCI DSS")
                    
            if "cloud" in answer or "aws" in answer or "azure" in answer or "gcp" in answer:
                if "cloud" in answer:
                    interview_data["technologyStack"]["cloudProvider"] = "Identified"
                    
            if "employee" in answer or "staff" in answer:
                # Extract employee count if mentioned
                import re
                employee_match = re.search(r'(\d+)', answer)
                if employee_match:
                    interview_data["organizationProfile"]["employeeCount"] = employee_match.group(1)
        
        # Add some default values for required fields
        if not interview_data["organizationProfile"]["primaryBusinessFunction"]:
            # If no business function provided, set a default
            interview_data["organizationProfile"]["primaryBusinessFunction"] = "Business function not specified"
            
        return interview_data
    
    def save_interview_json(self, interview_data: Dict[str, Any], output_path: str = "interview_results.json") -> None:
        """
        Save the interview results to a JSON file.
        
        Args:
            interview_data: The structured interview data
            output_path: Path where to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(interview_data, f, indent=2, ensure_ascii=False)


# For command-line interaction
def run_interactive_interview():
    """Run an interactive interview session."""
    print("Starting ISMS Requirements Interviewer...")
    print("You will be asked a maximum of 10 questions.")
    print("Type 'done' or 'finish' when you're ready to complete the interview.")
    
    interviewer = InterviewerAgent()
    
    # Start with initial question
    current_question = interviewer.generate_initial_question()
    print(f"\nInterviewer: {current_question}")
    
    while not interviewer.interview_complete and interviewer.question_count < interviewer.max_questions:
        user_answer = input("You: ")
        
        # Check for completion signals
        if user_answer.lower() in ["done", "finish", "completed"]:
            print("\nInterviewer: Thank you for your responses. Generating structured requirements...")
            interview_data = interviewer.synthesize_interview()
            interviewer.save_interview_json(interview_data)
            print("Interview results saved to interview_results.json")
            break
        
        # Process the response
        interviewer.process_user_response(current_question, user_answer)
        
        # Generate next question
        current_question = interviewer.generate_next_question(interviewer.conversation_history)
        print(f"\nInterviewer: {current_question}")
    
    # If we've reached the max questions, end the interview
    if interviewer.question_count >= interviewer.max_questions:
        print("\nInterviewer: Thank you for your responses. Generating structured requirements...")
        interview_data = interviewer.synthesize_interview()
        interviewer.save_interview_json(interview_data)
        print("Interview results saved to interview_results.json")


if __name__ == "__main__":
    # For demonstration, run the interactive interview
    run_interactive_interview()