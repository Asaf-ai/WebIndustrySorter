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
    
    # Instructions
    st.markdown("""
    ### How to use this app:
    1. Select an LLM provider and enter your API key below
    2. You have three options to define industries:
       - Use our default industry list
       - Have the AI suggest industries based on your business description
       - Upload your own custom industries list
    3. After confirming industries, you'll enter websites to classify
    4. The app will analyze and categorize each website
    """)
    
    # LLM Provider selection
    st.markdown("### Step 1: Set up your AI provider")
    providers = ["OpenAI", "Anthropic"]
    st.session_state.llm_provider = st.selectbox("Select LLM Provider", providers)
    
    # API Key input
    api_key = st.text_input("Enter your API key", type="password", 
                          help="Your API key will not be stored and is only used for this session")
    if api_key:
        st.session_state.api_key = api_key
    
    st.markdown("### Step 2: Define industries for classification")
    
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
    
    # Business description input
    st.markdown("### Or describe your business for AI-suggested industries")
    business_description = st.text_area(
        "Describe the business you're classifying for",
        help="Detail the products or services rendered, example of past or current customers, " +
        "business goals, capacity and resources, and any other relevant information."
    )
    
    # Infer industries button
    if st.button("Proceed with inferred industries"):
        if not business_description:
            st.error("Please provide a business description to infer industries.")
        elif not st.session_state.api_key:
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
    
    # Instructions
    st.info("""
    **Instructions:**
    - Review the list of industries below
    - You can edit industry names by changing the text in each field
    - Click the "Delete" button to remove an industry
    - Add new industries using the form at the bottom
    - When finished, click "Confirm industries and proceed"
    """)
    
    # Get the current industries and prepare a container for updated ones
    industries = st.session_state.industries.copy()
    
    # Use session state to keep track of deleted industries
    if "deleted_industries" not in st.session_state:
        st.session_state.deleted_industries = [False] * len(industries)
    
    # If the number of industries has changed, reset the deleted_industries array
    if len(st.session_state.deleted_industries) != len(industries):
        st.session_state.deleted_industries = [False] * len(industries)
    
    updated_industries = []
    
    # Add a container for better styling
    with st.container():
        st.markdown("### Current Industries")
        
        # Display warning if no industries
        if not industries:
            st.warning("No industries have been added yet. Add some industries below.")
        
        # Use a card-like styling for each industry
        for i, industry in enumerate(industries):
            if not st.session_state.deleted_industries[i]:
                with st.container():
                    # Add a slight visual separation between items
                    if i > 0:
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([8, 3, 2])
                    
                    with col1:
                        updated_industry = st.text_input(
                            label=f"Industry {i+1}",
                            value=industry,
                            key=f"industry_{i}",
                            placeholder="Enter industry name"
                        )
                    
                    with col3:
                        # Use a button instead of a checkbox for immediate feedback
                        if st.button("🗑️ Delete", key=f"delete_btn_{i}"):
                            st.session_state.deleted_industries[i] = True
                            st.rerun()
                    
                    if updated_industry.strip():
                        updated_industries.append(updated_industry.strip())
    
    # Add new industry in a visually distinct section
    st.markdown("---")
    st.markdown("### Add New Industry")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            new_industry = st.text_input(
                "New Industry Name",
                key="new_industry_input",
                placeholder="E.g., Technology, Healthcare, Finance, etc."
            )
        
        with col2:
            add_button = st.button("➕ Add Industry", type="primary")
        
        if add_button:
            if not new_industry.strip():
                st.error("Please enter an industry name.")
            else:
                industries.append(new_industry.strip())
                st.session_state.deleted_industries.append(False)
                st.session_state.industries = industries
                st.rerun()
    
    # Show count of industries
    if updated_industries:
        st.success(f"You have {len(updated_industries)} industries ready for classification.")
    
    # Save updated industries
    st.session_state.industries = updated_industries
    
    # Navigation buttons in a fixed footer
    st.markdown("---")
    st.markdown("### Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀️ Back to Main Menu", use_container_width=True):
            st.session_state.page = "main_menu"
            st.rerun()
    
    with col2:
        proceed_button = st.button("Confirm industries and proceed ▶️", type="primary", use_container_width=True)
        if proceed_button:
            if not updated_industries:
                st.error("At least one industry is required.")
            else:
                st.session_state.page = "website_input"
                st.session_state.deleted_industries = [] # Reset the delete tracker
                st.rerun()

def website_input():
    """Display the website input page"""
    st.title("Enter Websites to Classify")
    st.subheader("Add the websites you want to classify")
    
    # Instructions
    st.info("""
    **Instructions:**
    - Enter the URLs of websites you want to classify
    - Each URL must start with http:// or https://
    - You can add websites one by one or upload a CSV file
    - When you're ready, click "Confirm websites and proceed" to start the classification process
    """)
    
    # Get the current websites and prepare a container for updated ones
    websites = st.session_state.websites.copy()
    
    # Use session state to keep track of deleted websites
    if "deleted_websites" not in st.session_state:
        st.session_state.deleted_websites = [False] * len(websites)
    
    # If the number of websites has changed, reset the deleted_websites array
    if len(st.session_state.deleted_websites) != len(websites):
        st.session_state.deleted_websites = [False] * len(websites)
    
    updated_websites = []
    
    # Display current websites section
    with st.container():
        st.markdown("### Current Websites")
        
        # Display warning if no websites
        if not websites:
            st.warning("No websites have been added yet. Add a website below.")
            
        # Use a clean list style for each website
        for i, website in enumerate(websites):
            if not st.session_state.deleted_websites[i]:
                with st.container():
                    # Add a slight visual separation between items
                    if i > 0:
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        updated_website = st.text_input(
                            label=f"Website {i+1}",
                            value=website,
                            key=f"website_{i}",
                            placeholder="https://example.com"
                        )
                    
                    with col2:
                        # Use a button instead of a checkbox for immediate feedback
                        if st.button("🗑️ Delete", key=f"delete_website_btn_{i}"):
                            st.session_state.deleted_websites[i] = True
                            st.rerun()
                    
                    # Validate the URL
                    if updated_website.strip():
                        if validators.url(updated_website):
                            updated_websites.append(updated_website)
                        else:
                            st.warning(f"'{updated_website}' is not a valid URL. Please include http:// or https://.")
    
    # Add new website in a visually distinct section
    st.markdown("---")
    st.markdown("### Add New Website")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            new_website = st.text_input(
                "New Website URL",
                key="new_website_input",
                placeholder="https://example.com"
            )
        
        with col2:
            add_button = st.button("➕ Add Website", type="primary")
        
        if add_button:
            if not new_website.strip():
                st.error("Please enter a website URL.")
            elif not validators.url(new_website):
                st.error("Please enter a valid URL (must start with http:// or https://).")
            else:
                websites.append(new_website)
                st.session_state.deleted_websites.append(False)
                st.session_state.websites = websites
                st.rerun()
    
    # Upload websites from CSV
    st.markdown("### Or upload multiple websites from CSV file")
    
    with st.container():
        st.markdown("CSV should contain one website URL per line")
        uploaded_file = st.file_uploader("Upload CSV file with website URLs", type="csv")
        
        if uploaded_file is not None:
            try:
                new_websites = parse_csv(uploaded_file)
                valid_websites = []
                invalid_websites = []
                
                for url in new_websites:
                    if validators.url(url):
                        valid_websites.append(url)
                    else:
                        invalid_websites.append(url)
                
                if valid_websites:
                    # Add valid websites to the existing list
                    for url in valid_websites:
                        if url not in websites:
                            websites.append(url)
                            st.session_state.deleted_websites.append(False)
                    
                    st.session_state.websites = websites
                    st.success(f"✅ Added {len(valid_websites)} valid websites from the file.")
                    
                    if invalid_websites:
                        st.warning(f"⚠️ {len(invalid_websites)} invalid URLs were ignored.")
                    
                    st.rerun()
                else:
                    st.error("No valid websites found in the uploaded file.")
            except Exception as e:
                st.error(f"Error parsing uploaded file: {str(e)}")
    
    # Save updated websites
    st.session_state.websites = updated_websites
    
    # Show current count
    if updated_websites:
        st.success(f"You have {len(updated_websites)} websites ready for classification.")
    
    # Navigation buttons in a fixed footer
    st.markdown("---")
    st.markdown("### Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀️ Back to Industries", use_container_width=True):
            st.session_state.page = "industry_confirmation"
            st.rerun()
    
    with col2:
        proceed_button = st.button("Confirm websites and proceed ▶️", type="primary", use_container_width=True)
        if proceed_button:
            if not updated_websites:
                st.error("At least one website is required.")
            elif not st.session_state.api_key:
                st.error("API key is required for classification.")
            else:
                st.session_state.page = "processing"
                st.session_state.deleted_websites = [] # Reset the delete tracker
                st.rerun()

def processing_page():
    """Process websites and classify them"""
    st.title("Processing Websites")
    st.subheader("Please wait while we analyze your websites")
    
    # Show processing info
    st.markdown("""
    ### What's happening now:
    1. Each website is being scraped to extract its content
    2. The AI is analyzing the content to determine the most appropriate industry
    3. Results will be displayed when all websites are processed
    
    This may take some time depending on the number of websites and their complexity.
    """)
    
    if not st.session_state.results:
        results = []
        progress_bar = st.progress(0)
        status_container = st.container()
        status_text = status_container.empty()
        details_expander = st.expander("Show processing details")
        
        total_websites = len(st.session_state.websites)
        
        for i, website in enumerate(st.session_state.websites):
            current_website = i + 1
            progress = current_website / total_websites if total_websites > 0 else 0
            progress_bar.progress(progress)
            status_text.markdown(f"### Processing website {current_website} of {total_websites}")
            
            with details_expander:
                st.write(f"🔍 Analyzing: {website}")
            
            try:
                # Scrape the website
                with details_expander:
                    st.write("📥 Scraping website content...")
                
                content = scrape_website(website)
                
                # Classify the website
                with details_expander:
                    st.write("🧠 Classifying content with AI...")
                
                classification_result = classify_website(
                    website,
                    content,
                    st.session_state.industries,
                    st.session_state.llm_provider,
                    st.session_state.api_key
                )
                
                results.append(classification_result)
                
                with details_expander:
                    st.write(f"✅ Classification complete: {classification_result['industry']}")
                
            except Exception as e:
                # Handle failed scraping
                with details_expander:
                    st.write(f"❌ Error: {str(e)}")
                
                results.append({
                    "url": website,
                    "industry": "Unknown",
                    "additional_notes": f"Website scraping failed: {str(e)}"
                })
        
        progress_bar.progress(1.0)
        status_text.markdown("### 🎉 All websites processed successfully!")
        
        st.session_state.results = results
        
        # Add a small delay to show completion message
        import time
        time.sleep(1)
    
    # Move to results page
    st.session_state.page = "results"
    st.rerun()

def results_page():
    """Display classification results"""
    st.title("Classification Results")
    st.subheader("Website Industry Classification")
    
    if not st.session_state.results:
        st.error("No results to display. Please go back and try again.")
        if st.button("Back to Start"):
            st.session_state.page = "main_menu"
            st.rerun()
        return
    
    # Results summary
    total_sites = len(st.session_state.results)
    classified_sites = sum(1 for r in st.session_state.results if r["industry"] != "Unknown")
    unknown_sites = total_sites - classified_sites
    
    st.markdown(f"""
    ### Summary
    - Total websites analyzed: **{total_sites}**
    - Successfully classified: **{classified_sites}**
    - Unable to classify: **{unknown_sites}**
    """)
    
    # Instructions
    st.markdown("""
    ### Results Table
    The table below shows the classification results for each website:
    - **URL**: The website address
    - **Industry**: The determined industry category
    - **Additional Notes**: Extra information about the classification
    
    You can sort the table by clicking on column headers.
    """)
    
    # Display results in a table
    results_df = pd.DataFrame(st.session_state.results)
    st.dataframe(results_df, hide_index=True, use_container_width=True)
    
    # Download section
    st.markdown("### Export Results")
    st.markdown("Download the classification results as a CSV file for your records.")
    
    # Download button
    csv = export_to_csv(st.session_state.results)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="website_classification_results.csv",
            mime="text/csv",
            help="Download a CSV file with all classification results",
            use_container_width=True
        )
    
    # Navigation
    st.markdown("### What's Next?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Start a new classification with different websites or industries:")
        if st.button("🔄 Start New Classification", use_container_width=True):
            # Reset necessary state
            st.session_state.page = "main_menu"
            st.session_state.industries = []
            st.session_state.websites = []
            st.session_state.results = []
            st.rerun()
    
    with col2:
        st.markdown("View detailed information about the project:")
        if st.button("ℹ️ About Leads and Logic", use_container_width=True):
            st.markdown("""
            ### About Leads and Logic
            
            The Leads and Logic app helps businesses categorize websites into relevant industries, 
            which can assist with lead generation, competitive analysis, and market research.
            
            **Features:**
            - Customizable industry categories
            - AI-powered website classification
            - Bulk processing via CSV upload
            - Exportable results
            
            For more information, visit [Leads and Logic Community](https://leadslogic.slack.com/)
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("Thank you for using Leads and Logic. We hope this tool helps your business grow!")

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
