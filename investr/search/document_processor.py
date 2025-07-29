"""Document processor for extracting and chunking text from PDF files."""

import hashlib
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel
from pypdf import PdfReader

from investr.data.azure_search_client import SearchDocument


class DocumentChunk(BaseModel):
    """Document chunk model."""

    chunk_id: str
    content: str
    page_number: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class ProcessedDocument(BaseModel):
    """Processed document model."""

    document_id: str
    title: str
    source: str
    total_pages: Optional[int] = None
    total_chars: int
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any] = {}


class DocumentProcessor:
    """Document processor for PDF files."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ) -> None:
        """Initialize document processor.

        Args:
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum size of text chunks

        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def extract_text_from_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with extracted text and metadata

        """
        try:
            reader = PdfReader(file_path)

            # Extract metadata
            metadata = {
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "num_pages": len(reader.pages),
            }

            # Extract PDF metadata if available
            if reader.metadata:
                pdf_metadata = reader.metadata
                metadata.update(
                    {
                        "title": pdf_metadata.get("/Title", ""),
                        "author": pdf_metadata.get("/Author", ""),
                        "subject": pdf_metadata.get("/Subject", ""),
                        "creator": pdf_metadata.get("/Creator", ""),
                        "producer": pdf_metadata.get("/Producer", ""),
                        "creation_date": str(pdf_metadata.get("/CreationDate", "")),
                        "modification_date": str(pdf_metadata.get("/ModDate", "")),
                    }
                )

            # Extract text from all pages
            full_text = ""
            page_texts = []

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    page_texts.append(
                        {
                            "page_number": page_num,
                            "text": page_text,
                            "char_count": len(page_text),
                        }
                    )
                    full_text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    page_texts.append(
                        {
                            "page_number": page_num,
                            "text": "",
                            "char_count": 0,
                        }
                    )

            return {
                "full_text": full_text.strip(),
                "page_texts": page_texts,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise

    def chunk_text(
        self,
        text: str,
        page_number: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """Split text into chunks.

        Args:
            text: Text to chunk
            page_number: Page number for the text

        Returns:
            List of document chunks

        """
        if len(text) < self.min_chunk_size:
            # Text is too small to chunk, return as single chunk
            chunk_id = str(uuid.uuid4())
            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=text,
                    page_number=page_number,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        chunks = []
        start = 0

        while start < len(text):
            # Determine end position
            end = min(start + self.chunk_size, len(text))

            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (. followed by space)
                sentence_end = text.rfind(". ", start, end)
                if sentence_end > start + self.min_chunk_size:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(" ", start, end)
                    if word_end > start + self.min_chunk_size:
                        end = word_end

            # Extract chunk text
            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self.min_chunk_size:
                chunk_id = str(uuid.uuid4())
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        content=chunk_text,
                        page_number=page_number,
                        start_char=start,
                        end_char=end,
                    )
                )

            # Move to next chunk with overlap
            start = max(end - self.chunk_overlap, start + 1)

            # Prevent infinite loop
            if start >= len(text):
                break

        return chunks

    def process_pdf(self, file_path: Path) -> ProcessedDocument:
        """Process a PDF file into searchable document chunks.

        Args:
            file_path: Path to PDF file

        Returns:
            Processed document with chunks

        """
        logger.info(f"Processing PDF: {file_path}")

        # Extract text from PDF
        extraction_result = self.extract_text_from_pdf(file_path)
        full_text = extraction_result["full_text"]
        page_texts = extraction_result["page_texts"]
        metadata = extraction_result["metadata"]

        # Generate document ID based on file content
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        document_id = f"doc_{content_hash[:12]}"

        # Determine document title
        title = metadata.get("title", "").strip()
        if not title:
            title = file_path.stem

        # Chunk the full document
        all_chunks = []

        # Option 1: Chunk by page (better for maintaining context)
        for page_info in page_texts:
            if page_info["text"].strip():
                page_chunks = self.chunk_text(
                    page_info["text"], page_number=page_info["page_number"]
                )
                all_chunks.extend(page_chunks)

        # If no chunks from pages, chunk the full text
        if not all_chunks:
            all_chunks = self.chunk_text(full_text)

        logger.info(f"Created {len(all_chunks)} chunks from {file_path}")

        return ProcessedDocument(
            document_id=document_id,
            title=title,
            source=str(file_path),
            total_pages=metadata.get("num_pages"),
            total_chars=len(full_text),
            chunks=all_chunks,
            metadata=metadata,
        )

    def convert_to_search_documents(
        self,
        processed_doc: ProcessedDocument,
    ) -> List[SearchDocument]:
        """Convert processed document to Azure Search documents.

        Args:
            processed_doc: Processed document

        Returns:
            List of search documents

        """
        search_documents = []

        for chunk in processed_doc.chunks:
            # Create search document for each chunk
            search_doc = SearchDocument(
                id=f"{processed_doc.document_id}_{chunk.chunk_id}",
                title=processed_doc.title,
                content=chunk.content,
                source=processed_doc.source,
                chunk_id=chunk.chunk_id,
                metadata={
                    "document_id": processed_doc.document_id,
                    "page_number": chunk.page_number,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "total_pages": processed_doc.total_pages,
                    "file_size": processed_doc.metadata.get("file_size"),
                    "author": processed_doc.metadata.get("author"),
                    "creation_date": processed_doc.metadata.get("creation_date"),
                },
            )
            search_documents.append(search_doc)

        return search_documents

    async def process_directory(
        self,
        directory_path: Path,
        file_pattern: str = "*.pdf",
    ) -> List[SearchDocument]:
        """Process all PDF files in a directory.

        Args:
            directory_path: Directory containing PDF files
            file_pattern: File pattern to match

        Returns:
            List of search documents from all processed files

        """
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        pdf_files = list(directory_path.glob(file_pattern))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")

        all_search_documents = []

        for pdf_file in pdf_files:
            try:
                processed_doc = self.process_pdf(pdf_file)
                search_docs = self.convert_to_search_documents(processed_doc)
                all_search_documents.extend(search_docs)
                logger.info(f"Processed {pdf_file.name}: {len(search_docs)} chunks")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        logger.info(f"Total documents created: {len(all_search_documents)}")
        return all_search_documents
