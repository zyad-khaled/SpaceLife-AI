from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from pathlib import Path
import PyPDF2

app = Flask(__name__)
CORS(app)

# Configure Gemini API
API_KEY = "AIzaSyBKMpPiof3mAPmy7_wUTLq6gJHwpvV2KdA"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

# Global variables
pdf_texts = {}
PDF_FOLDER = r"C:\Users\Al-arab\Desktop\Nasa\backend\data"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            pages = len(pdf_reader.pages)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text, pages
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")
        return None, 0

def load_all_pdfs():
    """Load all PDF files from the data folder"""
    global pdf_texts
    pdf_texts = {}
    folder = Path(PDF_FOLDER)
    
    if not folder.exists():
        print(f"Error: Folder {PDF_FOLDER} does not exist!")
        return
    
    pdf_files = list(folder.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {PDF_FOLDER}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for pdf_file in pdf_files:
        print(f"Reading: {pdf_file.name}")
        text, pages = extract_text_from_pdf(pdf_file)
        if text:
            pdf_texts[pdf_file.name] = {
                'text': text,
                'pages': pages,
                'size': len(text)
            }
            print(f"✓ Successfully read {pdf_file.name} ({len(text)} characters, {pages} pages)")

# Load PDFs when server starts
load_all_pdfs()

@app.route('/api/pdfs', methods=['GET'])
def get_pdfs():
    """Get list of all loaded PDF files"""
    pdf_list = [
        {
            'name': name,
            'pages': info['pages'],
            'size': info['size']
        }
        for name, info in pdf_texts.items()
    ]
    return jsonify({
        'success': True,
        'pdfs': pdf_list,
        'count': len(pdf_list)
    })

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Ask a question about the PDF contents with advanced AI modes"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        mode = data.get('mode', 'normal')
        selected_pdfs = data.get('selected_pdfs', [])
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        # Handle casual conversation
        casual_greetings = ['hi', 'hello', 'hey', 'how are you', 'whats up', "what's up", 'good morning', 'good afternoon', 'good evening']
        question_lower = question.lower()
        
        if any(greeting in question_lower for greeting in casual_greetings):
            greeting_responses = {
                'answer': """Hello! I'm doing great, thank you for asking! 

I'm your AI document analysis assistant, and I'm here to help you understand and explore your PDF documents. 

**Here's what I can do for you:**

• **Summarize documents** - Get quick overviews of lengthy PDFs
• **Find connections** - Discover relationships between different documents
• **Extract insights** - Identify key findings and important information
• **Answer questions** - Get specific information from your documents

Feel free to ask me anything about your documents, or use the quick action buttons above to get started!""",
                'sources': [],
                'mode': 'casual'
            }
            return jsonify({
                'success': True,
                'answer': greeting_responses['answer'],
                'sources': greeting_responses['sources'],
                'question': question,
                'mode': greeting_responses['mode']
            })
        
        if not pdf_texts:
            return jsonify({
                'success': False,
                'error': 'No PDF content available'
            }), 400
        
        # Filter to selected PDFs
        pdfs_to_use = selected_pdfs if selected_pdfs else list(pdf_texts.keys())
        
        if not pdfs_to_use:
            return jsonify({
                'success': False,
                'error': 'No documents selected'
            }), 400
        
        # Combine selected PDF texts
        combined_context = ""
        sources = []
        
        for filename in pdfs_to_use:
            if filename in pdf_texts:
                info = pdf_texts[filename]
                combined_context += f"\n\n=== Document: {filename} ===\n{info['text']}"
                sources.append(filename)
        
        # Limit context to avoid token limits
        if len(combined_context) > 30000:
            combined_context = combined_context[:30000]
        
        # Create mode-specific prompts
        if mode == 'analysis':
            system_prompt = """You are an advanced AI research assistant specializing in document analysis.
Your task is to provide deep insights, find patterns, and make intelligent connections between documents.
Focus on:
- Identifying key themes and patterns across documents
- Finding relationships and connections between different topics
- Extracting meaningful insights and observations
- Highlighting contradictions or complementary information
- Suggesting new perspectives or research directions"""
        
        elif mode == 'summary':
            system_prompt = """You are an AI summarization expert.
Provide comprehensive yet concise summaries that capture:
- Main topics and key points from each document
- Important findings and conclusions
- Critical data and statistics
- Overall themes across all documents"""
        
        else:  # normal mode
            system_prompt = """You are a helpful AI assistant that answers questions about PDF documents.
Provide accurate, detailed answers based strictly on the document content.
If referencing specific information, mention which document it comes from."""
        
        # Create the full prompt
        prompt = f"""{system_prompt}

Question: {question}

Documents Content:
{combined_context}

Please provide a detailed and accurate response."""
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'answer': response.text,
            'sources': sources,
            'question': question,
            'mode': mode
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_documents():
    """Advanced document analysis endpoint"""
    try:
        data = request.get_json()
        analysis_type = data.get('type', 'connections')  # connections, insights, themes
        
        if not pdf_texts:
            return jsonify({
                'success': False,
                'error': 'No PDF content available'
            }), 400
        
        combined_context = ""
        for filename, info in pdf_texts.items():
            combined_context += f"\n\n=== {filename} ===\n{info['text']}"
        
        if len(combined_context) > 30000:
            combined_context = combined_context[:30000]
        
        prompts = {
            'connections': """Analyze all documents and identify:
1. Key connections and relationships between different documents
2. Common themes and patterns
3. Complementary or contradictory information
4. How concepts from one document relate to another
5. Potential research directions based on these connections""",
            
            'insights': """Extract and present:
1. The most important insights from each document
2. Novel findings or unique perspectives
3. Critical data points and their significance
4. Actionable takeaways
5. Areas requiring further investigation""",
            
            'themes': """Identify and analyze:
1. Major themes across all documents
2. How these themes are developed in each document
3. Recurring concepts and ideas
4. Theme evolution and relationships
5. Implications of these themes"""
        }
        
        prompt = f"""{prompts.get(analysis_type, prompts['connections'])}

Documents:
{combined_context}"""
        
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'analysis': response.text,
            'type': analysis_type,
            'documents_analyzed': len(pdf_texts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/reload', methods=['POST'])
def reload_pdfs():
    """Reload all PDF files from the folder"""
    try:
        load_all_pdfs()
        return jsonify({
            'success': True,
            'message': f'Successfully reloaded {len(pdf_texts)} PDF files',
            'count': len(pdf_texts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'pdfs_loaded': len(pdf_texts),
        'api_configured': API_KEY is not None
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Enhanced PDF AI Assistant Backend',
        'version': '2.0',
        'features': [
            'Multi-document analysis',
            'Connection finding',
            'Advanced insights',
            'Context-aware responses',
            'Save for later functionality'
        ],
        'endpoints': {
            '/api/pdfs': 'GET - List all PDFs',
            '/api/ask': 'POST - Ask questions (supports modes: normal, analysis, summary)',
            '/api/analyze': 'POST - Advanced analysis (types: connections, insights, themes)',
            '/api/reload': 'POST - Reload PDFs',
            '/api/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Enhanced PDF AI Assistant Backend Server v2.0")
    print("=" * 60)
    print(f"\nPDF Folder: {PDF_FOLDER}")
    print(f"Loaded PDFs: {len(pdf_texts)}")
    print("\n✨ New Features:")
    print("  - Advanced document analysis")
    print("  - Connection finding between documents")
    print("  - Multiple AI modes (normal, analysis, summary)")
    print("  - Enhanced context understanding")
    print("\nServer starting on http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)