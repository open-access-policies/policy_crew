from typing import Dict, Any
import os, pdb, json, ollama

class PolicyAgentUtilities:
  @staticmethod
  def filename_from_policy(policy):
    # Filter out invalid characters for MacOS filenames
    filename = policy["policy_name"] + ".md"
    # Remove invalid characters for MacOS filenames
    invalid_chars = ['/', ':', '\\', '*', '?', '"', '<', '>', '|', '\0']
    for char in invalid_chars:
      filename = filename.replace(char, '_')
    return filename 

  @staticmethod
  def write_policy_file(policy, result):
    # Filter out invalid characters for MacOS filenames
    filename = PolicyAgentUtilities.filename_from_policy(policy)
    with open("output/policies/" + filename, "w") as f:
      f.write(result.raw)
    PolicyAgentUtilities.mark_policy_complete(filename)

  @staticmethod
  def mark_policy_complete(filename):
    with open("output/policies/completed.out", "a") as f:
      f.write(filename + "\n")

  @staticmethod
  def is_policy_complete(policy):
    print('Checking for policy: ' + PolicyAgentUtilities.filename_from_policy(policy))
    with open("output/policies/completed.out") as f:
      if PolicyAgentUtilities.filename_from_policy(policy) in f.read():
        return True
      else:
        return False

  @staticmethod
  def read_instructions(path: str) -> str:
    try:
      with open(path, "r") as f:
        return f.read()
    except FileNotFoundError:
      # Fallback to a basic prompt if file not found
      print(f"Warning: {path} not found")
      raise SystemExit(1)

  @staticmethod
  def validate_json_response(result):
    try:
      validated_result = PolicyAgentUtilities.parse_response(result.raw)
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

  @staticmethod
  def warm_model(model_name: str):
    # Send a trivial request to load the model into memory
    ollama.chat(
      model=model_name,
      messages=[{'role': 'user', 'content': 'Hi'}],
      stream=False  # ensure it completes
    )
    print(model_name + " has been warmed up.")