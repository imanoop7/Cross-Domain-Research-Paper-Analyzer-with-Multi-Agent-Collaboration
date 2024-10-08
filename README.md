# Research Paper Analyzer with Multi-Agent Collaboration

## Project Overview

This project implements a Research Paper Analyzer that leverages multi-agent collaboration to analyze research papers. The system uses various expert agents to break down and analyze different sections of a research paper, providing a comprehensive analysis.

## Key Features

- Multi-agent system for distributed analysis
- PDF parsing and text extraction
- Section-specific expert analysis (Introduction, Methodology, Results, Discussion)
- Synthesis of individual analyses
- Page-by-page summary generation
- Gradio web interface for easy paper upload and analysis

## System Components

1. Expert Agents:
   - Introduction Expert
   - Methodology Expert
   - Results Expert
   - Discussion Expert
   - Synthesis Expert
   - Parser Agent

2. PDF Processing: Using PyPDF2 for text extraction
3. Parallel Analysis: Concurrent processing of paper sections
4. Error Handling: Exponential backoff for API rate limiting
5. Result Storage: JSON-based storage of analysis results

## Getting Started

### Prerequisites

- Python 3.8+
- Groq API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/imanoop7/Research-Paper-Analyzer-with-Multi-Agent-Collaboration
   cd cross-domain-research-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys in the `OAI_CONFIG_LIST.json` file. Here are sample configurations for different providers:

   ```json
   [
     {
       "name": "groq",
       "api_key": "your_groq_api_key_here",
       "api_base": "https://api.groq.com/v1",
       "api_type": "groq",
       "model": "llama-3.1-8b-instant",
       "temperature": 0
     },
     {
       "name": "openai",
       "api_key": "your_openai_api_key_here",
       "api_base": "https://api.openai.com/v1",
       "api_type": "openai",
       "model": "gpt-4-turbo-preview",
       "temperature": 0
     },
     {
       "name": "ollama",
       "api_base": "http://localhost:11434",
       "api_type": "ollama",
       "model": "llama2",
       "temperature": 0
     },
     {
       "name": "gemini",
       "api_key": "your_gemini_api_key_here",
       "api_base": "https://generativelanguage.googleapis.com/v1beta",
       "api_type": "gemini",
       "model": "gemini-pro",
       "temperature": 0
     }
   ]
   ```

   Replace `"your_*_api_key_here"` with your actual API keys for each service. Note that Ollama typically runs locally and doesn't require an API key.

4. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Launch the application to start the Gradio interface.
2. Upload a research paper PDF through the web interface.
3. The system will analyze the paper and return a JSON object containing:
   - Section-specific analyses
   - A final synthesis of the entire paper
   - Page-by-page summaries

## Configuration

The `OAI_CONFIG_LIST.json` file contains the configuration for the Groq API. Ensure your API key is correctly set in this file.

## Dependencies

- autogen: For creating and managing AI agents
- PyPDF2: For PDF parsing and text extraction
- gradio: For creating the web interface
- groq: For interacting with the Groq API

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

Contributions are welcome! Please feel free to submit a Pull Request.
