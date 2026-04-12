import re
import pdfplumber
from docx import Document

class ResumeParser:
    def __init__(self):
        self.skills_db = ['python','java','javascript','react','sql','aws','docker','machine learning','django','flask']
    
    def parse_resume(self, file_path):
        text = ""
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            with open(file_path, 'r') as f:
                text = f.read()
        return {
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'skills': self._extract_skills(text)
        }
    
    def _extract_name(self, text):
        lines = text.split('\n')
        return lines[0].strip() if lines else ""
    
    def _extract_email(self, text):
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text):
        match = re.search(r'\b\d{10}\b', text)
        return match.group(0) if match else ""
    
    def _extract_skills(self, text):
        found = [s for s in self.skills_db if s.lower() in text.lower()]
        return found