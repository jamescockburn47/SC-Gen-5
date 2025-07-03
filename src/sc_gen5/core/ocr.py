"""OCR module for text extraction from PDFs and images."""

import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR engine for extracting text from PDFs and images."""

    def __init__(
        self,
        engine: str = "tesseract",
        language: str = "eng",
        tesseract_config: str = "--oem 3 --psm 6",
    ) -> None:
        """Initialize OCR engine.
        
        Args:
            engine: OCR engine to use ('tesseract' or 'paddleocr')
            language: Language for OCR recognition
            tesseract_config: Tesseract configuration string
        """
        self.engine = engine.lower()
        self.language = language
        self.tesseract_config = tesseract_config
        
        # Initialize PaddleOCR if available and requested
        self.paddle_ocr = None
        if self.engine == "paddleocr":
            try:
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
                logger.info("PaddleOCR initialized successfully")
            except ImportError:
                logger.warning("PaddleOCR not available, falling back to Tesseract")
                self.engine = "tesseract"

    def extract_text(self, file_bytes: bytes, filename: str) -> Tuple[str, dict]:
        """Extract text from file bytes.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename for format detection
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        file_extension = Path(filename).suffix.lower()
        
        if file_extension == ".pdf":
            return self._extract_from_pdf(file_bytes, filename)
        elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]:
            return self._extract_from_image(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def _extract_from_pdf(self, pdf_bytes: bytes, filename: str) -> Tuple[str, dict]:
        """Extract text from PDF bytes."""
        metadata = {
            "filename": filename,
            "file_type": "pdf",
            "pages": 0,
            "ocr_engine": self.engine,
            "extraction_method": "unknown"
        }
        
        # First try to extract text directly from PDF
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            metadata["pages"] = len(reader.pages)
            
            direct_text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    direct_text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
            
            direct_text = "\n".join(direct_text_parts).strip()
            
            # Assess quality of direct extraction
            if direct_text:
                quality_score = self._assess_direct_text_quality(direct_text)
                logger.info(f"Direct PDF extraction: {len(direct_text)} chars, quality: {quality_score:.2f}")
                
                # Use direct text if it's good quality (much higher threshold)
                if quality_score > 0.7 and len(direct_text) > 200:
                    metadata["extraction_method"] = "direct"
                    metadata["quality_score"] = quality_score
                    logger.info(f"✅ Using direct PDF text extraction for {filename}")
                    return direct_text, metadata
                elif quality_score > 0.4 and len(direct_text) > 500:
                    # Lower quality but substantial text - still prefer direct
                    metadata["extraction_method"] = "direct"
                    metadata["quality_score"] = quality_score
                    logger.info(f"✅ Using direct PDF text extraction (lower quality) for {filename}")
                    return direct_text, metadata
                else:
                    logger.info(f"⚠️ Direct extraction quality too low ({quality_score:.2f}), trying OCR")
            else:
                logger.info(f"⚠️ No direct text found in PDF, trying OCR")
                
        except Exception as e:
            logger.warning(f"Direct PDF text extraction failed: {e}")
        
        # Fall back to OCR on PDF images
        logger.info(f"🔄 Falling back to OCR for {filename}")
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            metadata["extraction_method"] = "ocr"
            
            text_parts = []
            for page_num, image in enumerate(images):
                page_text = self._ocr_image(image)
                if page_text.strip():
                    text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")
                    
            ocr_text = "\n".join(text_parts)
            if ocr_text.strip():
                return ocr_text, metadata
            else:
                raise RuntimeError("OCR produced no readable text")
                    
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

    def _extract_from_image(self, image_bytes: bytes, filename: str) -> Tuple[str, dict]:
        """Extract text from image bytes."""
        metadata = {
            "filename": filename,
            "file_type": "image",
            "pages": 1,
            "ocr_engine": self.engine,
            "extraction_method": "ocr"
        }
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = self._ocr_image(image)
            return text, metadata
            
        except Exception as e:
            logger.error(f"Image OCR extraction failed: {e}")
            raise RuntimeError(f"Failed to extract text from image: {e}")

    def _ocr_image(self, image: Image.Image) -> str:
        """Perform OCR on a PIL image."""
        if self.engine == "paddleocr" and self.paddle_ocr:
            return self._paddle_ocr_image(image)
        else:
            return self._tesseract_ocr_image(image)

    def _tesseract_ocr_image(self, image: Image.Image) -> str:
        """Perform OCR using Tesseract."""
        try:
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
                
            text = pytesseract.image_to_string(
                image, 
                lang=self.language,
                config=self.tesseract_config
            )
            return text.strip()
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise RuntimeError(f"Tesseract OCR failed: {e}")

    def _paddle_ocr_image(self, image: Image.Image) -> str:
        """Perform OCR using PaddleOCR."""
        try:
            # Convert PIL image to format PaddleOCR expects
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                image.save(tmp_file.name, "PNG")
                tmp_path = tmp_file.name
            
            try:
                result = self.paddle_ocr.ocr(tmp_path, cls=True)
                
                # Extract text from PaddleOCR result
                text_parts = []
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) > 1:
                            text_parts.append(line[1][0])
                
                return "\n".join(text_parts)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            raise RuntimeError(f"PaddleOCR failed: {e}")

    def get_confidence_score(self, image: Image.Image) -> float:
        """Get OCR confidence score for an image."""
        if self.engine == "tesseract":
            try:
                data = pytesseract.image_to_data(
                    image, 
                    lang=self.language,
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                if confidences:
                    return sum(confidences) / len(confidences) / 100.0
                    
            except Exception as e:
                logger.warning(f"Failed to get confidence score: {e}")
                
        return 0.0

    def _assess_direct_text_quality(self, text: str) -> float:
        """Assess quality of directly extracted PDF text (0.0 = poor, 1.0 = excellent).
        
        Args:
            text: Extracted text to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Calculate metrics
        total_chars = len(text)
        alphanumeric = sum(1 for c in text if c.isalnum())
        spaces = text.count(' ')
        words = len(text.split())
        lines = text.count('\n')
        
        # Calculate ratios
        alpha_ratio = alphanumeric / total_chars if total_chars > 0 else 0
        space_ratio = spaces / total_chars if total_chars > 0 else 0
        avg_word_length = (alphanumeric / words) if words > 0 else 0
        
        # Check for common PDF extraction artifacts
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in 'àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ')
        weird_ratio = weird_chars / total_chars if total_chars > 0 else 0
        
        # Check for excessive repetition (common in OCR artifacts)
        repeated_chars = 0
        for i in range(1, len(text)):
            if text[i] == text[i-1] == ' ':  # Multiple spaces
                repeated_chars += 1
        repetition_ratio = repeated_chars / total_chars if total_chars > 0 else 0
        
        # Calculate quality score
        quality = 0.0
        
        # Good alphanumeric ratio (0.6-0.8 is typical for normal text)
        if 0.6 <= alpha_ratio <= 0.85:
            quality += 0.3
        elif 0.4 <= alpha_ratio < 0.6:
            quality += 0.2
        elif alpha_ratio > 0.85:
            quality += 0.1  # Too high might indicate missing spaces
        
        # Good space ratio (0.1-0.2 is typical)
        if 0.1 <= space_ratio <= 0.25:
            quality += 0.2
        elif 0.05 <= space_ratio < 0.1:
            quality += 0.1
        
        # Reasonable word length (3-8 characters average)
        if 3 <= avg_word_length <= 8:
            quality += 0.2
        elif 2 <= avg_word_length < 3 or 8 < avg_word_length <= 12:
            quality += 0.1
        
        # Low weird character ratio
        if weird_ratio < 0.05:
            quality += 0.2
        elif weird_ratio < 0.1:
            quality += 0.1
        
        # Low repetition ratio
        if repetition_ratio < 0.02:
            quality += 0.1
        
        # Bonus for substantial content
        if words > 50:
            quality += 0.1
        if words > 200:
            quality += 0.1
        
        return min(quality, 1.0)

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        import numpy as np
        from PIL import ImageEnhance, ImageFilter, ImageOps
        
        # Convert to RGB first to ensure proper processing
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        # Deskewing - detect and correct rotation
        image = OCREngine._deskew_image(image)
        
        # Convert to grayscale for processing
        if image.mode != "L":
            image = image.convert("L")
        
        # Noise reduction using median filter
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # Increase contrast by 50%
        
        # Sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        # Auto-adjust levels (similar to auto-levels in photo editing)
        image = ImageOps.autocontrast(image, cutoff=1)
        
        return image
    
    @staticmethod
    def _deskew_image(image: Image.Image) -> Image.Image:
        """Detect and correct image skew using Hough transform."""
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV format
            image_array = np.array(image)
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calculate the dominant angle
                angles = []
                for rho, theta in lines[:20]:  # Use first 20 lines
                    angle = theta * 180 / np.pi
                    # Convert to more intuitive angle range
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                # Find the most common angle (mode)
                if angles:
                    angle = np.median(angles)
                    
                                         # Only correct if angle is significant (> 0.5 degrees)
                    if abs(angle) > 0.5:
                        # Rotate the image
                        image = image.rotate(float(-angle), expand=True, fillcolor='white')
                        logger.info(f"Deskewed image by {angle:.2f} degrees")
            
        except ImportError:
            logger.debug("OpenCV not available, skipping deskewing")
        except Exception as e:
            logger.warning(f"Deskewing failed: {e}")
        
        return image
    
    @staticmethod
    def _enhance_for_ocr(image: Image.Image) -> Image.Image:
        """Apply additional enhancements specifically for OCR."""
        from PIL import ImageEnhance, ImageFilter, ImageOps
        
        # Adaptive threshold simulation using PIL
        # Convert to numpy for more advanced processing
        try:
            import numpy as np
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Apply adaptive threshold-like effect
            # Calculate local mean using a sliding window effect
            kernel_size = 15
            threshold_offset = 10
            
            # Simple local thresholding approximation
            # This creates a binary-like effect that helps with text recognition
            local_mean = np.ones_like(img_array) * np.mean(img_array)
            
            # Apply threshold
            binary = np.where(img_array > local_mean - threshold_offset, 255, 0)
            
            # Convert back to PIL
            image = Image.fromarray(binary.astype(np.uint8), mode='L')
            
        except ImportError:
            # Fallback to simpler PIL-only processing
            # Apply a simple threshold
            threshold = 128
            image = image.point(lambda p: 255 if p > threshold else 0)
            image = image.convert('L')
        
        return image 