from crewai import BaseLLM, Agent
from langchain_ollama import OllamaLLM
from typing import Any, Dict, List, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import pdb

class ChatOllamaLLM(BaseLLM):
  def __init__(self, model: str, base_url: str = "http://localhost:11434", temperature: Optional[float] = None):
    super().__init__(model=model, temperature=temperature)
    self.chat_ollama = OllamaLLM(
      model=model,
      base_url=base_url,
      temperature=temperature or 0.7
    )
  
  def call(
    self,
    messages: Union[str, List[Dict[str, str]]],
    tools: Optional[List[dict]] = None,
    callbacks: Optional[List[Any]] = None,
    available_functions: Optional[Dict[str, Any]] = None,
    from_task: Optional[Any] = None,
    from_agent: Optional[Any] = None,
  ) -> Union[str, Any]:
    # Convert string to message format if needed
    if isinstance(messages, str):
      result = self.chat_ollama.invoke([HumanMessage(content=messages)])
    else:
      # Convert dict format to LangChain messages
      lc_messages = []
      for msg in messages:
        if msg["role"] == "user":
          lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
          lc_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
          lc_messages.append(SystemMessage(content=msg["content"]))
      
      result = self.chat_ollama.invoke(lc_messages)
    
    return result

  def supports_function_calling(self) -> bool:
    return False
