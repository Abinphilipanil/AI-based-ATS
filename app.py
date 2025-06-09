from unicodedata import category
import streamlit as st
import google.generativeai as genai
import os
import docx2txt
import PyPDF2 as pdf 
from dotenv import load_dotenv 

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("google_api_key"))

generation_config = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

def generate_response_from_gemini(input_text):
    try:
        llm = genai.GenerativeModel(
    model_name="gemini-1.0-pro",  # Updated model name
    generation_config=generation_config,
    safety_settings=safety_settings,
)
        output = llm.generate_content(input_text)
        return output.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def extract_text_from_pdf_file(uploaded_file):
    try:
        pdf_reader = pdf.PdfReader(uploaded_file)
        return "".join(page.extract_text() or "" for page in pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_text_from_docx_file(uploaded_file):
    try:
        return docx2txt.process(uploaded_file)
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

input_prompt_template = """
As an experienced Application Tracking System (ATS) analyst,
your task is to evaluate the resume against the provided job description.
Please provide:

1. Match percentage (0-100%)
2. Missing keywords/skills
3. Candidate summary
4. Recommendations for improvement

Resume:
{text}

Job Description:
{job_description}

Format your response with clear headings for each section.
"""

# Streamlit UI
st.title("Intelligent ATS - Resume Analyzer")
st.markdown('<style>h1{color: orange; text-align: center;}</style>', unsafe_allow_html=True)

job_description = st.text_area("Paste the Job Description", height=300)
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"], 
                               help="Please upload a PDF or DOCX file")

if st.button("Analyze Resume"):
    if not job_description:
        st.warning("Please enter a job description")
    elif uploaded_file is None:
        st.warning("Please upload a resume file")
    else:
        with st.spinner("Analyzing resume..."):
            try:
                # Extract text based on file type
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf_file(uploaded_file)
                else:
                    resume_text = extract_text_from_docx_file(uploaded_file)
                
                if not resume_text:
                    st.error("Could not extract text from the file")
                
                
                # Generate response
                prompt = input_prompt_template.format(
                    text=resume_text,
                    job_description=job_description
                )
                
                response_text = generate_response_from_gemini(prompt)
                
                if response_text:
                    st.subheader("ATS Evaluation Results")
                    st.markdown(response_text)
                    
                    # Try to extract percentage (more flexible approach)
                    if "%" in response_text:
                        percentage_str = response_text.split("%")[0][-3:].strip()
                        try:
                            match_percentage = float(percentage_str)
                            if match_percentage >= 80:
                                st.success("✅ Strong match - Recommend proceeding")
                            elif match_percentage >= 60:
                                st.warning("⚠️ Moderate match - Consider with improvements")
                            else:
                                st.error("❌ Low match - Not recommended")
                        except ValueError:
                            pass
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
