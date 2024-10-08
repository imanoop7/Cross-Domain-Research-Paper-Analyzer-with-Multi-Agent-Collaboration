import autogen
import json
from typing import List, Dict, Tuple
import PyPDF2
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import gradio as gr
import time
import random
from groq import RateLimitError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_list = autogen.config_list_from_json("OAI_CONFIG_LIST.json")

# Create a base class for expert agents
class ExpertAgent(autogen.AssistantAgent):
    def __init__(self, name: str, system_message: str):
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config={
                "config_list": config_list,
                "temperature": 0,
                "request_timeout": 120,
            }
        )

# Create expert agents for specific parts of the research paper
introduction_expert = ExpertAgent("Introduction_Expert", "You are an expert in analyzing research paper introductions. Focus on the problem statement, research questions, and significance of the study.")
methodology_expert = ExpertAgent("Methodology_Expert", "You are an expert in research methodologies. Analyze the methods, experimental design, and data collection techniques used in the paper.")
results_expert = ExpertAgent("Results_Expert", "You are an expert in interpreting research results. Analyze the findings, statistical analyses, and data visualizations presented in the paper.")
discussion_expert = ExpertAgent("Discussion_Expert", "You are an expert in research paper discussions. Analyze the interpretation of results, implications, limitations, and future research directions.")
synthesis_expert = ExpertAgent("Synthesis_Expert", "You are an expert in synthesizing information from all parts of a research paper. Provide a cohesive analysis that highlights the key aspects and contributions of the study.")
parser_agent = ExpertAgent("Parser_Agent", "You are responsible for parsing and preprocessing the research paper. Parse the paper into sections (Introduction, Methodology, Results, Discussion) and handle any necessary preprocessing steps.")

# Modify the user_proxy agent to use Groq
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "paper_analysis", "use_docker": False},
    llm_config={
        "config_list": config_list,
        "temperature": 0,
        "request_timeout": 120,
    }
)

def retry_with_exponential_backoff(func, max_retries=5, initial_delay=1, max_delay=60):
    def wrapper(*args, **kwargs):
        retries = 0
        delay = initial_delay
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except (RateLimitError, Exception) as e:
                if retries == max_retries - 1:
                    raise
                wait_time = min(delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                logging.warning(f"Error occurred: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
    return wrapper

@retry_with_exponential_backoff
def safe_initiate_chat(agent, recipient, message):
    return agent.initiate_chat(recipient, message=message)

def load_pdf(file: gr.File) -> Tuple[str, Dict[int, str], str]:
    reader = PyPDF2.PdfReader(file.name)
    full_text = ""
    page_dict = {}
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        full_text += text
        page_dict[i] = text
    
    # Try to extract title from the first page
    title = "Untitled Research Paper"
    first_page_text = page_dict.get(0, "").strip()
    if first_page_text:
        # Assume the title is the first non-empty line
        lines = first_page_text.split('\n')
        for line in lines:
            if line.strip():
                title = line.strip()
                break
    
    return full_text, page_dict, title

def analyze_section(expert: ExpertAgent, section_name: str, section_content: str) -> str:
    logging.info(f"Analyzing {section_name} with {expert.name}")
    return safe_initiate_chat(user_proxy, expert, f"Analyze the {section_name} section:\n\n{section_content}")

def parallel_analysis(experts: List[ExpertAgent], sections: Dict[str, str]) -> Dict[str, str]:
    with ThreadPoolExecutor() as executor:
        future_to_section = {executor.submit(analyze_section, expert, section_name, content): section_name
                             for expert, (section_name, content) in zip(experts, sections.items())}
        results = {}
        for future in as_completed(future_to_section):
            section_name = future_to_section[future]
            results[section_name] = future.result()
    return results

def analyze_paper(paper_content: str, page_dict: Dict[int, str]) -> Dict[str, str]:
    groupchat = autogen.GroupChat(
        agents=[user_proxy, parser_agent, introduction_expert, methodology_expert, results_expert, discussion_expert, synthesis_expert],
        messages=[],
        max_round=50
    )
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={
            "config_list": config_list,
            "temperature": 0,
            "request_timeout": 120,
        }
    )

    # Parse the paper into sections
    parsing_result = safe_initiate_chat(
        user_proxy,
        parser_agent,
        f"Parse this paper into sections (Introduction, Methodology, Results, Discussion):\n\n{paper_content}"
    )
    sections = json.loads(parsing_result)  # Assume parser_agent returns a JSON string

    # Analyze sections in parallel
    section_analyses = parallel_analysis(
        [introduction_expert, methodology_expert, results_expert, discussion_expert],
        sections
    )

    # Synthesize the analyses
    synthesis_prompt = "Synthesize the following analyses into a comprehensive review:\n\n"
    for section, analysis in section_analyses.items():
        synthesis_prompt += f"{section}:\n{analysis}\n\n"
    
    final_synthesis = safe_initiate_chat(user_proxy, synthesis_expert, synthesis_prompt)

    # Generate a summary for each page
    page_summaries = {}
    for page_num, page_content in page_dict.items():
        summary = safe_initiate_chat(
            user_proxy,
            synthesis_expert,
            f"Summarize this page content in one sentence:\n\n{page_content}"
        )
        page_summaries[page_num] = summary

    return {
        "section_analyses": section_analyses,
        "final_synthesis": final_synthesis,
        "page_summaries": page_summaries
    }

def save_analysis(paper_title: str, analysis: Dict[str, str]):
    output_dir = "analysis_results"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"{paper_title}_analysis.json"), "w") as f:
        json.dump(analysis, f, indent=2)

def load_analysis(paper_title: str) -> Dict[str, str]:
    with open(os.path.join("analysis_results", f"{paper_title}_analysis.json"), "r") as f:
        return json.load(f)

def analyze_and_save(file: gr.File) -> Dict[str, str]:
    logging.info(f"Loading PDF: {file.name}")
    paper_content, page_dict, paper_title = load_pdf(file)

    logging.info("Analyzing paper")
    result = analyze_paper(paper_content, page_dict)

    logging.info("Saving analysis")
    save_analysis(paper_title, result)

    return result

def gradio_interface(file: gr.File) -> str:
    result = analyze_and_save(file)
    return json.dumps(result, indent=2)

# Create Gradio interface
iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.File(label="Upload Research Paper PDF")
    ],
    outputs=gr.Textbox(label="Analysis Result"),
    title="Research Paper Analyzer",
    description="Upload a research paper PDF and get an in-depth analysis."
)

if __name__ == "__main__":
    iface.launch()