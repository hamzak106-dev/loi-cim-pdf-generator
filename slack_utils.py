"""
Slack integration for sending notifications with PDF links
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime


class SlackNotifier:
    """
    Handles sending notifications to Slack via webhooks
    """
    
    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL
            channel: Optional channel override (e.g., '#business-submissions')
        """
        self.webhook_url = webhook_url
        self.channel = channel
    
    def send_pdf_notification(self, 
                            submission_data: Dict[str, Any],
                            drive_url: str,
                            file_name: str,
                            uploaded_file_url: Optional[str] = None) -> bool:
        """
        Send notification about uploaded PDF to Slack
        
        Args:
            submission_data: Dictionary with submission details (name, email, etc.)
            drive_url: Google Drive shareable URL
            file_name: Name of the uploaded PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build message payload
            message = self._build_pdf_message(submission_data, drive_url, file_name, uploaded_file_url)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Slack notification sent successfully")
                return True
            else:
                print(f"❌ Slack notification failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Slack notification timeout")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Slack notification error: {str(e)}")
            return False
    
    def _build_pdf_message(self, 
                       submission_data: Dict[str, Any],
                       drive_url: str,
                       file_name: str,
                       uploaded_file_url: Optional[str] = None) -> dict:
        """
        Build Slack message with blocks for better formatting

        Args:
            submission_data: Submission details
            drive_url: Google Drive URL
            file_name: PDF file name
            uploaded_file_url: Optional URL for the uploaded file

        Returns:
            Slack message payload (dict)
        """
        # Extract data with safe defaults
        full_name = submission_data.get('full_name', 'Unknown')
        email = submission_data.get('email', 'Not provided')
        purchase_price = submission_data.get('formatted_purchase_price', 'Not specified')
        revenue = submission_data.get('formatted_revenue', 'Not specified')
        industry = submission_data.get('industry', 'Not specified')
        location = submission_data.get('location', 'Not specified')

        # Define message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📄 New Business Acquisition PDF Generated"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Submitter:*\n{full_name}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                    {"type": "mrkdwn", "text": f"*Purchase Price:*\n{purchase_price}"},
                    {"type": "mrkdwn", "text": f"*Revenue:*\n{revenue}"},
                    {"type": "mrkdwn", "text": f"*Industry:*\n{industry}"},
                    {"type": "mrkdwn", "text": f"*Location:*\n{location}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*PDF File:* `{file_name}`"
                }
            }
        ]

        # Create action buttons safely
        action_elements = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "📎 View PDF on Google Drive"},
                "url": drive_url,
                "style": "primary"
            }
        ]
        if uploaded_file_url:
            action_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "📄 View Uploaded File"},
                "url": uploaded_file_url
            })

        blocks.append({
            "type": "actions",
            "elements": action_elements
        })

        # Add footer/context block
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        # Build the final message
        message = {"blocks": blocks}

        # Include target channel if specified
        if getattr(self, "channel", None):
            message["channel"] = self.channel

        return message
    
    def send_simple_message(self, text: str) -> bool:
        """
        Send a simple text message to Slack
        
        Args:
            text: Message text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {"text": text}
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Failed to send simple Slack message: {str(e)}")
            return False


def create_slack_notifier(webhook_url: str, channel: Optional[str] = None) -> SlackNotifier:
    """
    Factory function to create a SlackNotifier instance
    
    Args:
        webhook_url: Slack webhook URL
        channel: Optional channel name
        
    Returns:
        SlackNotifier instance
    """
    return SlackNotifier(webhook_url, channel)
