"""
Policy Generator Agent for ISMS Creation

This module implements a multi-agent system using the CrewAI framework
to automate the creation of an Information Security Management System (ISMS).
"""

import json, os, pdb
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM
from crewai_tools import DirectoryReadTool, FileWriterTool, FileReadTool

class ArchitectAgentRunner:
  VERBOSE=True
  """A multi-agent system that generates complete ISMS policy and procedure sets."""

  def __init__(self):
    """
    Initialize the Policy Generator Agent.
    """
    self.domain_agent = self.create_domain_architect_agent()
    self.policy_agent = self.create_policy_architect_agent()

    # Read the architect instructions
    self.domain_instructions = self.read_instructions("docs/architect/domain_architect.md")
    self.policy_instructions = self.read_instructions("docs/architect/policy_architect.md")
  
  def generate_policy_outline(self) -> None:
    """
    Generate the complete ISMS policy and procedure set using CrewAI agents.
    """
    domains = self.generate_domain_outline()
    policy_tasks = self.create_policy_tasks(domains)
    policy_outlines = self.generate_policy_outlines(policy_tasks)

  def generate_domain_outline(self):
    # Create tasks
    # Task 1: Create the blueprint
    domain_task = Task(
      description=self.domain_instructions,
      expected_output="A structured JSON object containing a list of the high-level policy domains required to meet the organization's security and compliance needs.",
      agent=self.domain_agent,
      tools=[FileReadTool(file_path="output/interview_results.json")],
      guardrail=self.validate_json_response
    )
    
    # Create the crew and run the process
    crew = Crew(
      agents=[self.domain_agent],
      tasks=[domain_task],
      verbose=self.VERBOSE
    )

    # Execute the crew
    result = crew.kickoff()
    return self.parse_response(result.raw)

  def generate_policy_outlines(self, tasks):
    crew = Crew(
      agents=[self.policy_agent],
      tasks=tasks,
      verbose=self.VERBOSE)
    result = crew.kickoff()
    pdb.set_trace()

  def create_policy_tasks(self, domains):
    tasks = []
    for domain in domains.get("policy_domains", []):
      tasks.append( Task(
        description=self.policy_instructions.replace("{domain}", str(domain)),
        expected_output="A structured JSON object containing a comprehensive list of the specific policies necessary to satisfy the requirements of a single, assigned security domain.",
        agent=self.policy_agent,
        input=domain,
        guardrail=self.validate_json_response
      ) )
    return tasks

  @staticmethod
  def validate_json_response(result):
    try:
      validated_result = ArchitectAgentRunner.parse_response(result.raw)
      pdb.set_trace()
      return (True, validated_result)
    except Exception as err:
      pdb.set_trace()
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

  def create_domain_architect_agent(self) -> Agent:
    role = "Information Security Policy Architect for Domain Level Analysis"
    goal = """This agent analyzes an organization's requirements to identify the essential, high-level policy domains required to fulfill their 
              security and compliance needs. It then synthesizes this analysis into a structured JSON object that outlines each domain's requirements 
              and maps them to specific compliance standards. This output serves as the strategic foundation for the entire ISMS structure."""
    backstory = """You are a former Chief Information Security Officer (CISO) who has transitioned into a strategic GRC consulting role. With over 15 
                   years of experience, you have guided numerous companies, from startups to enterprises, through the complex process of building 
                   security programs from scratch. Your expertise lies in your ability to quickly diagnose a company's core business drivers and 
                   compliance obligations, and from that, architect a high-level, strategic map of the essential security domains they need to focus 
                   on. You excel at seeing the forest for the trees, translating complex regulatory requirements like HIPAA and SOC 2 into a clear, 
                   logical, and actionable set of foundational pillars for any security program."""

    return self.create_architect_agent(role, goal, backstory)

  def create_policy_architect_agent(self) -> Agent:
    role = "Information Security Policy Architect for Policy Level Analysis"
    goal = """This agent takes a single, high-level policy domain and deconstructs it into a comprehensive list of the specific policies necessary to 
              meet its requirements. For each policy, it defines the key controls it must contain and links them back to the relevant compliance 
              sections. The final output is a detailed JSON plan that guides the creation of all policy documents within that domain."""
    backstory = """You are a seasoned Senior Security Architect who has spent years in the trenches designing and implementing security controls for 
                   cloud-native technology companies. Your background is deeply technical, but your real passion is in codifying best practices into 
                   clear, comprehensive policies. You have a reputation for being the bridge between high-level strategy and technical implementation, 
                   with an expert ability to take a broad domain like "Access Control" and deconstruct it into the specific, granular policies needed 
                   to make it a reality. You know exactly what controls are necessary to satisfy auditors and what level of detail is needed to guide 
                   an engineering team."""

    return self.create_architect_agent(role, goal, backstory)

  def create_architect_agent(self, role, goal, backstory) -> Agent:
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
  architect = ArchitectAgentRunner()
  architect.generate_policy_outline()