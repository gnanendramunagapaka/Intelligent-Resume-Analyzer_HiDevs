"""
File handling utilities for reading resumes (TXT, PDF, DOCX), loading JSON job descriptions,
and saving candidate matching reports.
"""

import os
import json
from typing import Dict, Any, List

class FileHandler:
    """
    Handles file interactions, including text extraction from various resume formats (PDF, DOCX, TXT),
    reading/writing JSON files, and path/directory validations.
    """
    
    @staticmethod
    def ensure_directory(directory_path: str) -> None:
        """
        Creates a directory if it does not already exist.
        
        Args:
            directory_path (str): Path of the directory.
        """
        if directory_path:
            os.makedirs(directory_path, exist_ok=True)

    @classmethod
    def read_txt(cls, file_path: str) -> str:
        """
        Reads content from a plain text file.
        
        Args:
            file_path (str): Path to the text file.
            
        Returns:
            str: Content of the text file.
            
        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file is empty.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if not content.strip():
                raise ValueError(f"File content is empty or contains only whitespace: {file_path}")
            return content
        except Exception as e:
            raise IOError(f"Error reading TXT file {file_path}: {str(e)}")

    @classmethod
    def read_pdf(cls, file_path: str) -> str:
        """
        Extracts text from a PDF file using pdfplumber.
        
        Args:
            file_path (str): Path to the PDF file.
            
        Returns:
            str: Extracted text content.
            
        Raises:
            ImportError: If pdfplumber is not installed.
            FileNotFoundError: If file does not exist.
            ValueError: If PDF is empty or text cannot be extracted.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")
            
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber library is required to parse PDF resumes.")

        try:
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            content = "\n".join(text_content)
            if not content.strip():
                raise ValueError(f"Could not extract text from PDF (it might be scanned/image-only or empty): {file_path}")
            return content
        except Exception as e:
            raise IOError(f"Error reading PDF file {file_path}: {str(e)}")

    @classmethod
    def read_docx(cls, file_path: str) -> str:
        """
        Extracts text from a DOCX file using python-docx.
        
        Args:
            file_path (str): Path to the DOCX file.
            
        Returns:
            str: Extracted text content.
            
        Raises:
            ImportError: If docx is not installed.
            FileNotFoundError: If file does not exist.
            ValueError: If DOCX is empty.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")

        try:
            import docx
        except ImportError:
            raise ImportError("python-docx (docx) library is required to parse DOCX resumes.")

        try:
            doc = docx.Document(file_path)
            text_content = [paragraph.text for paragraph in doc.paragraphs]
            
            # Extract from tables as well
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text_content.append(cell.text)
                        
            content = "\n".join(text_content)
            if not content.strip():
                raise ValueError(f"DOCX file content is empty: {file_path}")
            return content
        except Exception as e:
            raise IOError(f"Error reading DOCX file {file_path}: {str(e)}")

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Extracts text from a file, automatically detecting the extension.
        
        Args:
            file_path (str): Path to the file.
            
        Returns:
            str: Extracted raw text.
            
        Raises:
            ValueError: For unsupported formats.
        """
        if not file_path:
            raise ValueError("File path cannot be empty.")
            
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == ".txt":
            return cls.read_txt(file_path)
        elif ext == ".pdf":
            return cls.read_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return cls.read_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only PDF, DOCX, and TXT are supported.")

    @classmethod
    def read_json(cls, file_path: str) -> Dict[str, Any]:
        """
        Reads and parses a JSON file safely.
        
        Args:
            file_path (str): Path to the JSON file.
            
        Returns:
            dict: Parsed JSON data.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If JSON is invalid.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {str(e)}")
        except Exception as e:
            raise IOError(f"Error reading JSON file {file_path}: {str(e)}")

    @classmethod
    def write_json(cls, file_path: str, data: Dict[str, Any], indent: int = 4) -> None:
        """
        Writes data to a JSON file, ensuring the parent directory exists.
        
        Args:
            file_path (str): Path to write the JSON.
            data (dict): Data to serialize.
            indent (int): Indentation level for pretty-printing.
        """
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            cls.ensure_directory(parent_dir)
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Error writing JSON to {file_path}: {str(e)}")

    @staticmethod
    def validate_file(file_path: str, allowed_extensions: List[str] = None) -> bool:
        """
        Checks if a file exists, is not empty, and matches the allowed extensions.
        
        Args:
            file_path (str): Path to check.
            allowed_extensions (List[str]): List of valid extensions (e.g. ['.pdf', '.docx', '.txt'])
            
        Returns:
            bool: True if valid, False otherwise.
        """
        if not file_path or not os.path.exists(file_path):
            return False
            
        if os.path.getsize(file_path) == 0:
            return False
            
        if allowed_extensions:
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in [e.lower() for e in allowed_extensions]:
                return False
                
        return True
