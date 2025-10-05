import os
import google.generativeai as genai
from pathlib import Path
import PyPDF2

# Configure Gemini API
API_KEY = "AIzaSyBKMpPiof3mAPmy7_wUTLq6gJHwpvV2KdA"
genai.configure(api_key=API_KEY)

# Initialize the model with the best available model
model = genai.GenerativeModel('models/gemini-2.5-flash')

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")
        return None

def read_all_pdfs(folder_path):
    """Read all PDF files from the specified folder"""
    pdf_texts = {}
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder {folder_path} does not exist!")
        return pdf_texts
    
    pdf_files = list(folder.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return pdf_texts
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for pdf_file in pdf_files:
        print(f"Reading: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        if text:
            pdf_texts[pdf_file.name] = text
            print(f"✓ Successfully read {pdf_file.name} ({len(text)} characters)")
    
    return pdf_texts

def ask_question(pdf_texts, question):
    """Ask a question about the PDF contents using Gemini"""
    if not pdf_texts:
        return "No PDF content available to answer questions."
    
    # Combine all PDF texts with file names
    combined_context = ""
    for filename, text in pdf_texts.items():
        combined_context += f"\n\n=== Content from {filename} ===\n{text}"
    
    # Create the prompt
    prompt = f"""Based on the following PDF documents, please answer this question: {question}

PDF Contents:
{combined_context[:30000]}

Please provide a detailed and accurate answer based only on the information in these documents."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting response from Gemini: {str(e)}"

def main():
    # Folder path
    folder_path = r"C:\Users\Al-arab\Desktop\Nasa\Folders"
    
    print("=" * 60)
    print("PDF Reader with Gemini AI")
    print("=" * 60)
    print(f"\nReading PDFs from: {folder_path}\n")
    
    # Read all PDFs
    pdf_texts = read_all_pdfs(folder_path)
    
    if not pdf_texts:
        print("No PDFs were successfully loaded. Exiting.")
        return
    
    print(f"\n✓ Successfully loaded {len(pdf_texts)} PDF file(s)")
    print("\nFiles loaded:")
    for filename in pdf_texts.keys():
        print(f"  - {filename}")
    
    print("\n" + "=" * 60)
    print("You can now ask questions about the PDF content!")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 60 + "\n")
    
    # Question loop
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not question:
            print("Please enter a question.")
            continue
        
        print("\nThinking...")
        answer = ask_question(pdf_texts, question)
        print(f"\nAnswer:\n{answer}")
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()