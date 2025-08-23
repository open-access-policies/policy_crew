import json, os, pdb, time, glob
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM, Process
from tenacity import retry, stop_after_attempt, wait_fixed
from policy_agent_utilities import PolicyAgentUtilities
from retrieval_tool import RetrievalTool
from reranking_tool import ReRankingTool

class PolicyReviewerAgentRunner:
  VERBOSE=True

  def __init__(self, policies):
    # Create instances of the new tools
    retrieval_tool = RetrievalTool()
    reranking_tool = ReRankingTool()
    self.tools = [retrieval_tool, reranking_tool]
    policy_agent = self.create_policy_reviewer_agent()
    self.policy_instructions = self.create_instructions()
    self.init_policy_status(policies)
    PolicyAgentUtilities.warm_model("gpt-oss:20b")
    PolicyAgentUtilities.warm_model("gpt-oss:120b")

    task = Task(
        description=self.policy_instructions,
        expected_output="A markdown formatted policy or procedure document.",
        agent=policy_agent,
        tools=self.tools,
        guardrail=PolicyAgentUtilities.validate_json_response
      )

    self.crew = Crew(
      agents=[policy_agent],
      tasks=[task],
      process=Process.sequential,
      planning=True,
      planning_llm=LLM(
        model="ollama/gpt-oss:20b",
        temperature=0.2,
        base_url="http://localhost:11434",
        verbose=self.VERBOSE
      ),
      verbose=self.VERBOSE)

  def create_instructions(self):
    style_guide_content = PolicyAgentUtilities.read_instructions("docs/writer/style_guide.md")
    policy_template_content = PolicyAgentUtilities.read_instructions("docs/templates/policy_template.md")
    company_context = PolicyAgentUtilities.read_instructions("output/company_context.json")

    policy_instructions = PolicyAgentUtilities.read_instructions("docs/writer/policy_reviewer_instructions.md")
    policy_instructions = policy_instructions.replace("style_guide_content", style_guide_content)
    policy_instructions = policy_instructions.replace("policy_template_content", policy_template_content)
    policy_instructions = policy_instructions.replace("company_context", company_context)
    return policy_instructions
  

  # @retry(stop=stop_after_attempt(30), wait=wait_fixed(2))
  def process_policy_reviews(self) -> None:
    for policy_filename, status in self.policy_status.items():
      if status not in ["drafted", "under_review"]:
        print("Skipping policy " + policy_filename)
        continue

      # Update status to "under_review" before processing
      self.policy_status[policy_filename] = "under_review"
      with open(policy_filename) as f: content = f.read()
      
      result = self.crew.kickoff(inputs={"policy": content})
      # pdb.set_trace()
      # Parse the result from JSON string into Python dictionary
      result_data = json.loads(result.raw)
      
      # Log the review result
      self.append_to_review_ledger(policy_filename, result_data)
      
      # Determine and update final status based on review outcome
      # For now, we'll set status to "approved" - in a more complex system,
      # this would be determined by analyzing the result_data
      self.policy_status[policy_filename] = "reviewed"


  def create_policy_reviewer_agent(self) -> Agent:
    role = "Information Security Policy Reviewer"
    goal = """The goal is to review and refine first-draft security policies or procedures, ensuring they are comprehensive, compliant with industry standards, and aligned with the organization's specific context. It will achieve this by meticulously analyzing the draft against organizational background, industry standards, and best practices to produce a final, audit-ready document. To research the knowledge base, first use the `Initial Document Retrieval` tool to gather candidate documents. Then, feed the original query and the retrieved documents into the `Re-ranking Tool` to get the most relevant context."""
    backstory = """You are a senior information security auditor and GRC analyst with extensive experience in reviewing and improving security policies for organizations across various industries. You have deep expertise in information security standards (HIPAA, SOC 2, NIST CSF) and are skilled at identifying gaps in policy content. Your role is to enhance existing drafts by adding missing controls, ensuring accuracy against organizational context, and improving clarity for both employees and auditors."""


    return self.create_base_agent(role, goal, backstory, self.tools)

  def create_base_agent(self, role, goal, backstory, tools=[]) -> Agent:
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
      tools=tools,
      llm=LLM(
        model="ollama/gpt-oss:120b",
        temperature=0.2,
        base_url="http://localhost:11434",
        verbose=self.VERBOSE
      )
    )
  
  def init_policy_status(self, policies):
    # Initialize and load policy status
    self.status_file_path = "output/policy_status.json"
    self.policy_status = {}
    
    # Load existing status or initialize with default "drafted" status
    if os.path.exists(self.status_file_path) and os.path.getsize(self.status_file_path) > 0:
      with open(self.status_file_path, "r", encoding="utf-8") as f:
        self.policy_status = json.load(f)
    else:
      # Initialize all policies with "drafted" status
      for policy in policies:
        self.policy_status[policy] = "drafted"
      self.save_policy_status()

  def save_policy_status(self):
    # Persist final state back to policy_status.json
    with open(self.status_file_path, "w", encoding="utf-8") as f:
      json.dump(self.policy_status, f, indent=2)

  def append_to_review_ledger(self, policy_name: str, result_data: Dict[str, Any]) -> None:
    """Append a review result to the review ledger."""
    # Read existing review_log.json or initialize with empty list
    log_file_path = "output/review_log.json"
    try:
      if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
        with open(log_file_path, "r", encoding="utf-8") as f:
          review_log = json.load(f)
      else:
        review_log = []
    except (json.JSONDecodeError, IOError):
      # If there's an issue reading the file, start with empty list
      review_log = []
    
    # Create new log entry with timestamp
    import datetime
    log_entry = {
      "timestamp": datetime.datetime.now().isoformat(),
      "policy_name": policy_name,
      "result_data": result_data
    }
    
    # Append new entry to the list
    review_log.append(log_entry)
    
    # Write updated list back to file in nicely formatted way
    with open(log_file_path, "w", encoding="utf-8") as f:
      json.dump(review_log, f, indent=2)

if __name__ == "__main__":
  #Turn off crew telemetry
  os.environ['OTEL_SDK_DISABLED'] = 'true'
  # For demonstration, run the policy generation
  reviewer = PolicyReviewerAgentRunner(glob.glob("output/policies/*.md"))
  reviewer.process_policy_reviews()