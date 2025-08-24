import json, os, pdb, time, glob, datetime, re
from typing import Dict, Any, List
from crewai import Agent, Task, Crew, LLM, Process
from tenacity import retry, stop_after_attempt, wait_fixed
from policy_agent_utilities import PolicyAgentUtilities
from retrieval_tool import RetrievalTool
from reranking_tool import ReRankingTool
from chat_ollama_llm import ChatOllamaLLM


class PolicyReviewerAgentRunner:
  VERBOSE=True

  def __init__(self, policies):
    # Create instances of the new tools
    retrieval_tool = RetrievalTool()
    reranking_tool = ReRankingTool()
    self.tools = [retrieval_tool, reranking_tool]

    self.policies = policies
    self.policy_instructions = self.create_instructions()
    self.review_log = self.retrieve_review_log()

    PolicyAgentUtilities.warm_model("gpt-oss:20b")
    PolicyAgentUtilities.warm_model("gpt-oss:120b")
    planning_llm = ChatOllamaLLM(model="gpt-oss:20b", temperature=0.2)
    action_llm = ChatOllamaLLM(model="gpt-oss:120b", temperature=0.5)

    policy_agent = self.create_policy_reviewer_agent(action_llm)

    task = Task(
        description=self.policy_instructions,
        expected_output="A markdown formatted policy or procedure document.",
        agent=policy_agent,
        tools=self.tools,
        guardrail=PolicyReviewerAgentRunner.validate_json_response,
        callback=self.append_to_review_ledger
      )

    self.crew = Crew(
      agents=[policy_agent],
      tasks=[task],
      process=Process.sequential,
      planning=True,
      planning_llm=planning_llm,
      llm=action_llm,
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
  

  @retry(stop=stop_after_attempt(30), wait=wait_fixed(2))
  def process_policy_reviews(self) -> None:
    inputs = []
    for policy_filepath in self.unreviewed_policy_file_paths():
      with open(policy_filepath) as f: content = f.read()
      inputs.append({"policy": content, "file_name": policy_filepath})
      
    self.crew.kickoff_for_each(inputs=inputs)

  def create_policy_reviewer_agent(self, llm) -> Agent:
    role = "Information Security Policy Reviewer"
    goal = """The goal is to review and refine first-draft security policies or procedures, ensuring they are comprehensive, compliant with industry standards, and aligned with the organization's specific context. It will achieve this by meticulously analyzing the draft against organizational background, industry standards, and best practices to produce a final, audit-ready document. To research the knowledge base, first use the `Initial Document Retrieval` tool to gather candidate documents. Then, feed the original query and the retrieved documents into the `Re-ranking Tool` to get the most relevant context."""
    backstory = """You are a senior information security auditor and GRC analyst with extensive experience in reviewing and improving security policies for organizations across various industries. You have deep expertise in information security standards (HIPAA, SOC 2, NIST CSF) and are skilled at identifying gaps in policy content. Your role is to enhance existing drafts by adding missing controls, ensuring accuracy against organizational context, and improving clarity for both employees and auditors."""


    return self.create_base_agent(role, goal, backstory, llm, self.tools)

  def create_base_agent(self, role, goal, backstory, llm, tools=[]) -> Agent:
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
      llm=llm
    )

  def append_to_review_ledger(self, result_data) -> None:
    """Append a review result to the review ledger."""
    # Read existing review_log.json or initialize with empty list
    results = json.loads(result_data.raw)

    # Get file name, this is clunky for now but works
    file_name = (m.group(1) if (m := re.search(r'"file_name"\s*:\s*"([^"]+)"', result_data.description)) else "Unknown")
    
    # Create new log entry with timestamp
    log_entry = {
      "timestamp": datetime.datetime.now().isoformat(),
      "file_path": file_name,
      "result_data": results
    }
    
    # Append new entry to the list
    self.review_log.append(log_entry)
    
    # Write updated list back to file in nicely formatted way
    with open(self.log_file_path, "w", encoding="utf-8") as f:
      json.dump(self.review_log, f, indent=2)

  def unreviewed_policy_file_paths(self) -> List[str]:
    # Collect file paths where 'decision' exists in result_data
    file_paths_with_decision = [
      entry["file_path"]
      for entry in self.review_log
      if "decision" in entry.get("result_data", {})
    ]
    if file_paths_with_decision:
      print("SKIPPING THESE ALREADY REVIEWED POLICIES:")
      print(",\n".join(file_paths_with_decision))

    not_in_decision_list = [
      path for path in self.policies if path not in file_paths_with_decision
    ]

    return not_in_decision_list

  def retrieve_review_log(self):
    if hasattr(self, 'review_log'):
      return self.review_log

    self.log_file_path = "output/review_log.json"
    review_log = []
    try:
      if os.path.exists(self.log_file_path) and os.path.getsize(self.log_file_path) > 0:
        with open(self.log_file_path, "r", encoding="utf-8") as f:
          review_log = json.load(f)
    except (json.JSONDecodeError, IOError):
      # If there's an issue reading the file, start with empty list
      review_log = []

    return review_log

  @staticmethod
  def validate_json_response(result):
    try:
      validated_result = PolicyAgentUtilities.parse_response(result.raw)
      if "decision" in validated_result and "justification" in validated_result:
        return (True, validated_result)
      else:
        return (False, "Result must follow the JSON structure in the instructions with decision and justification elements.")
    except Exception as err:
      return (False, "Result must be a valid JSON object with no other text.")


if __name__ == "__main__":
  #Turn off crew telemetry
  os.environ['OTEL_SDK_DISABLED'] = 'true'
  # For demonstration, run the policy generation
  reviewer = PolicyReviewerAgentRunner(glob.glob("output/policies/*.md"))
  reviewer.process_policy_reviews()