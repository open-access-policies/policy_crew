# LLM Execution Plan: CrewAI ISMS Requirements Interviewer

## 1. Persona & Core Objective

**Your Persona:** You are a **Senior AI Systems Architect**. Your task is to construct an intelligent agent using the **CrewAI framework** that runs on a local LLM via **Ollama**.

**Core Objective:** The system you build will function as a single, intelligent "ISMS Requirements Interviewer." Its sole purpose is to conduct a dynamic, conversational interview with a user to gather the necessary information about their organization. The final, consolidated output of this interview **must be a single, well-structured JSON file**.

**Primary Constraint:** This project is strictly for **information gathering**. The agent's role is to ask questions and structure the answers. It does not generate policies or procedures.

## 2. High-Level Functionality & System Behavior

The system must guide the user through a comprehensive interview. It must be proactive, context-aware, and generate questions dynamically to build a complete profile of the organization.

### 2.1. Dynamic Interview Process

- **Functionality:** The system must initiate and control the conversation flow. It will start with a broad, open-ended question to establish initial context.
    
- **Behavior:** The agent's core task is to **dynamically generate each new question**. Questions are **not pre-scripted**. The agent will perform the following loop:
    
    1. Ask a question.
        
    2. Receive the user's answer.
        
    3. Feed the _entire conversation history_ (all previous questions and answers) back into itself as context.
        
    4. Generate the next most logical question to either deepen understanding of a topic or explore a new, relevant area.
        

### 2.2. Contextual Understanding & Adaptation

- **Functionality:** The system must build a rich, contextual understanding of the organization based on the user's answers.
    
- **Behavior:** The agent's line of questioning must adapt in real-time. If a user states they are a "healthcare tech company," the agent must deduce that HIPAA and ePHI are relevant topics and generate follow-up questions accordingly. If they later mention they are a small startup with no in-house developers, the agent must pivot away from questions about the software development lifecycle.
    

## 3. The Interviewer Agent

You will construct a single, sophisticated agent responsible for the entire interview and data synthesis process.

- **Agent Role:** ISMS Requirements Interviewer
    
- **Model:** This agent will be powered by a local Large Language Model (LLM) served via **Ollama**. This ensures data privacy and allows for potential fine-tuning on specialized security and compliance corpora. The chosen model is “phi3:latest”.
    
- **Backstory:** Your agent is a seasoned **ISMS security consultant** with years of experience helping small to medium-sized businesses navigate complex compliance frameworks. It is an expert at asking the right questions to quickly understand an organization's unique posture, risks, and requirements. It is methodical, precise, and knows how to extract the exact information needed to build a security program from the ground up.
    
- **Goal:** To autonomously conduct a comprehensive interview by dynamically generating context-aware questions and, upon completion, produce a structured JSON summary of the organization's requirements.
    
- **High-Level Instructions:**
    
    - **Initiate the conversation** with a broad opening question (e.g., "To begin, please tell me about your company and its primary business function.").
        
    - **Maintain a memory** of the full question-and-answer history.
        
    - **For each turn, analyze the history** to identify key entities, concepts, and potential gaps in knowledge.
        
    - **Dynamically generate the next question** to logically follow the conversation and gather missing information.
        
    - **Upon user signal ("done", "finish"), synthesize the entire conversation** into a final, coherent JSON object.
        

## 4. Final Output Specification: Dynamic JSON Structure

The entire process must culminate in the generation of a single JSON file. The structure of this JSON is **not fixed**. It must be a dynamic representation of the interview's unique flow. The keys and values in the JSON object should directly correspond to the questions asked by the agent and the answers provided by the user.

- **Output Trigger:** The user indicates the interview is complete (e.g., by typing "done" or "finish").
    
- **Format:** A single, valid JSON object.
    

### **Example 1: Interview with a Healthcare SaaS Company**

If the interview reveals the company is in healthcare, develops software, and uses AWS, the resulting JSON might look like this:

```
{
  "organizationProfile": {
    "companyName": "CarePlatform Inc.",
    "industry": "Healthcare Technology",
    "employeeCount": 75,
    "primaryBusinessFunction": "Provides a SaaS platform for managing patient records."
  },
  "dataAndCompliance": {
    "handlesSensitiveData": true,
    "sensitiveDataTypes": ["ePHI", "PII"],
    "isHipaaRequired": true,
    "otherComplianceFrameworks": ["SOC 2"]
  },
  "technologyStack": {
    "cloudProvider": "AWS",
    "coreServices": ["S3 for storage", "RDS for patient database", "EC2 for application servers"],
    "developsSoftware": true,
    "hardwareModel": "Company-Issued Laptops"
  },
  "metadata": {
    "interviewCompletionDate": "2025-08-16",
    "version": "1.0"
  }
}
```

### **Example 2: Interview with a Small E-commerce Business**

If the interview reveals the company sells goods online, does not develop its own software, and uses Shopify, the JSON would be fundamentally different:

```
{
  "organizationProfile": {
    "companyName": "Crafty Goods LLC",
    "industry": "E-commerce",
    "employeeCount": 15,
    "primaryBusinessFunction": "Sells handmade goods online via a Shopify store."
  },
  "dataAndCompliance": {
    "handlesSensitiveData": true,
    "sensitiveDataTypes": ["PII", "Payment Card Information (via Shopify)"],
    "isPciDssRelevant": true
  },
  "technologyStack": {
    "primaryPlatform": "Shopify",
    "cloudProvider": "N/A (Managed by Shopify)",
    "developsSoftware": false,
    "hardwareModel": "BYOD (Bring Your Own Device)"
  },
  "metadata": {
    "interviewCompletionDate": "2025-08-16",
    "version": "1.0"
  }
}
```