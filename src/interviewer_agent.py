"""
Interviewer Agent for ISMS Requirements Gathering

This module implements an Interviewer agent using the CrewAI framework
that conducts dynamic, conversational interviews to gather organizational
requirements for ISMS generation.
"""

import json, os, re, contextlib, io, pdb
from datetime import datetime
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel, Field


class InterviewerAgent:
  """An intelligent agent that conducts dynamic interviews to gather ISMS requirements."""
  
  def __init__(self, model_name: str = "ollama/dolphin3:latest"):
    """
    Initialize the Interviewer Agent.
    
    Args:
      model_name: The LLM model to use (default: phi3:latest)
    """
    self.model_name = model_name
    self.conversation_history = []
    self.interview_complete = False
    self.max_questions = 12
    self.question_count = 0
    self.agent = self.create_agent()
    
  def create_agent(self) -> Agent:
    """
    Create the Interviewer agent using CrewAI.
    
    Returns:
      An initialized CrewAI Agent instance
    """
    return Agent(
      role="ISMS Requirements Interviewer",
      goal="To efficiently determine the minimum number of questions required to gather sufficient requirements about an organization's information security program needs. The final, structured JSON output must provide an information security architect and a policy writer with enough context to create a comprehensive first draft of a tailored policy and procedure set for the organization.",
      backstory="You are a seasoned information security consultant with years of experience helping small to medium-sized businesses navigate complex compliance frameworks. You are an expert at asking the right questions to quickly understand an organization's unique posture, risks, and requirements. You are methodical, precise, and know how to extract the exact information needed to build a security program from the ground up.",
      verbose=False,
      allow_delegation=False,
      tools=[],
      reasoning=True,
      memory=True,
      llm=LLM(
        model=self.model_name,
        temperature=0.7,
        base_url="http://localhost:11434",
        verbose=False
      )
    )
  
  def generate_initial_question(self) -> str:
    return "To begin, please tell me about your company and its primary business function."

  def read_generate_question_prompt(self) ->  str:
    return self.read_instructions("docs/interviewer/generate_question.md")

  def read_synthesize_instructions(self) -> str:
    return self.read_instructions("docs/interviewer/synthesize_conversation.md")

  def read_instructions(self, path) -> str:
    try:
      with open(path, "r") as f:
        return f.read()
    except FileNotFoundError:
      # Fallback to a basic prompt if file not found
      print(f"Warning: {path} not found, using fallback prompt")
      raise SystemExit(1)

  def quiet_task(self, prompt) -> str:
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
      return self.remove_think_block(self.agent.kickoff(prompt).raw)

  def generate_next_question_batch(self, conversation_history: List[Dict[str, str]]) -> List:
    """
    Dynamically generate the next logical question based on conversation history.
    
    Args:
      conversation_history: List of previous question-answer pairs
      
    Returns:
      The next logical question string
    """
    if not conversation_history:
      return self.generate_initial_question()
    
    past_questions = "\n".join(f"- {q['question']}" for q in conversation_history)

    prompt_template = self.read_generate_question_prompt()
    
    prompt = prompt_template.replace("{business_description}", conversation_history[0]["answer"])
    prompt = prompt.replace("{max_questions}", str(self.max_questions))
    prompt = prompt.replace("{question_history}", past_questions)
    
    try:
      result = self.strip_markdown(self.quiet_task(prompt))
      return [item["question_text"] for item in result["questions"]]
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
    prompt = self.read_synthesize_instructions()
    history = "\n\n".join(
      f"Q: {item['question']}\nA: {item['answer']}"
      for item in self.conversation_history if "question" in item and "answer" in item
    )
    prompt = prompt.replace("{question_history}", history)
    
    try:
      result = self.quiet_task(prompt)
      pdb.set_trace()
      return self.strip_markdown(result)
    except Exception as e:
      # If there's an error with the LLM or processing, log the error and exit
      print(f"Error generating structured JSON: {e}")
      raise SystemExit(1)
  
  def strip_markdown(self, result) -> str:
      # Handle markdown-wrapped JSON if present
      if result.strip().startswith("```json"):
        # Extract JSON from markdown code block
        json_start = result.find("{")
        json_end = result.rfind("}") + 1
        if json_start != -1 and json_end != -1:
          json_str = result[json_start:json_end]
        else:
          # If we can't find proper JSON bounds, use the whole result
          json_str = result.strip()
      else:
        json_str = result.strip()
      
      # Validate that it's valid JSON
      try:
        # Try to parse the result as JSON
        return json.loads(json_str)
      except json.JSONDecodeError as e:
        # If it's not valid JSON, log the error and exit
        print(f"Error: Generated content is not valid JSON. Details: {e}")
        print(f"Generated content: {json_str}")
        raise SystemExit(1)

  def save_interview_json(self, interview_data: Dict[str, Any], output_path: str = "interview_results.json") -> None:
    """
    Save the interview results to a JSON file.
    
    Args:
      interview_data: The structured interview data
      output_path: Path where to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(interview_data, f, indent=2, ensure_ascii=False)

  def remove_think_block(self, text: str) -> str:
    return re.sub(r"<think>.*?</think>\n?", "", text, flags=re.DOTALL)

  # For command-line interaction
  def run_interactive_interview(self):
    """Run an interactive interview session."""
    print("Starting ISMS Requirements Interviewer...")
    print("Type 'done' or 'finish' when you're ready to complete the interview.")

    # Start with initial question
    current_question = self.generate_initial_question()
    print(f"\nInterviewer: {current_question}")
    user_answer = input("You: ")
    self.process_user_response(current_question, user_answer)
    
    while not self.interview_complete and self.question_count < self.max_questions:
      # Generate next question
      next_questions = self.generate_next_question_batch(self.conversation_history)
      for question in next_questions:
        print(f"\nInterviewer: {question}")
        user_answer = input("You: ")
        self.process_user_response(question, user_answer)
    
    # If we've reached the max questions, end the interview
    if self.question_count >= self.max_questions:
      print("\nInterviewer: Thank you for your responses. Generating structured requirements...")
      interview_data = self.synthesize_interview()
      self.save_interview_json(interview_data)
      print("Interview results saved to interview_results.json")


if __name__ == "__main__":
  # For demonstration, run the interactive interview
  interviewer = InterviewerAgent()
  interviewer.run_interactive_interview()