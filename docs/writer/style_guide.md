# ISMS Writing & Style Guide

This document is the single source of truth for the tone, style, word choice, and formatting of all documents within the Information Security Management System (ISMS). All writing and editing agents must adhere to these guidelines strictly.

## Tone & Voice

- **Authoritative & Helpful:** The tone should be professional, direct, and clear, establishing rules and requirements without ambiguity. However, it should also be helpful, not punitive. The goal is to empower team members to do the right thing.
    
- **Active Voice:** Use the active voice whenever possible. (e.g., "The IT team grants access..." instead of "Access is granted by the IT team...").
    
- **Clarity Over Jargon:** While technical accuracy is essential, avoid unnecessary jargon. If a technical term is required, define it in the Glossary.
    

## Word Choice & Glossary

- **`Team Member`:** Always use "team member" instead of "employee," "staff," or "user."
    
- **`The Company`:** Use "the Company" when referring to the organization itself.
    
- **Acronyms:** Define all acronyms on their first use. For example: "Information Security Management System (ISMS)." A master list of acronyms should be maintained in the `_annexes/glossary.md` file.
    
- **Shall, Will, Must:** Use "must" for mandatory requirements. Avoid using "shall" or "will."
    

## Writing for Readability & Auditability

- **Testable Assertions:** Every policy statement must be a testable assertion that an auditor can verify. Avoid vague or subjective language.
    
    - **Bad (Not Testable):** `The network must be kept secure.`
        
    - **Good (Testable):** `All inbound network traffic from the internet is blocked by default and must be explicitly allowed by a firewall rule.`
        
- **Scannability:** Documents must be easy for team members to scan and understand quickly.
    
    - Keep paragraphs short (3-4 sentences maximum).
        
    - Use bulleted lists to break up complex ideas.
        
    - Use tables to present structured information, especially for roles and responsibilities.
        

## Document Structure & Formatting

- **YAML Front Matter:** All policy and procedure documents must begin with a YAML front matter block for metadata.
    
    ```
    ---
    title: Incident Response Plan (IRP) ([RES-PROC-001])
    parent: Resilience Procedures
    nav_order: 1
    ---
    ```
    
- **Headings:**
    
    - Do not include the document title as a header in the body of the text; it belongs only in the front matter.
        
    - Major Sections (`Purpose`, `Scope`, etc.): H1 (`#`)
        
    - Sub-sections: H2 (`##`) and H3 (`###`)
        
- **Lists:**
    
    - Use hyphens (`-`) for unordered lists.
        
    - Use numbered lists (`1.`, `2.`) for sequential steps in procedures.
        
- **Emphasis:**
    
    - Use _italics_ (`*text*`) for emphasis on specific words.
        
- **Internal Linking:** When referencing another document within the ISMS, use its formal title as defined in its front matter.
    
    - **Example:** `All access requests must follow the process defined in the User Access Request Procedure.`
        
- **Mandatory Sections:**
    
    - **Policies:** Every policy document must follow the `_templates/Policy Template.md` and include, at a minimum: `# Purpose`, `# Scope`, `# Policy`, and `# Roles and Responsibilities`.
        
    - **Procedures:** Every procedure document must follow the `_templates/Procedures Template.md` and include, at a minimum: `# Purpose`, `# Scope`, `# Procedure`, and `# Roles and Responsibilities`.
        

## Markdown Compatibility & Portability

To ensure documents render correctly on the web (GitHub Pages) and can be reliably converted to other formats like PDF (using tools like Pandoc), follow these Markdown conventions:

- **Tables:** Use standard GitHub Flavored Markdown for tables. Ensure there is a separator line with at least three hyphens (`---`) for each column. Keep tables simple for maximum compatibility.
    
    ```
    | Role                  | Responsibility                                      |
    | --------------------- | --------------------------------------------------- |
    | Chief Technology Officer | Owns and approves the overall security program.     |
    | IT Team               | Implements and manages technical security controls. |
    ```
    
- **Line Breaks:** Use a blank line to separate paragraphs. This is the most universally supported way to create a new paragraph. For a hard line break within a paragraph (use sparingly), end the line with two spaces.
    
- **Images:** Use relative paths for images stored within the repository. This ensures they work in both the web view and local editors.
    
    - **Example:** `![Company Logo](./assets/images/logo.png)`
        
- **Escaping Characters:** If you need to use a character that has a special meaning in Markdown (like `*` or `#`) as literal text, escape it with a backslash (`\`).
    
    - **Example:** `This is a literal asterisk: \*`
        
- **Pandoc / PDF Export:**
    
    - The YAML front matter (`title`, `owner`, etc.) will be used by Pandoc to populate the PDF's metadata.
        
    - To automatically generate a Table of Contents when exporting, Pandoc can be run with the `--toc` flag. No special formatting is needed in the document itself.