"""
Script to log into Streamspot and navigate to the archive page.
Outlook Desktop application MUST be open for the verifyEmail to work.
verifyEmailGraph does not require Outlook to be open. 

"""

import requests
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import logging
import logging.handlers
from functions.getEmailLink import verifyEmailGraph


# Setup logging to both file and console
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "streamspot_rename.log")

# Clear any existing handlers
logger = logging.getLogger()
logger.handlers.clear()

# Set up formatter
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")

# File handler
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

logging.info(f"Log file location: {log_file}")

# Test write to verify file logging works
try:
    with open(log_file, 'a') as test_file:
        test_file.write(f"{formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None))} INFO Log file write test successful\n")
    logging.info("Log file write test completed")
except Exception as e:
    print(f"Error writing to log file: {e}")


url = "https://mystreamspot.com"
values = {
    "username": os.environ.get("STREAMSPOT_USERNAME"),
    "password": os.environ.get("STREAMSPOT_PASSWORD"),
}
mydate = date.today()


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
        
        # Get the archive data via AJAX endpoint (same as the page uses)
        archive_data = get_archive_data()
        if archive_data:
            process_archive_data(archive_data)
        
    else:
        logging.error(f"Failed to access archive page. Status code: {response.status_code}")
    
    logging.debug("Leaving navigate_to_archive()")
    return response


def get_archive_data():
    """Get archive data from the AJAX endpoint that the page uses"""
    global session
    global url
    
    logging.debug("Entering get_archive_data()")
    
    try:
        # Call the same AJAX endpoint the page uses to get archive data
        ajax_url = url + "/archive/ajax/archives.php"
        response = session.get(ajax_url, timeout=20)
        
        if response.status_code == 200:
            logging.info("Successfully retrieved archive data")
            logging.debug(f"Archive data response length: {len(response.text)}")
            
            # The response should be JSON data
            try:
                archive_data = response.json()
                
                # Check if it's a list (direct array) or dict with 'rows' key
                if isinstance(archive_data, list):
                    logging.info(f"Found {len(archive_data)} archives (direct list)")
                    return {'rows': archive_data}  # Wrap in dict for consistency
                elif isinstance(archive_data, dict) and 'rows' in archive_data:
                    logging.info(f"Found {len(archive_data['rows'])} archives (rows object)")
                    return archive_data
                else:
                    logging.warning(f"Unexpected archive data format: {type(archive_data)}")
                    logging.debug(f"Data keys: {list(archive_data.keys()) if isinstance(archive_data, dict) else 'Not a dict'}")
                    return None
                    
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
    
    logging.debug("Leaving get_archive_data()")


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
        logging.debug(f"First archive sample: {str(archives[0])[:200]}...")
    
    # Find the most recent archive (they should be sorted by date)
    if archives:
        most_recent = archives[0]  # Assuming first item is most recent
        
        # Extract video information
        video_data = extract_video_info(most_recent)
        if video_data:
            logging.info(f"Most recent video: {video_data}")
            
            # Here you can add logic to rename the video
            # rename_video(video_data)
    
    logging.debug("Leaving process_archive_data()")


def extract_video_info(archive_item):
    """Extract relevant information from an archive item"""
    try:
        logging.debug(f"Extracting info from archive item: {list(archive_item.keys()) if isinstance(archive_item, dict) else 'Not a dict'}")
        
        # The data might be structured differently, let's handle various formats
        if 'data' in archive_item:
            # If there's a 'data' field with JSON string
            import json
            if isinstance(archive_item['data'], str):
                data = json.loads(archive_item['data'])
            else:
                data = archive_item['data']
        else:
            # If the data is directly in the archive_item
            data = archive_item
        
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


def rename_video(video_data, new_title):
    """Rename a video using the same endpoint the page uses"""
    global session
    global url
    
    logging.debug(f"Entering rename_video() for {video_data['id_hash']}")
    
    try:
        # Use the same update endpoint as the JavaScript function updateName()
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
    
    logging.debug("Leaving rename_video()")


def main():
    try:
        # Open session and log in
        open_session()
        
        # Navigate to archive page and process archives
        navigate_to_archive()
        
        # Example: Rename the most recent video
        # You can modify this logic based on your needs
        example_rename_recent_video()
        
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
        
        # Send error email
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


def example_rename_recent_video():
    """Example function showing how to rename the most recent video"""
    logging.debug("Entering example_rename_recent_video()")
    
    # Get fresh archive data
    archive_data = get_archive_data()
    if not archive_data or not archive_data.get('rows'):
        logging.warning("No archives found to rename")
        return
    
    # Get the most recent video
    most_recent = archive_data['rows'][0]
    video_info = extract_video_info(most_recent)
    
    if video_info:
        current_title = video_info['title']
        logging.info(f"Current title: '{current_title}'")
        
        # Example renaming logic - modify this as needed
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        new_title = f"Sunday Service - {today}"
        
        # Only rename if the title is different
        if current_title != new_title:
            success = rename_video(video_info, new_title)
            if success:
                logging.info(f"Successfully renamed video from '{current_title}' to '{new_title}'")
            else:
                logging.error(f"Failed to rename video")
        else:
            logging.info("Video title is already correct, no rename needed")
    
    logging.debug("Leaving example_rename_recent_video()")


if __name__ == "__main__":
    main()