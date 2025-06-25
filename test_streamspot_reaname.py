"""
Script to log into Streamspot and rename videos based on WordPress post titles.
Uses WordPress API to get post titles and matches them with Streamspot videos.
Outlook Desktop application MUST be open for the verifyEmail to work.
verifyEmailGraph does not require Outlook to be open. 

"""

import requests
import time
import os
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import logging
import logging.handlers
from functions.getEmailLink import verifyEmailGraph
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging to file only
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "streamspot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=log_file,
    filemode='a'
)

url = "https://mystreamspot.com"
values = {
    "username": os.environ.get("STREAMSPOT_USERNAME"),
    "password": os.environ.get("STREAMSPOT_PASSWORD"),
}
mydate = date.today()

# WordPress API settings
wp_api_url = os.getenv("WP_API_URL")
if not wp_api_url:
    logging.error("WP_API_URL environment variable not set")
    wp_url = None
else:
    wp_url = wp_api_url + "posts?categories=48&per_page=3"

wp_username = os.getenv("WP_API_USER")
wp_password = os.getenv("WP_API_PASSWORD")
wp_headers = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


def open_session():
    global session
    global response
    global url

    # open session
    session = requests.session()
    logging.info("Opening session")

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logging.debug("Login response: " + response.url)
    logging.info("Checking for email verification")
    verifylink = verifyEmailGraph()
    response = session.get(verifylink, allow_redirects=True)
    logging.info(response.request.headers)
    logging.info(response.url)

    return response


def get_archive_data():
    """Get archive data from Streamspot"""
    global session
    global url
    
    logging.debug("Entering get_archive_data()")
    
    try:
        archive_url = url + "/archive/ajax/archives.php"
        response = session.get(archive_url, timeout=20)
        
        if response.status_code == 200:
            logging.info("Successfully retrieved archive data")
            logging.debug(f"Archive data response length: {len(response.text)}")
            
            # The response is a JSON array of archives
            try:
                archive_data = response.json()
                logging.info(f"Found {len(archive_data)} archives")
                return {'rows': archive_data}  # Wrap in dict
                    
            except Exception as e:
                logging.error(f"Failed to parse archive JSON: {str(e)}")
                logging.debug(f"Raw response: {response.text[:500]}...")
                return None
        else:
            logging.error(f"Failed to get archive data. Status code: {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting archive data: {str(e)}")
        return None
    


def navigate_to_archive():
    global response
    global session
    global url

    logging.debug("Entering navigate_to_archive()")
    
    # Navigate to archive page
    time.sleep(15)
    response = session.get(url + "/archive/", timeout=20)
    logging.info("Archive page response URL: " + response.url)
    logging.info("Archive page status code: " + str(response.status_code))
    
    if response.status_code == 200:
        logging.info("Successfully navigated to archive page")
        
        # Get the archive data and process with WordPress matching
        archive_data = get_archive_data()
        if archive_data:
            # Get WordPress post information
            wp_posts = get_wordpress_info()
            if wp_posts:
                # Process archives and match with WordPress posts by date
                renamed_count = match_videos(archive_data['rows'], wp_posts)
                logging.info(f"Rename operation completed. {renamed_count} videos renamed.")
            else:
                logging.warning("No WordPress posts found for matching")

        else:
            logging.error("No archive data available")
        
    else:
        logging.error(f"Failed to access archive page. Status code: {response.status_code}")
    
    logging.debug("Leaving navigate_to_archive()")
    return response


def process_archive_data(archive_data):
    """Process the archive data to find and rename videos"""
    logging.debug("Entering process_archive_data()")
    
    if not archive_data or 'rows' not in archive_data:
        logging.warning("No archive data to process")
        return
    
    archives = archive_data['rows']
    logging.info(f"Processing {len(archives)} archives")
    
    # Debug: Log the structure of the first archive item
    if archives:
        logging.debug(f"First archive keys: {list(archives[0].keys()) if isinstance(archives[0], dict) else 'Not a dict'}")
    
    logging.debug("Leaving process_archive_data()")


def extract_video_info(archive_item):
    """Extract  information from an archive item"""
    try:
        logging.debug(f"Extracting info from archive item: {list(archive_item.keys()) if isinstance(archive_item, dict) else 'Not a dict'}")

        import json
        if isinstance(archive_item['data'], str):
            data = json.loads(archive_item['data'])
        else:
            data = archive_item['data']

        
        # Extract common fields that might be at different levels
        video_info = {
            'id_hash': data.get('idHash') or archive_item.get('idHash'),
            'title': data.get('title') or archive_item.get('title', 'Unknown'),
            'date': archive_item.get('date') or data.get('date'),
            'platform': data.get('platform') or archive_item.get('platform', 'gen3'),
            'visible': not (data.get('is_hidden', False) or archive_item.get('is_hidden', False)),
            'category': archive_item.get('category') or data.get('category'),
            'expiration': archive_item.get('expiration') or data.get('expiration')
        }
        
        logging.info(f"Extracted video info: ID={video_info['id_hash']}, Title='{video_info['title']}'")
        logging.debug(f"Full video info: {video_info}")
        return video_info
        
    except Exception as e:
        logging.error(f"Error extracting video info: {str(e)}")
        logging.debug(f"Archive item structure: {str(archive_item)[:300]}...")
        return None


def get_wordpress_info():
    """Get 3 WordPress posts and extract titles and dates"""
    logging.debug("Entering get_wordpress_info()")
    
    # Check if WordPress URL is configured
    if not wp_url:
        logging.error("WordPress API URL not configured. Please set WP_API_URL environment variable.")
        return []
    
    try:
        response = requests.get(wp_url, headers=wp_headers)
        response.raise_for_status()
        posts = response.json()
        logging.info(f"Retrieved {len(posts)} WordPress posts")
    except Exception as e:
        logging.error(f"Failed to retrieve WordPress posts: {e}")
        return []
    
    wp_posts = []
    
    for post in posts:
        # Extract date from post (assuming it's in the post date field)
        post_date = post['date'][:10]  # Get YYYY-MM-DD format
        post_title = post['title']['rendered']
        
        # Clean the title for Streamspot
        clean_title = sanitize_title_for_streamspot(post_title)
        
        wp_posts.append({
            'date': post_date,
            'title': post_title,
            'clean_title': clean_title
        })
        
        logging.info(f"WordPress Post: Date={post_date}, Title='{post_title}', Clean='{clean_title}'")

    logging.debug("Leaving get_wordpress_info()")
    return wp_posts


def sanitize_title_for_streamspot(title):
    """Clean title for Streamspot compatibility"""
    import html
    
    # Decode HTML entities (&#038; -> &, etc.)
    clean_title = html.unescape(title)
    
    # Replace characters that Streamspot doesn't allow
    replacements = {
        ':': '_',           # Colon to underscore
        '&': 'and',         # Ampersand to 'and'
        ',': '',            # Remove commas (they seem to cause issues)
        '<': '',            # Remove less than
        '>': '',            # Remove greater than
        '"': '',            # Remove quotes
        "'": '',            # Remove single quotes
        '|': '-',           # Pipe to dash
        '\\': '-',          # Backslash to dash
        '/': '-',           # Forward slash to dash
        '*': '',            # Remove asterisk
        '?': '',            # Remove question mark
        '[': '',            # Remove square brackets
        ']': '',            # Remove square brackets
        '(': '',            # Remove parentheses
        ')': '',            # Remove parentheses
        '{': '',            # Remove curly braces
        '}': '',            # Remove curly braces
    }
    
    for char, replacement in replacements.items():
        clean_title = clean_title.replace(char, replacement)
    
    # Clean up any double spaces or dashes
    clean_title = re.sub(r'\s+', ' ', clean_title)  # Multiple spaces to single space
    clean_title = re.sub(r'-+', '-', clean_title)   # Multiple dashes to single dash
    clean_title = clean_title.strip()               # Remove leading/trailing whitespace
    
    logging.debug(f"Sanitized '{title}' to '{clean_title}'")
    return clean_title


def parse_streamspot_date(date_string):
    """Parse Streamspot date format to YYYY-MM-DD"""
    try:
        # Handle None or empty date
        if not date_string:
            logging.warning("Date string is None or empty")
            return None
            
        # Streamspot format: "Mon 06/16/25"
        # Extract the date and convert to YYYY-MM-DD format
        from datetime import datetime
        
        # HTML content, try to extract date
        if '<' in str(date_string):
            import re
            date_match = re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', str(date_string))
            if date_match:
                date_part = date_match.group()
            else:
                logging.warning(f"No date pattern found in HTML content: {str(date_string)[:100]}...")
                return None
        else:
            # Remove day name and parse the date
            date_part = str(date_string).split(' ')[1] if ' ' in str(date_string) else str(date_string)
        
        # Parse the date (MM/DD/YY or MM/DD/YYYY)
        month, day, year = date_part.split('/')
        
        # Convert 2-digit year to 4-digit year
        if len(year) == 2:
            full_year = f"20{year}"
        else:
            full_year = year
        
        # Create proper date format YYYY-MM-DD
        formatted_date = f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"
        
        logging.debug(f"Converted '{date_string}' to '{formatted_date}'")
        return formatted_date
        
    except Exception as e:
        logging.error(f"Error parsing Streamspot date '{date_string}': {e}")
        return None


def match_videos(archives, wp_posts):
    """Match Streamspot videos with WordPress posts by date and rename them"""
    logging.debug("Entering match_videos()")
    
    renamed_count = 0
    
    for archive in archives:
        video_info = extract_video_info(archive)
        if not video_info:
            continue
            
        current_title = video_info['title']
        video_date_raw = video_info['date']
        
        # Parse the Streamspot date
        video_date = parse_streamspot_date(video_date_raw)
        if not video_date:
            logging.warning(f"Could not parse date for video: {current_title}")
            continue
            
        logging.debug(f"Processing video: '{current_title}' from {video_date}")
        
        # Find WordPress post with matching date
        matching_wp_post = None
        for wp_post in wp_posts:
            if wp_post['date'] == video_date:
                matching_wp_post = wp_post
                break
        
        if matching_wp_post:
            new_title = matching_wp_post['clean_title']
            logging.info(f"Date match found! Video date: {video_date}, WP title: '{matching_wp_post['title']}'")
            
            # Only rename if the titles are different
            if current_title != new_title:
                success = rename_video(video_info, new_title)
                if success:
                    logging.info(f"Successfully renamed '{current_title}' to '{new_title}'")
                    renamed_count += 1
                else:
                    logging.error(f"Failed to rename video: {video_info['id_hash']}")
            else:
                logging.info(f"Video '{current_title}' already has correct title, skipping")
        else:
            logging.debug(f"No WordPress post found for date: {video_date}")
    
    logging.info(f"Total videos renamed: {renamed_count}")
    logging.debug("Leaving match_videos()")
    return renamed_count


def rename_video(video_data, new_title):
    """Rename a video using the same endpoint the page uses"""
    global session
    global url
    
    logging.debug(f"Entering rename_video() for {video_data['id_hash']}")
    
    try:
        # Use the same endpoint as the JavaScript function updateName()
        query_params = {
            'title': new_title,
            'idHash': video_data['id_hash'],
            'platform': video_data.get('platform', 'gen3')
        }
        
        update_url = url + "/archive/ajax/update_video.php"
        response = session.get(update_url, params=query_params, timeout=20)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    logging.info(f"Successfully renamed video to '{new_title}'")
                    return True
                else:
                    error_msg = result.get('error', {}).get('title', 'Unknown error')
                    logging.error(f"Failed to rename video: {error_msg}")
                    return False
            except Exception as e:
                logging.error(f"Error parsing rename response: {str(e)}")
                return False
        else:
            logging.error(f"Rename request failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error renaming video: {str(e)}")
        return False
    


def main():
    try:
        # Open session and log in
        open_session()
        
        # Navigate to archive page and process archives
        navigate_to_archive()
        
        logging.info("Streamspot rename script completed successfully")
        
        # Send success email
        message = Mail(
            from_email=os.environ.get("EMAIL_FROM"),
            to_emails=os.environ.get("EMAIL_TO"),
            subject="Streamspot rename script ran successfully",
            html_content="This email indicates that the streamspot rename script ran without errors. <p>There is no guarantee that it ran correctly.</p>",
        )

        try:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            response = sg.send(message)
            logging.info("Success email sent")

        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            
    except Exception as e:
        logging.error(f"Script failed with error: {str(e)}")
        
        # Or send error email
        error_message = Mail(
            from_email=os.environ.get("EMAIL_FROM"),
            to_emails=os.environ.get("EMAIL_TO"),
            subject="Streamspot rename script failed",
            html_content=f"The streamspot rename script encountered an error: <p>{str(e)}</p>",
        )
        
        try:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            sg.send(error_message)
        except:
            pass  # Don't fail if we can't send the error email


if __name__ == "__main__":
    main()