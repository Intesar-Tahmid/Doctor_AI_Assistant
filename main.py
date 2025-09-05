import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import google.generativeai as genai
import os
import random
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv('GEMINI_API_KEY')

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    st.error("Gemini API Key Not Found")

# App configuration
st.set_page_config(
    page_title="MedConnect - Find Your Specialist",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'specialty' not in st.session_state:
    st.session_state.specialty = None
if 'doctor_data' not in st.session_state:
    st.session_state.doctor_data = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = {}
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'doctors_loaded' not in st.session_state:
    st.session_state.doctors_loaded = False
if 'doctor_db' not in st.session_state:
    st.session_state.doctor_db = None

# Load doctor database
def load_doctor_database():
    try:
        # Load the CSV file
        doctor_db = pd.read_csv("Doctor_Directory.csv")
        st.session_state.doctor_db = doctor_db
        st.session_state.doctors_loaded = True
        return doctor_db
    except Exception as e:
        st.error(f"Error loading doctor database: {str(e)}")
        return None

# Filter doctors based on specialty, location, and availability
def filter_doctors(specialty, location, preferred_date, preferred_time):
    if st.session_state.doctor_db is None:
        load_doctor_database()
    
    if st.session_state.doctor_db is None:
        return None
    
    doctor_db = st.session_state.doctor_db
    
    # Filter by specialty (case-insensitive)
    specialty_filter = doctor_db['Department'].str.lower() == specialty.lower()
    filtered_doctors = doctor_db[specialty_filter]
    
    # If no doctors found in that specialty, try to find similar departments
    if len(filtered_doctors) == 0:
        # Look for similar specialties (this is a simple approach)
        similar_specialties = {
            'cardiology': ['Cardiology'],
            'dermatology': ['Dermatology'],
            'neurology': ['Neurology'],
            'orthopedics': ['Orthopedics'],
            'pediatrics': ['Pediatrics'],
            'psychiatry': ['Psychiatry'],
            'gynecology': ['Gynecology'],
            'general practice': ['General Medicine', 'General Surgery'],
            'general medicine': ['General Medicine'],
            'general surgery': ['General Surgery'],
            'gastroenterology': ['Gastroenterology'],
            'oncology': ['Oncology'],
            'ophthalmology': ['Ophthalmology'],
            'ent': ['ENT'],
            'urology': ['Urology'],
            'nephrology': ['Nephrology']
        }
        
        if specialty.lower() in similar_specialties:
            similar_departments = similar_specialties[specialty.lower()]
            specialty_filter = doctor_db['Department'].isin(similar_departments)
            filtered_doctors = doctor_db[specialty_filter]
    
    # Filter by location if provided (case-insensitive)
    if location:
        location_lower = location.lower()
        location_filter = (
            doctor_db['District'].str.lower().str.contains(location_lower) |
            doctor_db['Upazila'].str.lower().str.contains(location_lower) |
            doctor_db['Address'].str.lower().str.contains(location_lower)
        )
        filtered_doctors = filtered_doctors[location_filter]
    
    # For MVP, we'll simulate availability based on the doctor's ID and time
    # In a real application, you would have actual availability data
    available_doctors = []
    for _, doctor in filtered_doctors.iterrows():
        # Simulate availability (70% chance of being available)
        is_available = random.random() > 0.3
        
        if is_available:
            available_doctors.append(doctor)
    
    # Convert to DataFrame
    if available_doctors:
        return pd.DataFrame(available_doctors)
    else:
        return pd.DataFrame()

# Add sidebar for API key input (for development)
# with st.sidebar:
#     st.header("Configuration")
#     gemini_api_key = st.text_input("Enter your Gemini API Key", type="password")
#     if gemini_api_key:
#         genai.configure(api_key=gemini_api_key)
#         st.success("API key configured!")
#     else:
#         st.info("Please enter your Gemini API key to use the symptom analysis feature.")

# Function to analyze symptoms using Gemini
def analyze_symptoms(user_input):
    # try:
        # Create the model
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
    )
    
    # Prepare the prompt
    prompt_parts = [
        "You are a medical triage assistant. Based on the following symptoms and concerns, ",
        "recommend the most appropriate medical specialty. Your response should be only the name ",
        "of the specialty (e.g., 'Cardiology', 'Dermatology', 'General Practice').",
        "\nUser Input:"
    ]
    
    # Add the user inputs to the prompt
    if 'keywords' in user_input:
        prompt_parts.append(f"Keywords: {user_input['keywords']}")
    
    if 'questions' in user_input:
        prompt_parts.append(f"Questions: {user_input['questions']}")
    
    if 'text_description' in user_input:
        prompt_parts.append(f"Description: {user_input['text_description']}")
    
    # Note: For documents, we would need to extract text first
    # For MVP, we'll just note that documents were provided
    if 'uploaded_files' in user_input:
        prompt_parts.append(f"User also uploaded {len(user_input['uploaded_files'])} document(s)")
    
    prompt = "\n".join(prompt_parts)
    
    # Generate content
    response = model.generate_content(prompt)
    return response.text.strip()
    # except Exception as e:
    #     st.error(f"Error analyzing symptoms: {str(e)}")
    #     return "General Practice"  # Fallback specialty

# App header
st.title("🏥 MedConnect")
st.markdown("### Find the right medical specialist for your needs")

# Introduction
st.markdown("""
Welcome to MedConnect! We'll help you find the appropriate medical specialist 
based on your symptoms or concerns. Start by providing information about your condition 
using one or more of the methods below.
""")

# Input methods section
st.header("Describe Your Medical Concern")

# Create tabs for different input methods
tab1, tab2, tab3, tab4 = st.tabs(["🔑 Keywords", "❓ Questions", "📝 Text Description", "📄 Scanned Documents"])

with tab1:
    st.subheader("Enter Keywords")
    st.markdown("List symptoms or medical terms (e.g., 'headache', 'fever', 'chest pain')")
    keywords = st.text_area(
        "Keywords (separate with commas)",
        placeholder="headache, fever, nausea...",
        height=100,
        label_visibility="collapsed"
    )
    if keywords:
        st.session_state.user_input['keywords'] = keywords

with tab2:
    st.subheader("Ask Questions")
    st.markdown("Describe your concerns in question format")
    questions = st.text_area(
        "Questions",
        placeholder="What could be causing my persistent cough? Should I be concerned about chest pain?",
        height=100,
        label_visibility="collapsed"
    )
    if questions:
        st.session_state.user_input['questions'] = questions

with tab3:
    st.subheader("Describe in Detail")
    st.markdown("Provide a detailed description of your symptoms or concerns")
    text_description = st.text_area(
        "Detailed Description",
        placeholder="I've been experiencing sharp pains in my lower right abdomen for the past two days, accompanied by a mild fever and loss of appetite...",
        height=150,
        label_visibility="collapsed"
    )
    if text_description:
        st.session_state.user_input['text_description'] = text_description

with tab4:
    st.subheader("Upload Documents")
    st.markdown("Upload scanned medical documents, test results, or doctor's notes")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        st.session_state.user_input['uploaded_files'] = uploaded_files
        for file in uploaded_files:
            st.write(f"📄 {file.name}")

# Add a button to submit the inputs
# if st.button("Analyze My Symptoms", type="primary", use_container_width=True):
#     # Check if any input was provided
#     if not st.session_state.user_input:
#         st.error("Please provide at least one form of input about your medical concern.")
#     elif not gemini_api_key:
#         st.error("Please enter your Gemini API key in the sidebar to analyze symptoms.")
#     else:
#         # Store the input for processing
#         st.session_state.analysis_started = True
        
#         with st.spinner("Analyzing your symptoms to determine the right specialist..."):
#             # Call the Gemini API to analyze symptoms
#             specialty = analyze_symptoms(st.session_state.user_input)
#             st.session_state.specialty = specialty
#             st.session_state.analysis_complete = True
            
#         # Move to the next step
#         st.rerun()
if st.button("Analyze My Symptoms", type="primary", use_container_width=True):
    # Check if any input was provided
    if not st.session_state.user_input:
        st.error("Please provide at least one form of input about your medical concern.")
    else:
        # Store the input for processing
        st.session_state.analysis_started = True
        
        with st.spinner("Analyzing your symptoms to determine the right specialist..."):
            # Call the Gemini API to analyze symptoms
            specialty = analyze_symptoms(st.session_state.user_input)
            st.session_state.specialty = specialty
            st.session_state.analysis_complete = True
            
        # Move to the next step
        st.rerun()

# Display a summary of provided inputs if any
if st.session_state.user_input:
    st.divider()
    st.subheader("Input Summary")
    
    if 'keywords' in st.session_state.user_input:
        st.write("🔑 **Keywords:**", st.session_state.user_input['keywords'])
    
    if 'questions' in st.session_state.user_input:
        st.write("❓ **Questions:**", st.session_state.user_input['questions'])
    
    if 'text_description' in st.session_state.user_input:
        st.write("📝 **Description:**", st.session_state.user_input['text_description'])
    
    if 'uploaded_files' in st.session_state.user_input:
        st.write("📄 **Uploaded files:**", 
                 ", ".join([f.name for f in st.session_state.user_input['uploaded_files']]))

# Display the analysis result if available
if st.session_state.analysis_complete:
    st.divider()
    st.subheader("Analysis Result")
    
    st.success(f"Based on your symptoms, we recommend seeing a **{st.session_state.specialty}** specialist.")
    
    # Next step: Get location and time preferences
    st.markdown("### Next: Find Available Specialists")
    
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input("Enter your location (city, district, or upazila)")
    
    with col2:
        preferred_date = st.date_input("Preferred appointment date")
        preferred_time = st.time_input("Preferred time of day")
    
    if st.button("Find Available Doctors", type="primary"):
        if location:
            st.session_state.location = location
            st.session_state.preferred_date = preferred_date
            st.session_state.preferred_time = preferred_time
            
            # Load doctor database if not already loaded
            if not st.session_state.doctors_loaded:
                with st.spinner("Loading doctor database..."):
                    load_doctor_database()
            
            # Filter doctors based on criteria
            with st.spinner("Finding available doctors..."):
                available_doctors = filter_doctors(
                    st.session_state.specialty, 
                    location, 
                    preferred_date, 
                    preferred_time
                )
                
                if available_doctors is not None and len(available_doctors) > 0:
                    st.session_state.available_doctors = available_doctors
                    st.session_state.doctors_found = True
                else:
                    st.session_state.doctors_found = False
                    
            st.rerun()
        else:
            st.error("Please enter your location to find available doctors.")

# Display available doctors if found
if hasattr(st.session_state, 'doctors_found') and st.session_state.doctors_found:
    st.divider()
    st.subheader("Available Doctors")
    
    doctors_df = st.session_state.available_doctors
    
    # Display doctors in a nice format
    for idx, doctor in doctors_df.iterrows():
        with st.expander(f"👨‍⚕️ Dr. {doctor['Provider']} - {doctor['Department']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Specialty:** {doctor['Department']}")
                st.write(f"**Hospital/Clinic:** {doctor['Address']}")
                st.write(f"**Location:** {doctor['District']}, {doctor['Upazila']}")
                st.write(f"**Qualifications:** {doctor['Degree']}")
                
            with col2:
                st.write(f"**Position:** {doctor['Post']}")
                st.write(f"**Contact:** {doctor['ContactNo']}")
                st.write(f"**Professional Type:** {doctor['Professional']}")
                
                # Simulated availability for MVP
                available_times = ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"]
                selected_time = st.selectbox(
                    f"Select appointment time with Dr. {doctor['Provider']}",
                    available_times,
                    key=f"time_{idx}"
                )
                
                if st.button(f"Book Appointment with Dr. {doctor['Provider']}", key=f"book_{idx}"):
                    st.success(f"Appointment booked with Dr. {doctor['Provider']} at {selected_time} on {st.session_state.preferred_date}!")
                    
    st.info(f"Found {len(doctors_df)} doctors matching your criteria.")

elif hasattr(st.session_state, 'doctors_found') and not st.session_state.doctors_found:
    st.warning("No doctors found matching your criteria. Please try a different location or specialty.")