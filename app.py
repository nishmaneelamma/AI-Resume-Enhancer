import streamlit as st
import streamlit.components.v1 as components
import PyPDF2
import google.generativeai as genai
import json
import os
import pdf_templates
import db

# --- Initialize Database ---
db.init_db()

# --- Page Configuration ---
st.set_page_config(page_title="AI Resume Enhancer", page_icon="✨", layout="wide")

st.title("AI Resume Enhancer ✨")
st.markdown("Upload your resume and a job description to extract and enhance your resume using **Gemini 2.5 Flash**.")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("Navigation")
    app_mode = st.radio("Go to Option:", ["Enhancer", "Database Review"])
    st.divider()

    st.header("Configuration")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key here")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        genai.configure(api_key=api_key_input)
        st.success("API Key loaded from input!")
    elif "GEMINI_API_KEY" in os.environ:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        st.success("API Key loaded from environment variables!")
    else:
        st.warning("Please enter your Gemini API key to proceed.")
        st.write("You can get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).")

# --- Helper Functions ---
def extract_text_from_pdf(pdf_file):
    """Extracts text from the uploaded PDF document."""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for i, page in enumerate(reader.pages):
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def parse_resume(raw_text):
    """Uses Gemini 2.5 Flash to structure the resume into JSON format."""
    prompt = f"""
    You are an expert resume parser. Analyze the provided resume text and dynamically identify EVERY logical section present (e.g., Summary, Work Experience, Education, Skills, Projects, Certifications, Publications, Languages, Hobbies, etc.).
    
    Return the information strictly as a valid JSON object where the keys are the exact names of the sections you found in the resume, and the values are detailed strings or lists containing the content of those sections. 
    Do not include any formatting, markdown markers, or other outside text. Just the JSON.
    Make sure to capture EVERYTHING mentioned in the resume under an appropriate section key.
    
    Resume Text:
    {raw_text}
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
            request_options={"timeout": 120} 
        )
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse resume into structured JSON. Falling back to raw response.")
        return {"Raw Response": getattr(response, 'text', str(e))}
    except Exception as e:
        st.error(f"Error in Gemini API: {e}")
        return {}

def calculate_ats_score(resume_data, job_description):
    """Calculates an ATS score and identifies missing keywords."""
    prompt = f"""
    You are an expert Applicant Tracking System (ATS).
    Compare the following Resume JSON Data against the provided Job Description.
    
    Resume JSON:
    {json.dumps(resume_data, indent=2)}
    
    Job Description:
    {job_description}
    
    Perform a strict evaluation and return ONLY a valid JSON object exactly with the following structure:
    {{
      "ATS_Score": 65,
      "Matching_Keywords": ["Python", "SQL", "Agile"],
      "Missing_Keywords": ["AWS", "Docker", "CI/CD"],
      "Feedback": "Brief 1-2 sentence advice on how to improve."
    }}
    (Note: ATS_Score must be an integer between 0 and 100).
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
            request_options={"timeout": 60} 
        )
        return json.loads(response.text)
    except Exception as e:
        return {"ATS_Score": 0, "Matching_Keywords": [], "Missing_Keywords": [], "Feedback": f"Error: {e}"}

def enhance_all_sections(parsed_resume_dict, job_description):
    """Uses Gemini 2.5 Flash to rewrite all valid sections in one pass based on a Job Description."""
    prompt = f"""
    You are an expert career coach and resume writer. 
    I have a candidate's resume presented as a JSON dictionary below.
    
    --- Current Resume JSON ---
    {json.dumps(parsed_resume_dict, indent=2)}
    -----------------------------
    
    I also have a Job Description that the candidate is applying for:
    
    --- Job Description ---
    {job_description}
    -----------------------
    
    CRITICAL INSTRUCTION:
    Go through the candidate's profile and the Job Description.
    1. You MUST extract a top-level key "Name" containing just the candidate's exact full name.
    2. You MUST extract a top-level key "Title" containing the candidate's professional job title.
    3. You MUST consolidate all contact info (phone, email, portfolio links) under a "Contact" key.
    4. If a section represents fixed, factual information (such as "Contact", "Awards", "Certifications", "Achievements", or "Education names"), return its content unmodified.
    5. For descriptive sections (like Summary, Experience, Projects), your absolute primary goal is to MAXIMIZE the ATS Match Score for the Job Description.
       - Identify ALL key skills, technologies, and buzzwords required from the Job Description.
       - You MUST completely, creatively, and seamlessly weave these job description keywords into the candidate's Summary, Experience, and Projects sections. 
       - Reframe their past experience to logically align with the target role and ensure a very high ATS match.
       - Make the tone impactful, professional, and entirely tailored to the JD requirements.
    6. GUARANTEE ATS PASS: You MUST aggressively update the candidate's "Skills" section (or CREATE a new top-level "Skills" key if one doesn't exist). Explicitly list all the missing technical skills, tools, and keywords required by the Job Description here so the ATS score reaches 100%.
       
    Return the information strictly as a valid JSON object. You are ALLOWED and ENCOURAGED to add new keys (like "Skills") if it improves the ATS score. Do not include any HTML or markdown formatting inside the text except where necessary for structure (like creating lists). Just return the JSON object.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
            request_options={"timeout": 120}
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error enhancing resume: {e}")
        return parsed_resume_dict

# --- Main Application Logic ---

if app_mode == "Enhancer":
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.header("1. Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF resume", type=["pdf"])
        
        # Initialize session state variables safely
        if 'resume_text' not in st.session_state:
            st.session_state['resume_text'] = ""
        if 'parsed_resume' not in st.session_state:
            st.session_state['parsed_resume'] = None
    
        if uploaded_file is not None:
            if st.button("Extract & Structure Resume", type="primary", use_container_width=True):
                if "GEMINI_API_KEY" not in os.environ and not api_key_input:
                    st.error("Please provide a Gemini API key in the sidebar first.")
                else:
                    with st.spinner("Extracting text and analyzing with Gemini 2.5 Flash..."):
                        # Clear old session data when a new resume is processed
                        st.session_state.pop('original_ats_results', None)
                        st.session_state.pop('enhanced_ats_results', None)
                        st.session_state.pop('enhanced_resume_dict', None)
                        
                        st.session_state['resume_text'] = extract_text_from_pdf(uploaded_file)
                        
                        if st.session_state['resume_text']:
                            st.session_state['parsed_resume'] = parse_resume(st.session_state['resume_text'])
                            
                            # --- Save to Database ---
                            try:
                                candidate_name = st.session_state['parsed_resume'].get("Name", "Unknown Candidate")
                                # Fallback to looking for variants if Name is missing
                                if candidate_name == "Unknown Candidate":
                                    for key in ["Candidate Name", "FullName", "Full Name", "First Name"]:
                                        if key in st.session_state['parsed_resume']:
                                            candidate_name = st.session_state['parsed_resume'][key]
                                            break

                                record_id = db.create_resume_record(
                                    candidate_name=candidate_name,
                                    original_text=st.session_state['resume_text'],
                                    parsed_json=st.session_state['parsed_resume']
                                )
                                st.session_state['current_record_id'] = record_id
                                st.success("Resume Extracted & Structured Successfully! (Saved to Database)")
                            except Exception as e:
                                st.warning(f"Extracted but failed to save to Database: {e}")
                                
                        else:
                            st.warning("No text could be extracted from the PDF.")
    
    with col2:
        st.header("2. Provide Job Description")
        job_desc = st.text_area("Paste the target Job Description here", height=120)
        
        # New ATS functionality logic
        if st.session_state.get('parsed_resume') and job_desc:
            st.write("") # Add simple spacing
            if st.button("🔍 Calculate Original ATS Match", type="secondary", use_container_width=True):
                with st.spinner("Analyzing JD against your original resume..."):
                    ats_results = calculate_ats_score(st.session_state['parsed_resume'], job_desc)
                    st.session_state['original_ats_results'] = ats_results
                    
                    # Update DB
                    if 'current_record_id' in st.session_state:
                        db.update_original_ats(st.session_state['current_record_id'], ats_results.get("ATS_Score", 0))

    if st.session_state.get('parsed_resume'):
        st.divider()
        res_col1, res_col2 = st.columns(2, gap="large")
        
        with res_col1:
            st.subheader("📝 Extracted Dictionary")
            with st.expander("View Extracted Sections", expanded=False):
                for key, val in st.session_state['parsed_resume'].items():
                    st.text_area(f"Original {key}", value=str(val), height=100, disabled=True, key=f"orig_disp_{key}")
                    
        with res_col2:
            st.subheader("🎯 ATS Match Analysis")
            # Display original ATS results if they exist
            if 'original_ats_results' in st.session_state:
                res = st.session_state['original_ats_results']
                score = res.get('ATS_Score', 0)
                
                # Check performance based on standard ATS parameters
                color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                st.markdown(f"### <span style='color:{color}'>Original ATS Match: {score}%</span>", unsafe_allow_html=True)
                
                with st.expander("View ATS Insights", expanded=True):
                    st.write(f"**Feedback:** {res.get('Feedback', '')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Matching Keywords:**")
                        for kw in res.get('Matching_Keywords', []):
                            st.write(f"✅ {kw}")
                    with c2:
                        st.write("**Missing Keywords:**")
                        for kw in res.get('Missing_Keywords', []):
                            st.write(f"❌ {kw}")
            else:
                st.info("Input a Job Description to the right and click 'Calculate Original ATS Match' to see your score.")
    
    st.divider()
    
    # --- Enhancement Execution ---
    if st.session_state.get('parsed_resume') and job_desc:
        st.header("3. Enhance & Compare")
        st.write("Click below to enhance your entire resume, effectively raising your ATS score by addressing the Missing Keywords!")
        
        if st.button("✨ Enhance Resume with Gemini 2.5 Flash ✨", type="primary"):
            # Step 1: Rewrite Sections
            with st.spinner("Rewriting your entire resume with Gemini in one pass..."):
                st.session_state['enhanced_resume_dict'] = enhance_all_sections(st.session_state['parsed_resume'], job_desc)
                
            # Step 2: Calculate New Ats Score
            with st.spinner("Calculating Enhanced ATS Match Score..."):
                enh_ats_results = calculate_ats_score(st.session_state['enhanced_resume_dict'], job_desc)
                st.session_state['enhanced_ats_results'] = enh_ats_results
                
                # Update Database!
                if 'current_record_id' in st.session_state:
                    try:
                        db.update_resume_record(
                            record_id=st.session_state['current_record_id'],
                            job_description=job_desc,
                            enhanced_json=st.session_state['enhanced_resume_dict']
                        )
                        db.update_enhanced_ats(st.session_state['current_record_id'], enh_ats_results.get("ATS_Score", 0))
                        st.success("Enhancement Complete! (Database Updated)")
                    except Exception as e:
                        st.warning(f"Enhancement successful, but failed to update Database: {e}")
                else:
                    st.success("Enhancement Complete!")
                
        # Display Enhanced ATS Score side-by-side with original if enhancement happened
        if st.session_state.get('enhanced_ats_results'):
            enh_res = st.session_state['enhanced_ats_results']
            enh_score = enh_res.get('ATS_Score', 0)
            orig_score = st.session_state.get('original_ats_results', {}).get('ATS_Score', 0)
            
            st.divider()
            st.subheader("ATS Match Score Comparison")
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Original Resume", f"{orig_score}%")
            mc2.metric("✨ Enhanced Resume", f"{enh_score}%", delta=f"{enh_score - orig_score}%")
            
            with st.expander("View Enhanced ATS Insights", expanded=True):
                st.write(f"**Feedback:** {enh_res.get('Feedback', '')}")
                ec1, ec2 = st.columns(2)
                with ec1:
                    st.write("**Matching Keywords:**")
                    for kw in enh_res.get('Matching_Keywords', []):
                        st.write(f"✅ {kw}")
                with ec2:
                    st.write("**Missing Keywords (Remaining):**")
                    if enh_res.get('Missing_Keywords', []):
                        for kw in enh_res.get('Missing_Keywords', []):
                            st.write(f"⚠️ {kw}")
                    else:
                        st.write("🎉 None! Excellent Match!")

        # Display Before & After Content side-by-side for each key
        if st.session_state.get('enhanced_resume_dict'):
            enhanced_resume_dict = st.session_state['enhanced_resume_dict']
            
            def format_for_display(data):
                if isinstance(data, dict):
                    lines = []
                    for k, v in data.items():
                        lines.append(f"{k}:")
                        if isinstance(v, list):
                            lines.extend([f"  • {item}" for item in v])
                        else:
                            lines.append(f"  {v}")
                        lines.append("")
                    return "\n".join(lines).strip()
                elif isinstance(data, list):
                    return "\n".join([f"• {item}" for item in data])
                return str(data).replace("\\n", "\n")

            st.divider()
            st.header("Section-by-Section Review")
            
            # Combine keys to show newly added sections (like Skills) as well
            all_keys = list(st.session_state['parsed_resume'].keys())
            for k in enhanced_resume_dict.keys():
                if k not in all_keys:
                    all_keys.append(k)
            
            for section in all_keys:
                original_content = st.session_state['parsed_resume'].get(section, "Not present in original resume.")
                enhanced_text = enhanced_resume_dict.get(section, "Not present.")
                
                if (not original_content or original_content in ["None", [], {}]) and (not enhanced_text or enhanced_text in ["None", [], {}]):
                    continue
                
                st.subheader(section)
                
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    st.text_area("Original", value=format_for_display(original_content), height=250, disabled=True, key=f"orig_{section}")
                with sub_col2:
                    st.text_area("Enhanced", value=format_for_display(enhanced_text), height=250, key=f"enh_{section}")
            
            # --- New Template Previews & Downloads ---
            st.divider()
            st.header("4. Select & Download PDF Templates")
            st.markdown("Your enhanced text has been formatted perfectly with no blank spaces into 3 different design templates.")
            
            tab1, tab2, tab3 = st.tabs(["Template 1", "Template 2", "Template 3"])
            
            def create_download_button(template_name, container):
                try:
                    html_str = pdf_templates.render_html_template(template_name, enhanced_resume_dict)
                    pdf_bytes = pdf_templates.generate_pdf_from_html(html_str)
                    
                    container.components.v1.html(html_str, height=600, scrolling=True)
                    
                    container.download_button(
                        label=f"⬇️ Download {template_name} as PDF",
                        data=pdf_bytes,
                        file_name=f"Resume_{template_name.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                except Exception as e:
                    container.error(f"Failed to build {template_name}: {e}")
    
            with tab1:
                create_download_button("Template 1", st)
            with tab2:
                create_download_button("Template 2", st)
            with tab3:
                create_download_button("Template 3", st)
                
    elif not st.session_state.get('parsed_resume'):
        st.info("Upload and Extract a resume first.")
    elif not job_desc:
        st.info("Enter a Job Description above to enable enhancements.")

elif app_mode == "Database Review":
    st.header("Database Review")
    st.markdown("View past resumes extracted and enhanced in your session.")
    
    try:
        records = db.get_all_resumes()
        
        if not records:
            st.info("No records found in the database. Go to the Enhancer and extract a resume first!")
        else:
            search_query = st.text_input("Search Candidate Name...", "")
            
            # Sort records visually to table
            for record in records:
                name = record.get("candidate_name") or "Unknown Candidate"
                if search_query.lower() not in name.lower() and search_query != "":
                    continue
                    
                created_at = record.get("created_at") or "Unknown Date"
                o_score = record.get("original_ats_score")
                e_score = record.get("enhanced_ats_score")
                
                score_str = f"(Orig ATS: {o_score}%" if o_score is not None else "(Orig ATS: N/A"
                if e_score is not None:
                    score_str += f" ➡️ Enh ATS: {e_score}%)"
                else:
                    score_str += ")"
                
                with st.expander(f"Applicant: {name} | {score_str} | Date: {created_at}"):
                    st.write(f"**Database ID:** {record['id']}")
                    
                    if o_score is not None and e_score is not None:
                        st.metric("ATS Improvement", f"{e_score}%", delta=f"{e_score - o_score}%")
                    elif o_score is not None:
                        st.metric("Original ATS Match", f"{o_score}%")
                        
                    tab_orig, tab_jd, tab_enh = st.tabs(["Original Parsed JSON", "Job Description", "Enhanced JSON"])
                    
                    with tab_orig:
                        st.json(record.get('parsed_json') or {})
                        if st.checkbox("Show raw extracted text", key=f"raw_{record['id']}"):
                            st.text_area("Raw Context", record.get("original_text", ""), height=200, disabled=True, key=f"rawe_{record['id']}")
                            
                    with tab_jd:
                        jd_text = record.get("job_description")
                        if jd_text:
                            st.text_area("Job Description Target", jd_text, height=200, disabled=True, key=f"jd_{record['id']}")
                        else:
                            st.info("No Job Description was provided for this resume.")
                            
                    with tab_enh:
                        enhanced_data = record.get("enhanced_json")
                        if enhanced_data:
                            st.json(enhanced_data)
                        else:
                            st.info("This resume has not been enhanced yet.")
                            
                    st.divider()
                    if st.button("Delete Record", key=f"delete_{record['id']}", type="secondary"):
                        db.delete_resume_record(record['id'])
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error accessing database: {e}")
