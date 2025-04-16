import streamlit as st
import pandas as pd
import validators
import os
from utils.web_scraper import scrape_website
from utils.llm_integration import classify_website, infer_industries
from utils.file_utils import parse_csv, export_to_csv

# Set page config
st.set_page_config(page_title="Leads and Logic App",
                   page_icon="🔍",
                   layout="wide",
                   initial_sidebar_state="collapsed")

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


def show_license_agreement():
    license_container = st.empty()
    with license_container.container():
        st.markdown("""
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px; border: 1px solid #ddd; box-shadow: 0 0 15px rgba(0,0,0,0.15); max-width: 800px; margin: 0 auto; font-size: 16px; line-height: 1.5; color: #333333;">
            <h2 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">Leads and Logic App - Licensing Agreement</h2>
            <p style="margin-bottom: 15px;"><strong>Effective Date: April 5th, 2025</strong></p>
            <p style="margin-bottom: 15px;">By using the Leads and Logic app ("App"), you agree to the following terms:</p>
            <ul style="margin-bottom: 20px; margin-left: 20px;">
                <li style="margin-bottom: 10px;"><strong>License:</strong> The App is provided for free and can be used commercially or otherwise, at your own risk. You are responsible for any consequences arising from your use of the App.</li>
                <li style="margin-bottom: 10px;"><strong>Data Retention:</strong> The Leads and Logic community does not store or retain any data or files submitted through the App. You are responsible for the security of your data.</li>
                <li style="margin-bottom: 10px;"><strong>API Key:</strong> The App requires an API key from an external large language model provider (such as OpenAI or Anthropic). You must obtain this key privately and keep it confidential. Do not share it with others.</li>
                <li style="margin-bottom: 10px;"><strong>Restrictions:</strong> You cannot reverse-engineer, redistribute, or misuse the App. Keep your API key secure and do not use the App in a way that harms its functionality or others.</li>
                <li style="margin-bottom: 10px;"><strong>No Warranty:</strong> The App is provided "as is," without any warranties or guarantees. We are not responsible for any issues arising from your use of the App.</li>
                <li style="margin-bottom: 10px;"><strong>Liability:</strong> The Provider is not liable for any damages, including data loss or interruptions, related to your use of the App.</li>
                <li style="margin-bottom: 10px;"><strong>Modifications:</strong> We may modify or discontinue the App at any time without notice.</li>
            </ul>
            <p style="margin-bottom: 15px;">By using the App, you accept these terms.</p>
            <p style="margin-bottom: 0; text-align: center;"><a href="https://leadslogic.slack.com/" target="_blank" style="color: #3498db; text-decoration: underline;">Leads and Logic Community</a></p>
            </div>
            """,
                    unsafe_allow_html=True)

        # Center the Accept button with columns
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Accept",
                         use_container_width=True,
                         key="accept_license"):
                st.session_state.show_license = False
                st.rerun()


def main_menu():
    """Display the main menu"""
    st.title("Classify websites into industries")
    #st.subheader("Classify websites into industries")
    st.markdown(
        "App by [Leads and Logic Community](https://leadslogic.slack.com/)")
    # Instructions
    st.markdown("""
    ### How to use this app:
    1. Select your preferred LLM provider (such as Anthropic, or OpenAI) and enter your API key
    2. You have three options to define your industries:
       - Use our default industry list
       - Have the AI suggest industries based on your business description
       - Upload your own custom industries list
    3. After confirming industries, you'll enter websites to classify
    4. The app will analyse and categorise each website
    """)

    # LLM Provider selection
    st.markdown("### Step 1: Set up your AI provider")
    providers = ["OpenAI", "Anthropic"]
    st.session_state.llm_provider = st.selectbox("Select LLM Provider",
                                                 providers)

    # API Key input
    api_key = st.text_input(
        "Enter your API key",
        type="password",
        help="Your API key will not be stored and is only used for this session"
    )
    if api_key:
        st.session_state.api_key = api_key

    st.markdown("### Step 2: Define industries for classification")

    # Default industries button
    if st.button("Proceed with default industries"):
        st.session_state.industries = [
            "Technology & Software", "E-commerce & Retail",
            "Finance & FinTech", "Healthcare & Life Sciences",
            "Education & Training", "Marketing & Advertising",
            "Consulting & Professional", "Services", "Media & Content",
            "Real Estate", "Travel, Hospitality & Events",
            "Manufacturing & Industrial", "Non-Profit & Government",
            "Other / Miscellaneous"
        ]
        st.session_state.page = "industry_confirmation"
        st.rerun()

    # Business description input
    st.markdown("### Or describe your business for AI-suggested industries")
    business_description = st.text_area(
        "Describe the business you're classifying for",
        help=
        "Detail the products or services rendered, example of past or current customers, "
        +
        "business goals, capacity and resources, and any other relevant information."
    )

    # Infer industries button
    if st.button("Proceed with inferred industries"):
        if not business_description:
            st.error(
                "Please provide a business description to infer industries.")
        elif not st.session_state.api_key:
            st.error("API key is required to infer industries.")
        else:
            with st.spinner(
                    "Inferring industries based on your description..."):
                try:
                    inferred_industries = infer_industries(
                        business_description, st.session_state.llm_provider,
                        st.session_state.api_key)
                    st.session_state.industries = inferred_industries
                    st.session_state.page = "industry_confirmation"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error inferring industries: {str(e)}")

    # Upload custom industries
    st.markdown("### Or upload custom industries")
    uploaded_file = st.file_uploader(
        "Upload CSV file with industries (one per line)", type="csv")

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

    st.markdown("""
    ### Notes & Tips:
    1. It is sometimes difficult to get the right API key. If you are having trouble, please contact us on the [Leads and Logic Community](https://leadslogic.slack.com/) for assistance.
    2.  If you choose to infer industries, please provide as much detail as possible to support accurate and meaningful inferences. This may include a description of the products or services offered, examples of past or current customers, business goals, available capacity and resources, and any other relevant context. The more comprehensive the information, the better we can tailor results to your specific needs.
    3.  If you choose to upload custom industries, ensure that the CSV file contains one industry per line. The file should be plain text with no headers or additional formatting.
    """)


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
            st.warning(
                "No industries have been added yet. Add some industries below."
            )

        # Use a card-like styling for each industry
        for i, industry in enumerate(industries):
            if not st.session_state.deleted_industries[i]:
                with st.container():
                    # Add a slight visual separation between items
                    if i > 0:
                        st.markdown(
                            "<hr style='margin: 5px 0; opacity: 0.3;'>",
                            unsafe_allow_html=True)

                    col1, col2, col3 = st.columns([8, 3, 2])

                    with col1:
                        updated_industry = st.text_input(
                            label=f"Industry {i+1}",
                            value=industry,
                            key=f"industry_{i}",
                            placeholder="Enter industry name")

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
                placeholder="E.g., Technology, Healthcare, Finance, etc.")

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
        st.success(
            f"You have {len(updated_industries)} industries ready for classification."
        )

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
        proceed_button = st.button("Confirm industries and proceed ▶️",
                                   type="primary",
                                   use_container_width=True)
        if proceed_button:
            if not updated_industries:
                st.error("At least one industry is required.")
            else:
                st.session_state.page = "website_input"
                st.session_state.deleted_industries = [
                ]  # Reset the delete tracker
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
                        st.markdown(
                            "<hr style='margin: 5px 0; opacity: 0.3;'>",
                            unsafe_allow_html=True)

                    col1, col2 = st.columns([4, 1])

                    with col1:
                        updated_website = st.text_input(
                            label=f"Website {i+1}",
                            value=website,
                            key=f"website_{i}",
                            placeholder="https://example.com")

                    with col2:
                        # Use a button instead of a checkbox for immediate feedback
                        if st.button("🗑️ Delete",
                                     key=f"delete_website_btn_{i}"):
                            st.session_state.deleted_websites[i] = True
                            st.rerun()

                    # Validate the URL
                    if updated_website.strip():
                        if validators.url(updated_website):
                            updated_websites.append(updated_website)
                        else:
                            st.warning(
                                f"'{updated_website}' is not a valid URL. Please include http:// or https://."
                            )

    # Add new website in a visually distinct section
    st.markdown("---")
    st.markdown("### Add New Website")

    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            new_website = st.text_input("New Website URL",
                                        key="new_website_input",
                                        placeholder="https://example.com")

        with col2:
            add_button = st.button("➕ Add Website", type="primary")

        if add_button:
            if not new_website.strip():
                st.error("Please enter a website URL.")
            elif not validators.url(new_website):
                st.error(
                    "Please enter a valid URL (must start with http:// or https://)."
                )
            else:
                websites.append(new_website)
                st.session_state.deleted_websites.append(False)
                st.session_state.websites = websites
                st.rerun()

    # Upload websites from CSV
    st.markdown("### Or upload multiple websites from CSV file")
    
    with st.container():
        st.markdown("""
        CSV file should:
        - Contain one website URL per line
        - URLs must start with http:// or https://
        - Can be a plain text file with .csv extension
        """)
        
        csv_col1, csv_col2 = st.columns([3, 1])
        
        with csv_col1:
            uploaded_file = st.file_uploader("Upload CSV file with website URLs", type=["csv", "txt"])
        
        with csv_col2:
            if uploaded_file is not None:
                process_csv = st.button("Process CSV", type="primary")
            else:
                process_csv = False
        
        if uploaded_file is not None and process_csv:
            # Create a spinner to show processing
            with st.spinner("Processing CSV file..."):
                try:
                    # Parse the CSV file
                    new_websites = parse_csv(uploaded_file)
                    
                    if not new_websites:
                        st.error("The uploaded file appears to be empty.")
                    else:
                        # Show the parsed content in an expander
                        with st.expander("CSV File Contents"):
                            st.write(f"Found {len(new_websites)} entries in the CSV file:")
                            for i, entry in enumerate(new_websites):
                                st.text(f"{i+1}. {entry}")
                        
                        # Validate URLs
                        valid_websites = []
                        invalid_websites = []
                        
                        for url in new_websites:
                            # Add http:// prefix if missing
                            if url and not url.startswith(('http://', 'https://')):
                                url = 'https://' + url
                                
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
                            st.success(f"✅ Successfully added {len(valid_websites)} valid websites from the file.")
                            
                            if invalid_websites:
                                with st.expander(f"⚠️ {len(invalid_websites)} invalid URLs were ignored"):
                                    for i, url in enumerate(invalid_websites):
                                        st.text(f"{i+1}. {url}")
                            
                            # Wait a moment before rerunning to show the success message
                            import time
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("No valid website URLs found in the uploaded file.")
                except Exception as e:
                    st.error(f"Error processing the file: {str(e)}")
                    st.info("Please ensure your CSV file contains valid website URLs, one per line.")
                    
        # Example CSV format
        with st.expander("Show example CSV format"):
            st.code("""https://example.com
https://google.com
https://microsoft.com""", language="text")

    # Save updated websites
    st.session_state.websites = updated_websites

    # Show current count
    if updated_websites:
        st.success(
            f"You have {len(updated_websites)} websites ready for classification."
        )

    # Navigation buttons in a fixed footer
    st.markdown("---")
    st.markdown("### Navigation")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀️ Back to Industries", use_container_width=True):
            st.session_state.page = "industry_confirmation"
            st.rerun()

    with col2:
        proceed_button = st.button("Confirm websites and proceed ▶️",
                                   type="primary",
                                   use_container_width=True)
        if proceed_button:
            if not updated_websites:
                st.error("At least one website is required.")
            elif not st.session_state.api_key:
                st.error("API key is required for classification.")
            else:
                st.session_state.page = "processing"
                st.session_state.deleted_websites = [
                ]  # Reset the delete tracker
                st.rerun()


def processing_page():
    """Process websites and classify them"""
    st.title("Processing Websites")
    st.subheader("Please wait while we analyse your websites")

    # Show processing info
    st.markdown("""
    ### What's happening now:
    1. Each website is being scraped to extract its content
    2. The AI is analysing the content to determine the most appropriate industry
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
            status_text.markdown(
                f"### Processing website {current_website} of {total_websites}"
            )

            with details_expander:
                st.write(f"🔍 Analysing: {website}")

            try:
                # Scrape the website
                with details_expander:
                    st.write("📥 Scraping website content...")

                content = scrape_website(website)

                # Classify the website
                with details_expander:
                    st.write("🧠 Classifying content with AI...")

                classification_result = classify_website(
                    website, content, st.session_state.industries,
                    st.session_state.llm_provider, st.session_state.api_key)

                results.append(classification_result)

                with details_expander:
                    st.write(
                        f"✅ Classification complete: {classification_result['industry']}"
                    )

            except Exception as e:
                # Handle failed scraping
                with details_expander:
                    st.write(f"❌ Error: {str(e)}")

                results.append({
                    "url":
                    website,
                    "industry":
                    "Unknown",
                    "additional_notes":
                    f"Website scraping failed: {str(e)}"
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
    classified_sites = sum(1 for r in st.session_state.results
                           if r["industry"] != "Unknown")
    unknown_sites = total_sites - classified_sites

    st.markdown(f"""
    ### Summary
    - Total websites analysed: **{total_sites}**
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
    st.markdown(
        "Download the classification results as a CSV file for your records.")

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
            use_container_width=True)

    # Navigation
    st.markdown("### What's Next?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "Start a new classification with different websites or industries:"
        )
        if st.button("🔄 Start New Classification", use_container_width=True):
            # Reset necessary state
            st.session_state.page = "main_menu"
            st.session_state.industries = []
            st.session_state.websites = []
            st.session_state.results = []
            st.rerun()

    with col2:
        st.markdown(
            "App by [Leads and Logic Community](https://leadslogic.slack.com/)"
        )

    # Footer
    st.markdown("---")
    st.markdown(
        "Thank you for using Leads and Logic. We hope this tool helps your business grow!"
    )


# Main app flow
if st.session_state.show_license:
    show_license_agreement()
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
