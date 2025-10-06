from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from pathlib import Path
import PyPDF2
import json

app = Flask(__name__)
CORS(app)

# Configure Gemini API
API_KEY = "AIzaSyBKMpPiof3mAPmy7_wUTLq6gJHwpvV2KdA"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

# Global variables
pdf_texts = {}
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('pdf_folder', get_default_pdf_folder())
        except:
            pass
    return get_default_pdf_folder()

def save_config(pdf_folder):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'pdf_folder': pdf_folder}, f)
        return True
    except:
        return False

def get_default_pdf_folder():
    """Get default PDF folder"""
    # المسار المحدد للـ PDFs
    default_folder = r"C:\Users\Al-arab\Desktop\Nasa\backend\data"
    
    # لو المجلد مش موجود، حاول تعمله
    if not os.path.exists(default_folder):
        try:
            os.makedirs(default_folder)
            print(f"Created folder: {default_folder}")
        except Exception as e:
            print(f"Could not create folder: {e}")
            # استخدم المجلد الحالي كبديل
            default_folder = os.path.join(os.getcwd(), 'data')
            if not os.path.exists(default_folder):
                os.makedirs(default_folder)
    
    return default_folder

# Load PDF folder from config or use default
PDF_FOLDER = load_config()

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

def load_all_pdfs(folder_path=None):
    """Load all PDF files from the specified folder"""
    global pdf_texts, PDF_FOLDER
    
    if folder_path:
        PDF_FOLDER = folder_path
        save_config(PDF_FOLDER)
    
    pdf_texts = {}
    folder = Path(PDF_FOLDER)
    
    if not folder.exists():
        print(f"Creating folder: {PDF_FOLDER}")
        folder.mkdir(parents=True, exist_ok=True)
        return 0
    
    # Search for PDFs recursively
    pdf_files = list(folder.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {PDF_FOLDER}")
        return 0
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for pdf_file in pdf_files:
        print(f"Reading: {pdf_file.name}")
        text, pages = extract_text_from_pdf(pdf_file)
        if text:
            pdf_texts[pdf_file.name] = {
                'text': text,
                'pages': pages,
                'size': len(text),
                'path': str(pdf_file)
            }
            print(f"✓ Successfully read {pdf_file.name} ({len(text)} characters, {pages} pages)")
    
    return len(pdf_texts)

# Load PDFs when server starts
load_all_pdfs()

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'success': True,
        'pdf_folder': PDF_FOLDER,
        'pdfs_loaded': len(pdf_texts)
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update PDF folder path"""
    try:
        data = request.get_json()
        new_folder = data.get('pdf_folder', '').strip()
        
        if not new_folder:
            return jsonify({
                'success': False,
                'error': 'PDF folder path is required'
            }), 400
        
        # Validate path
        if not os.path.exists(new_folder):
            return jsonify({
                'success': False,
                'error': f'Folder does not exist: {new_folder}'
            }), 400
        
        # Load PDFs from new folder
        count = load_all_pdfs(new_folder)
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {count} PDFs from new folder',
            'pdf_folder': PDF_FOLDER,
            'count': count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pdfs', methods=['GET'])
def get_pdfs():
    """Get list of all loaded PDF files"""
    pdf_list = [
        {
            'name': name,
            'pages': info['pages'],
            'size': info['size'],
            'path': info.get('path', '')
        }
        for name, info in pdf_texts.items()
    ]
    return jsonify({
        'success': True,
        'pdfs': pdf_list,
        'count': len(pdf_list),
        'folder': PDF_FOLDER
    })

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Ask a question about the PDF contents"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        mode = data.get('mode', 'normal')
        selected_pdfs = data.get('selected_pdfs', [])
        
        print(f"\n{'='*60}")
        print(f"New Question Received:")
        print(f"Question: {question}")
        print(f"Mode: {mode}")
        print(f"Selected PDFs: {selected_pdfs}")
        print(f"{'='*60}\n")
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        if not pdf_texts:
            return jsonify({
                'success': False,
                'error': 'No PDF files loaded. Please add PDFs to your folder and reload.'
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
                combined_context += f"\n\n=== Document: {filename} ===\n{info['text'][:10000]}"  # Limit per doc
                sources.append(filename)
        
        if not combined_context.strip():
            return jsonify({
                'success': False,
                'error': 'No content found in selected documents'
            }), 400
        
        # Limit total context
        if len(combined_context) > 30000:
            combined_context = combined_context[:30000]
        
        print(f"Context length: {len(combined_context)} characters")
        print(f"Sources: {sources}")
        
        # Create mode-specific prompts
        if mode == 'analysis':
            system_prompt = """You are an advanced AI research assistant specializing in document analysis.
Provide deep insights, find patterns, and make intelligent connections between documents.
Answer in Arabic if the question is in Arabic, otherwise answer in English."""
        
        elif mode == 'summary':
            system_prompt = """You are an AI summarization expert.
Provide comprehensive yet concise summaries.
Answer in Arabic if the question is in Arabic, otherwise answer in English."""
        
        else:  # normal mode
            system_prompt = """You are a helpful AI assistant that answers questions about documents.
Provide accurate, detailed answers based on the document content.
Answer in Arabic if the question is in Arabic, otherwise answer in English.
If you cannot find the answer in the documents, say so clearly."""
        
        # Create the full prompt
        prompt = f"""{system_prompt}

Question: {question}

Documents Content:
{combined_context}

Please provide a detailed and accurate response based ONLY on the information in these documents."""
        
        print("Sending to Gemini AI...")
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        answer = response.text
        print(f"\nResponse generated: {len(answer)} characters")
        
        return jsonify({
            'success': True,
            'answer': answer,
            'sources': sources,
            'question': question,
            'mode': mode
        })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing question: {str(e)}'
        }), 500

@app.route('/api/reload', methods=['POST'])
def reload_pdfs():
    """Reload all PDF files from the current folder"""
    try:
        count = load_all_pdfs()
        return jsonify({
            'success': True,
            'message': f'Successfully reloaded {count} PDF files',
            'count': count,
            'folder': PDF_FOLDER
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
        'pdf_folder': PDF_FOLDER,
        'api_configured': API_KEY is not None
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Enhanced PDF AI Assistant Backend',
        'version': '3.0',
        'current_folder': PDF_FOLDER,
        'pdfs_loaded': len(pdf_texts),
        'features': [
            'Flexible PDF folder configuration',
            'Multi-document analysis',
            'Arabic & English support',
            'Context-aware responses'
        ],
        'endpoints': {
            '/api/config': 'GET/POST - View/Update PDF folder',
            '/api/pdfs': 'GET - List all PDFs',
            '/api/ask': 'POST - Ask questions',
            '/api/reload': 'POST - Reload PDFs',
            '/api/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    print("=" * 70)
    print("Enhanced PDF AI Assistant Backend Server v3.0")
    print("=" * 70)
    print(f"\nCurrent PDF Folder: {PDF_FOLDER}")
    print(f"Loaded PDFs: {len(pdf_texts)}")
    
    if pdf_texts:
        print("\nLoaded documents:")
        for name in pdf_texts.keys():
            print(f"  - {name}")
    else:
        print("\n⚠ No PDFs found. Add PDFs to your folder and use /api/reload")
    
    print("\n✨ Features:")
    print("  - Flexible folder configuration")
    print("  - Arabic & English support")
    print("  - Enhanced error handling")
    print("  - Detailed logging")
    
    print(f"\nServer starting on http://localhost:5000")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)