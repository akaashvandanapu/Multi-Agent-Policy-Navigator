"""
Document processor for loading and chunking agricultural documents
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from sentence_transformers import SentenceTransformer
from policy_navigator.config.llm_config import get_embedding_model


class DocumentProcessor:
    """Processes PDF and text documents for RAG"""
    
    def __init__(self, data_path: str = "data"):
        """
        Initialize document processor
        
        Args:
            data_path: Path to data directory containing documents
        """
        self.data_path = Path(data_path)
        embedding_model = get_embedding_model()
        self.embedder = SentenceTransformer(embedding_model)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def read_text_file(self, txt_path: Path) -> str:
        """
        Read text from .txt file
        
        Args:
            txt_path: Path to text file
            
        Returns:
            File content
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file {txt_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into chunks for vector storage
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # Only break if reasonable
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def process_document(self, file_path: Path, category: str) -> List[Dict[str, Any]]:
        """
        Process a single document and return chunks with metadata
        
        Args:
            file_path: Path to document
            category: Document category
            
        Returns:
            List of chunks with metadata
        """
        # Determine file type and extract text
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() == '.txt':
            text = self.read_text_file(file_path)
        else:
            print(f"Unsupported file type: {file_path.suffix}")
            return []
        
        if not text:
            return []
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        # Create metadata for each chunk
        results = []
        for idx, chunk in enumerate(chunks):
            results.append({
                'text': chunk,
                'source': file_path.name,
                'category': category,
                'chunk_index': idx,
                'total_chunks': len(chunks)
            })
        
        return results
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """
        Process all documents in the data directory
        
        Returns:
            List of all document chunks with metadata
        """
        all_chunks = []
        
        # Map folder names to categories
        category_mapping = {
            '01_Financial_Schemes': 'Financial Schemes',
            '02_Credit_Loans': 'Credit Loans',
            '03_Crop_Insurance': 'Crop Insurance',
            '04_Seeds_Inputs': 'Seeds Inputs',
            '05_Irrigation_Water': 'Irrigation Water',
            '06_Soil_Health': 'Soil Health',
            '07_Farm_Mechanization': 'Farm Mechanization',
            '08_Market_Pricing': 'Market Pricing',
            '09_Horticulture_Allied': 'Horticulture Allied',
            '10_Extension_Training': 'Extension Training',
            '11_Digital_Initiatives': 'Digital Initiatives',
            '12_Calamity_Relief': 'Calamity Relief',
            '13_Crop_Cultivation_Guides': 'Crop Cultivation Guides',
            '14_Pest_Disease_Management': 'Pest Disease Management',
            '15_Fertilizer_Schedules': 'Fertilizer Schedules',
            '16_Crop_Calendar': 'Crop Calendar',
            '17_Crop_Varieties': 'Crop Varieties',
        }
        
        # Process each category folder
        for folder_name, category in category_mapping.items():
            folder_path = self.data_path / folder_name
            if not folder_path.exists():
                continue
            
            # Process all files in the folder
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt']:
                    chunks = self.process_document(file_path, category)
                    all_chunks.extend(chunks)
        
        return all_chunks

