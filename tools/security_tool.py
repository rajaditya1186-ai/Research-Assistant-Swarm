import os
import re

def validate_file_signature(file_path: str) -> bool:
    """
    Validates the actual file binary structure against its extension.
    Supports .pdf, .docx, and .txt.
    """
    if not os.path.exists(file_path):
        return False
        
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            
        if ext == ".pdf":
            # PDF files must start with %PDF (% is 0x25, P is 0x50, D is 0x44, F is 0x46)
            return header.startswith(b"%PDF")
        elif ext == ".docx":
            # DOCX is a zip file. Zip files start with PK (P is 0x50, K is 0x4B)
            return header.startswith(b"PK\x03\x04")
        elif ext == ".txt":
            # Simple text files can have any bytes but should generally be decodable.
            # We check if we can read and decode the first few KB as text.
            try:
                with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                    f.read(1024)
                return True
            except UnicodeDecodeError:
                # If UTF-8 fails, try latin-1
                try:
                    with open(file_path, "r", encoding="latin-1", errors="strict") as f:
                        f.read(1024)
                    return True
                except Exception:
                    return False
        else:
            return False
    except Exception:
        return False

def mask_pii_emails(text: str) -> str:
    """
    Identifies sensitive personal information (emails, phone numbers, and IP addresses)
    and replaces them with masked placeholders.
    """
    if not text:
        return ""
        
    # Mask emails
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, "[EMAIL_MASKED]", text)
    
    # Mask phone numbers (supports various international/domestic formats)
    phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    text = re.sub(phone_pattern, "[PHONE_MASKED]", text)
    
    # Mask IPv4 addresses
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    text = re.sub(ip_pattern, "[IP_MASKED]", text)
    
    return text

def check_prompt_injection(text: str) -> bool:
    """
    Checks for common prompt injection patterns, unauthorized system instruction
    overrides, and credential disclosure requests. Returns True if an injection attempt is detected.
    """
    if not text:
        return False
        
    normalized = text.lower()
    
    # Static signatures list for direct/quick matching
    injection_signatures = [
        "ignore previous instructions",
        "ignore the instructions above",
        "ignore system prompt",
        "bypass system instructions",
        "ignore instructions",
        "reveal api key",
        "reveal your api key",
        "reveal the api key",
        "reveal api_key",
        "show api key",
        "print api key",
        "print the api key",
        "what is your api key",
        "give me your api key",
        "output your api key",
        "forget all previous instructions",
        "forget your instructions"
    ]
    
    for signature in injection_signatures:
        if signature in normalized:
            return True
            
    # Advanced regex matching for complex bypass phrasing
    regex_injection_patterns = [
        r"(?:ignore|bypass|override|forget|reset|clear)\s+(?:all\s+)?(?:previous\s+)?(?:system\s+)?(?:instructions|prompt|rules|constraints)",
        r"(?:output|show|reveal|print|display|tell|expose|give)\s+(?:your\s+)?(?:api\s+)?(?:key|secret|token|credentials)",
        r"(?:you\s+are\s+now|acting\s+as)\s+(?:a\s+)?(?:developer\s+mode|jailbreak|root|unrestricted)",
        r"system\s+override\s+mode"
    ]
    
    for pattern in regex_injection_patterns:
        if re.search(pattern, normalized):
            return True
            
    return False
