import os
import json

def infer_industries(business_description, provider, api_key):
    """
    Infer relevant industries based on a business description using LLM.
    
    Args:
        business_description (str): Description of the business
        provider (str): The LLM provider name
        api_key (str): API key for the LLM provider
        
    Returns:
        list: List of inferred industries
    """
    if provider == "OpenAI":
        return infer_industries_openai(business_description, api_key)
    elif provider == "Anthropic":
        return infer_industries_anthropic(business_description, api_key)
    else:
        # Default to OpenAI if provider not specifically implemented
        return infer_industries_openai(business_description, api_key)

def infer_industries_openai(business_description, api_key):
    """
    Infer industries using OpenAI API
    """
    from openai import OpenAI
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    
    # Initialize the API client
    client = OpenAI(api_key=api_key)
    
    # Construct the prompt
    prompt = f"""Based on the following business description, identify a list of relevant industry categories
    (maximum 10) that would be useful for classifying websites for this business:
    
    Business Description:
    {business_description}
    
    Please provide a JSON array of industry names that are relevant to this business.
    Format your response ONLY as a JSON array of strings with no additional explanation.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we have a list of industries
        if 'industries' in result:
            industries = result['industries']
        else:
            # If the model returned a JSON object with different structure
            # try to extract a list from it
            for key, value in result.items():
                if isinstance(value, list):
                    industries = value
                    break
            else:
                # If no list found, use the values directly
                industries = list(result.values())
        
        # Handle case where we might get a list directly
        if isinstance(result, list):
            industries = result
            
        return industries
    except Exception as e:
        raise Exception(f"Error inferring industries with OpenAI: {str(e)}")

def infer_industries_anthropic(business_description, api_key):
    """
    Infer industries using Anthropic API
    """
    from anthropic import Anthropic
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    
    # Initialize the API client
    client = Anthropic(api_key=api_key)
    
    # Construct the prompt
    prompt = f"""Based on the following business description, identify a list of relevant industry categories
    (maximum 10) that would be useful for classifying websites for this business:
    
    Business Description:
    {business_description}
    
    Please provide a JSON array of industry names that are relevant to this business.
    Format your response ONLY as a JSON array of strings with no additional explanation.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract JSON from the response
        content = response.content[0].text
        
        # Try to parse JSON from the response
        try:
            # Find JSON array in the response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = content[json_start:json_end]
                industries = json.loads(json_str)
            else:
                # Look for JSON object that might contain the industries
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > 0:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Extract list from the JSON object
                    if 'industries' in result:
                        industries = result['industries']
                    else:
                        # Find the first list in the object
                        for key, value in result.items():
                            if isinstance(value, list):
                                industries = value
                                break
                        else:
                            industries = list(result.values())
                else:
                    # Fallback to parsing the whole response
                    industries = json.loads(content)
            
            return industries
        except json.JSONDecodeError:
            # If JSON parsing fails, extract industries using line-by-line approach
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            industries = []
            
            for line in lines:
                # Remove numbering, quotes, and other characters
                clean_line = line.strip()
                if clean_line.startswith(('- ', '* ', '• ')):
                    clean_line = clean_line[2:].strip()
                elif clean_line[0].isdigit() and clean_line[1:3] in ['. ', ') ']:
                    clean_line = clean_line[3:].strip()
                
                # Remove quotes if present
                if clean_line.startswith('"') and clean_line.endswith('"'):
                    clean_line = clean_line[1:-1].strip()
                
                if clean_line and clean_line not in ['[', ']', '{', '}']:
                    industries.append(clean_line)
            
            return industries
            
    except Exception as e:
        raise Exception(f"Error inferring industries with Anthropic: {str(e)}")

def classify_website(url, content, industries, provider, api_key):
    """
    Classify a website into an industry based on its content.
    
    Args:
        url (str): The URL of the website
        content (str): The scraped content of the website
        industries (list): List of possible industries
        provider (str): The LLM provider name
        api_key (str): API key for the LLM provider
        
    Returns:
        dict: Classification result with URL, industry, and additional notes
    """
    if provider == "OpenAI":
        return classify_website_openai(url, content, industries, api_key)
    elif provider == "Anthropic":
        return classify_website_anthropic(url, content, industries, api_key)
    else:
        # Default to OpenAI if provider not specifically implemented
        return classify_website_openai(url, content, industries, api_key)

def classify_website_openai(url, content, industries, api_key):
    """
    Classify a website using OpenAI API
    """
    from openai import OpenAI
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    
    # Initialize the API client
    client = OpenAI(api_key=api_key)
    
    # Trim content if too long
    MAX_CONTENT_LENGTH = 12000  # Adjust based on token limits and needs
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH] + "... (content truncated)"
    
    # Format the industries list
    industries_list = "\n".join([f"- {industry}" for industry in industries])
    
    # Construct the prompt
    prompt = f"""Classify the following website into one of the provided industry categories based on its content.
    
    Website URL: {url}
    
    Website Content:
    {content}
    
    Available Industry Categories:
    {industries_list}
    
    If the website doesn't clearly fit any category, classify it as "Other/Miscellaneous".
    
    Respond with a JSON object that contains:
    1. "industry": The most appropriate industry category from the provided list
    2. "additional_notes": Any additional observations or notes about the classification (e.g., subcategories, multiple relevant industries, or challenges in classification)
    
    Format your response ONLY as a JSON object with no additional explanation.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "url": url,
            "industry": result.get("industry", "Unknown"),
            "additional_notes": result.get("additional_notes", "")
        }
    except Exception as e:
        return {
            "url": url,
            "industry": "Unknown",
            "additional_notes": f"Classification failed: {str(e)}"
        }

def classify_website_anthropic(url, content, industries, api_key):
    """
    Classify a website using Anthropic API
    """
    from anthropic import Anthropic
    # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
    
    # Initialize the API client
    client = Anthropic(api_key=api_key)
    
    # Trim content if too long
    MAX_CONTENT_LENGTH = 12000  # Adjust based on token limits and needs
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH] + "... (content truncated)"
    
    # Format the industries list
    industries_list = "\n".join([f"- {industry}" for industry in industries])
    
    # Construct the prompt
    prompt = f"""Classify the following website into one of the provided industry categories based on its content.
    
    Website URL: {url}
    
    Website Content:
    {content}
    
    Available Industry Categories:
    {industries_list}
    
    If the website doesn't clearly fit any category, classify it as "Other/Miscellaneous".
    
    Respond with a JSON object that contains:
    1. "industry": The most appropriate industry category from the provided list
    2. "additional_notes": Any additional observations or notes about the classification (e.g., subcategories, multiple relevant industries, or challenges in classification)
    
    Format your response ONLY as a JSON object with no additional explanation.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        
        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                
                return {
                    "url": url,
                    "industry": result.get("industry", "Unknown"),
                    "additional_notes": result.get("additional_notes", "")
                }
            else:
                # If JSON parsing fails, return basic classification
                return {
                    "url": url,
                    "industry": "Unknown",
                    "additional_notes": "Unable to parse classification result"
                }
        except:
            return {
                "url": url,
                "industry": "Unknown",
                "additional_notes": "Failed to parse classification result"
            }
    except Exception as e:
        return {
            "url": url,
            "industry": "Unknown",
            "additional_notes": f"Classification failed: {str(e)}"
        }
