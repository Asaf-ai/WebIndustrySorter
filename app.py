import streamlit as st
import pandas as pd
import validators
import os
from utils.web_scraper import scrape_website
from utils.llm_integration import classify_website, infer_industries
from utils.file_utils import parse_csv, export_to_csv

# Set page config
st.set_page_config(
    page_title="Leads and Logic App",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.show_license = True
    st.session_state.page = "main_menu"
    st.session_state.llm_provider = None
    st.session_state.api_key = None
    st.session_state.industries = []
    st.session_state.websites = []
    st.session_state.results = []

def license_agreement():
    """Display the license agreement popup"""
    if st.session_state.show_license:
        with st.container():
            st.markdown("""
            # Leads and Logic App - Licensing Agreement
            **Effective Date: April 5th, 2025**
            
            By using the Leads and Logic app ("App"), you agree to the following terms:
            
            **License:** The App is provided for free and can be used commercially or otherwise, at your own risk. You are responsible for any consequences arising from your use of the App.
            
            **Data Retention:** The Leads and Logic community does not store or retain any data or files submitted through the App. You are responsible for the security of your data.
            
            **API Key:** The App requires an API key from an external LLM provider. You must obtain this key privately and keep it confidential. Do not share it with others.
            
            **Restrictions:** You cannot reverse-engineer, redistribute, or misuse the App. Keep your API key secure and do not use the App in a way that harms its functionality or others.
            
            **No Warranty:** The App is provided "as is," without any warranties or guarantees. We are not responsible for any issues arising from your use of the App.
            
            **Liability:** The Provider is not liable for any damages, including data loss or interruptions, related to your use of the App.
            
            **Modifications:** We may modify or discontinue the App at any time without notice.
            
            By using the App, you accept these terms.
            
            [Leads and Logic Community](https://leadslogic.slack.com/)
            """)
            
            if st.button("I Accept", key="accept_license"):
                st.session_state.show_license = False
                st.rerun()

def main_menu():
    """Display the main menu"""
    st.title("Leads and Logic App")
    st.subheader("Classify websites into industries")
    
    # LLM Provider selection
    providers = ["OpenAI", "Anthropic", "Google", "Mistral", "Llama"]
    st.session_state.llm_provider = st.selectbox("Select LLM Provider", providers)
    
    # API Key input
    api_key = st.text_input("Enter your API key", type="password")
    if api_key:
        st.session_state.api_key = api_key
    
    # Business description input
    st.markdown("### Business Description")
    business_description = st.text_area(
        "Describe the business you're classifying for",
        help="Detail the products or services rendered, example of past or current customers, " +
        "business goals, capacity and resources, and any other relevant information."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Default industries button
        if st.button("Proceed with default industries"):
            st.session_state.industries = [
                "Technology & Software", 
                "E-commerce & Retail", 
                "Finance & FinTech",
                "Healthcare & Life Sciences", 
                "Education & Training", 
                "Marketing & Advertising",
                "Consulting & Professional", 
                "Services", 
                "Media & Content", 
                "Real Estate",
                "Travel, Hospitality & Events", 
                "Manufacturing & Industrial", 
                "Non-Profit & Government",
                "Other / Miscellaneous"
            ]
            st.session_state.page = "industry_confirmation"
            st.rerun()
    
    with col2:
        # Infer industries button
        if business_description and st.button("Proceed with inferred industries"):
            if not st.session_state.api_key:
                st.error("API key is required to infer industries.")
            else:
                with st.spinner("Inferring industries based on your description..."):
                    try:
                        inferred_industries = infer_industries(
                            business_description, 
                            st.session_state.llm_provider, 
                            st.session_state.api_key
                        )
                        st.session_state.industries = inferred_industries
                        st.session_state.page = "industry_confirmation"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error inferring industries: {str(e)}")
    
    # Upload custom industries
    st.markdown("### Or upload custom industries")
    uploaded_file = st.file_uploader("Upload CSV file with industries (one per line)", type="csv")
    
    if uploaded_file is not None:
        try:
            industries = parse_csv(uploaded_file)
            if industries:
                st.session_state.industries = industries
                st.session_state.page = "industry_confirmation"
                st.rerun()
            else:
                st.error("No industries found in the uploaded file.")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {str(e)}")

def industry_confirmation():
    """Display the industry confirmation page"""
    st.title("Confirm Industries")
    st.subheader("Review and edit the industries below")
    
    industries = st.session_state.industries.copy()
    updated_industries = []
    
    # Display each industry with options to edit or delete
    for i, industry in enumerate(industries):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            updated_industry = st.text_input(f"Industry {i+1}", value=industry, key=f"industry_{i}")
        with col2:
            delete = st.checkbox("Delete", key=f"delete_{i}")
        
        if not delete and updated_industry.strip():
            updated_industries.append(updated_industry)
    
    # Add new industry
    st.markdown("### Add New Industry")
    new_industry = st.text_input("New Industry")
    if st.button("Add") and new_industry.strip():
        updated_industries.append(new_industry)
        st.rerun()
    
    # Save updated industries
    st.session_state.industries = updated_industries
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Main Menu"):
            st.session_state.page = "main_menu"
            st.rerun()
    
    with col2:
        if st.button("Confirm industries and proceed"):
            if not updated_industries:
                st.error("At least one industry is required.")
            else:
                st.session_state.page = "website_input"
                st.rerun()

def website_input():
    """Display the website input page"""
    st.title("Enter Websites to Classify")
    st.subheader("Add the websites you want to classify")
    
    websites = st.session_state.websites.copy()
    updated_websites = []
    
    # Display each website with options to edit or delete
    for i, website in enumerate(websites):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            updated_website = st.text_input(f"Website {i+1}", value=website, key=f"website_{i}")
        with col2:
            delete = st.checkbox("Delete", key=f"delete_website_{i}")
        
        if not delete and updated_website.strip():
            if validators.url(updated_website):
                updated_websites.append(updated_website)
            else:
                st.warning(f"'{updated_website}' is not a valid URL. It will be ignored.")
    
    # Add new website
    st.markdown("### Add New Website")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_website = st.text_input("New Website URL", placeholder="https://example.com")
    with col2:
        if st.button("Add") and new_website.strip():
            if validators.url(new_website):
                updated_websites.append(new_website)
                st.rerun()
            else:
                st.error("Please enter a valid URL.")
    
    # Upload websites from CSV
    st.markdown("### Or upload websites from CSV")
    uploaded_file = st.file_uploader("Upload CSV file with websites (one per line)", type="csv")
    
    if uploaded_file is not None:
        try:
            new_websites = parse_csv(uploaded_file)
            valid_websites = []
            for url in new_websites:
                if validators.url(url):
                    valid_websites.append(url)
                else:
                    st.warning(f"'{url}' is not a valid URL. It will be ignored.")
            
            if valid_websites:
                # Merge with existing websites
                updated_websites.extend([w for w in valid_websites if w not in updated_websites])
                st.success(f"Added {len(valid_websites)} valid websites from the file.")
                st.rerun()
            else:
                st.error("No valid websites found in the uploaded file.")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {str(e)}")
    
    # Save updated websites
    st.session_state.websites = updated_websites
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Industries"):
            st.session_state.page = "industry_confirmation"
            st.rerun()
    
    with col2:
        if st.button("Confirm websites and proceed"):
            if not updated_websites:
                st.error("At least one website is required.")
            elif not st.session_state.api_key:
                st.error("API key is required for classification.")
            else:
                st.session_state.page = "processing"
                st.rerun()

def processing_page():
    """Process websites and classify them"""
    st.title("Processing Websites")
    
    if not st.session_state.results:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_websites = len(st.session_state.websites)
        
        for i, website in enumerate(st.session_state.websites):
            progress = (i) / total_websites
            progress_bar.progress(progress)
            status_text.text(f"Processing website {i+1} of {total_websites}: {website}")
            
            try:
                # Scrape the website
                content = scrape_website(website)
                
                # Classify the website
                classification_result = classify_website(
                    website,
                    content,
                    st.session_state.industries,
                    st.session_state.llm_provider,
                    st.session_state.api_key
                )
                
                results.append(classification_result)
                
            except Exception as e:
                # Handle failed scraping
                results.append({
                    "url": website,
                    "industry": "Unknown",
                    "additional_notes": f"Website scraping failed: {str(e)}"
                })
        
        progress_bar.progress(1.0)
        status_text.text("All websites processed!")
        
        st.session_state.results = results
    
    # Move to results page
    st.session_state.page = "results"
    st.rerun()

def results_page():
    """Display classification results"""
    st.title("Classification Results")
    
    if not st.session_state.results:
        st.error("No results to display. Please go back and try again.")
        if st.button("Back to Start"):
            st.session_state.page = "main_menu"
            st.rerun()
        return
    
    # Display results in a table
    results_df = pd.DataFrame(st.session_state.results)
    st.dataframe(results_df, hide_index=True, use_container_width=True)
    
    # Download button
    csv = export_to_csv(st.session_state.results)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="website_classification_results.csv",
        mime="text/csv",
    )
    
    # Navigation
    if st.button("Start New Classification"):
        # Reset necessary state
        st.session_state.page = "main_menu"
        st.session_state.industries = []
        st.session_state.websites = []
        st.session_state.results = []
        st.rerun()

# Main app flow
if st.session_state.show_license:
    license_agreement()
else:
    # Page router
    if st.session_state.page == "main_menu":
        main_menu()
    elif st.session_state.page == "industry_confirmation":
        industry_confirmation()
    elif st.session_state.page == "website_input":
        website_input()
    elif st.session_state.page == "processing":
        processing_page()
    elif st.session_state.page == "results":
        results_page()
