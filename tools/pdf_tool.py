import os
import fitz
import docx

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        raw_text = text
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
    elif ext == ".docx":
        doc = docx.Document(file_path)
        raw_text = "\n".join([p.text for p in doc.paragraphs])
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # Security Step 2: Prompt Injection Defense
    from tools.security_tool import check_prompt_injection, mask_pii_emails
    if check_prompt_injection(raw_text):
        raise ValueError("🔒 Security Alert: Prompt injection attempt detected in document contents! (Forbidden command phrases like 'ignore instructions' or 'reveal api key' were found).")

    # Security Step 3: PII Masking
    return mask_pii_emails(raw_text)

