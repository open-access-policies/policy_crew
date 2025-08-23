
import json, os, pdb, time
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import DirectoryReadTool, FileWriterTool, FileReadTool
from tenacity import retry, stop_after_attempt, wait_fixed
from policy_agent_utilities import PolicyAgentUtilities

class WriterAgentRunner:
  VERBOSE=True

  def __init__(self):
    self.policy_agent = self.create_writer_agent()
    self.policy_instructions = self.create_instructions()

  def create_instructions(self):
    style_guide_content = PolicyAgentUtilities.read_instructions("docs/writer/style_guide.md")
    policy_template_content = PolicyAgentUtilities.read_instructions("docs/templates/policy_template.md")
    procedures_template_content = PolicyAgentUtilities.read_instructions("docs/templates/procedures_template.md")

    policy_instructions = PolicyAgentUtilities.read_instructions("docs/writer/instructions.md")
    policy_instructions = policy_instructions.replace("style_guide_content", style_guide_content)
    policy_instructions = policy_instructions.replace("policy_template_content", policy_template_content)
    policy_instructions = policy_instructions.replace("procedures_template_content", procedures_template_content)
    return policy_instructions
    
  @retry(stop=stop_after_attempt(30), wait=wait_fixed(2))
  def generate_policy_outline(self, policies) -> None:
    task = Task(
        description=self.policy_instructions,
        expected_output="A markdown formatted policy or procedure document.",
        agent=self.policy_agent
      )

    crew = Crew(
      agents=[self.policy_agent],
      tasks=[task],
      process=Process.sequential,
      verbose=self.VERBOSE)

    results = []
    for policy in policies:
      if PolicyAgentUtilities.is_policy_complete(policy):
        print('Skipping already complete policy: ' + policy["policy_name"])
        continue
      result = crew.kickoff(inputs={"input": policy})
      PolicyAgentUtilities.write_policy_file(policy, result)
      print('Finished writing ' + policy["policy_name"])
      # time.sleep(60)

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
      role=role, goal=goal, backstory=backstory + " Reasoning: medium",
      verbose=self.VERBOSE, 
      allow_delegation=False,
      reasoning=True, max_reasoning_attempts=5,
      memory=True,
      llm=LLM(
        model="ollama/gpt-oss:120b",
        temperature=0.2,
        base_url="http://localhost:11434",
        verbose=self.VERBOSE
      )
    )

if __name__ == "__main__":
  #Turn off crew telemetry
  os.environ['OTEL_SDK_DISABLED'] = 'true'
  # For demonstration, run the policy generation
  writer = WriterAgentRunner()
  with open("policy_output.json", "r", encoding="utf-8") as f:
    policies = json.load(f)["policies"]
  writer.generate_policy_outline(policies=policies)