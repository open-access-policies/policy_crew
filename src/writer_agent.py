
import json, os, pdb, time
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import DirectoryReadTool, FileWriterTool, FileReadTool

class WriterAgentRunner:
  VERBOSE=True

  def __init__(self):
    self.policy_agent = self.create_writer_agent()
    self.policy_instructions = self.read_instructions("docs/writer/instructions.md")
    self.file_readers = [
      FileReadTool(file_path="docs/writer/style_guide.md"),
      FileReadTool(file_path="docs/templates/policy_template.md"),
      FileReadTool(file_path="docs/templates/procedures_template.md")
    ]
  
  def generate_policy_outline(self, policies) -> None:
    task = Task(
        description=self.policy_instructions,
        expected_output="A markdown formatted policy or procedure document.",
        agent=self.policy_agent,
        tools=self.file_readers,
        # guardrail=self.validate_json_response
      )

    crew = Crew(
      agents=[self.policy_agent],
      tasks=[task],
      process=Process.sequential,
      verbose=self.VERBOSE)

    batch_size = 5
    input_list = [{"input": policy} for policy in policies]
    batches = [input_list[i:i + batch_size] for i in range(0, len(input_list), batch_size)]
    results = []
    for batch in batches:
      results.append(crew.kickoff_for_each(inputs=batch))
      time.sleep(60)

    pdb.set_trace()


  @staticmethod
  def validate_json_response(result):
    try:
      validated_result = ArchitectAgentRunner.parse_response(result.raw)
      return (True, validated_result)
    except Exception as err:
      return (False, "Result must be a valid JSON object with no other text.")

  @staticmethod
  def parse_response(result):
    # Handle markdown-wrapped JSON if present
    if result.strip().startswith("```json"):
      # Extract JSON from markdown code block
      json_start = result.find("{")
      json_end = result.rfind("}") + 1
      if json_start != -1 and json_end != -1:
        result = result[json_start:json_end]
      else:
        # If we can't find proper JSON bounds, use the whole result
        result = result.strip()
    else:
      result = result.strip()

    return json.loads(result)

  def create_writer_agent(self) -> Agent:
    role = "Information Security Policy Writer"
    goal = """The goal is to generate the complete, first-draft text for a single security policy or procedure. It will achieve this by strictly adhering to 
           a provided template and style guide, while tailoring the content to fulfill the specific requirements it is given. The final output will be a 
           single, fully-formatted Markdown document that is both audit-ready and employee-friendly."""
    backstory = """You are a former senior technical writer from a major GRC (Governance, Risk, and Compliance) consulting firm, renowned for your 
                ability to translate complex regulatory requirements into clear, actionable, and auditable corporate policies. Your professional 
                experience is built on a deep understanding of security frameworks and an unwavering attention to detail, which allows you to meticulously 
                follow templates and style guides to produce perfectly structured documents. You are highly skilled at writing for a dual audience, 
                crafting prose that is both unambiguous and defensible for an auditor, yet clear and easy for an everyday employee to understand and follow."""

    return self.create_base_agent(role, goal, backstory)

  def create_base_agent(self, role, goal, backstory) -> Agent:
    """
    Create the Policy Architect agent using CrewAI.
    
    Returns:
      An initialized CrewAI Agent instance
    """
    return Agent(
      role=role, goal=goal, backstory=backstory + " Reasoning: high",
      verbose=self.VERBOSE, allow_delegation=False,
      tools=[], reasoning=True, memory=True,
      llm=LLM(
        model="ollama/gpt-oss:120b",
        temperature=0.7,
        base_url="http://localhost:11434",
        verbose=self.VERBOSE
      )
    )


  def read_instructions(self, path: str) -> str:
    """
    Read instructions from a file.
    
    Args:
      path: Path to the instructions file
      
    Returns:
      The content of the instructions file
    """
    try:
      with open(path, "r") as f:
        return f.read()
    except FileNotFoundError:
      # Fallback to a basic prompt if file not found
      print(f"Warning: {path} not found")
      raise SystemExit(1)


if __name__ == "__main__":
  #Turn off crew telemetry
  os.environ['OTEL_SDK_DISABLED'] = 'true'
  # For demonstration, run the policy generation
  writer = WriterAgentRunner()
  with open("policy_output.json", "r", encoding="utf-8") as f:
    policies = json.load(f)["policies"]
  writer.generate_policy_outline(policies=policies)