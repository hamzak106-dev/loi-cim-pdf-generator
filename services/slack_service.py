"""
Slack Service
Handles sending notifications to Slack via webhooks
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
            uploaded_file_url: Optional URL for uploaded file
            
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
                    "text": "New Business Acquisition PDF Generated"
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
                "text": {"type": "plain_text", "text": "View PDF on Google Drive"},
                "url": drive_url,
                "style": "primary"
            }
        ]
        if uploaded_file_url:
            action_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "View Uploaded File"},
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
        if self.channel:
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
    
    def send_success_notification(self, form_type: str, full_name: str, email: str, drive_url: str) -> bool:
        """
        Send success notification when PDF is generated and email is sent successfully
        
        Args:
            form_type: "LOI", "CIM", or "CIM_TRAINING"
            full_name: Submitter's full name
            email: Submitter's email
            drive_url: Google Drive URL for the PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format form type for display
            form_label = form_type.upper() if form_type else "PDF"
            
            # Build simple message
            message_text = f"""New {form_label} PDF generated
Submitter: {full_name}
Email: {email}
View PDF on Google Drive: {drive_url}"""
            
            payload = {"text": message_text}
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Success Slack notification sent")
                return True
            else:
                print(f"❌ Success Slack notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send success Slack notification: {str(e)}")
            return False
    
    def send_failure_notification(self, form_type: str, full_name: str, email: str, error_type: str, drive_url: str = None) -> bool:
        """
        Send failure notification when PDF generation or email sending fails
        
        Args:
            form_type: "LOI", "CIM", or "CIM_TRAINING"
            full_name: Submitter's full name
            email: Submitter's email
            error_type: "GENERATE" or "SEND"
            drive_url: Optional Google Drive URL (if PDF was generated but email failed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format form type for display
            form_label = form_type.upper() if form_type else "PDF"
            
            # Build failure message
            error_action = "GENERATE" if error_type == "GENERATE" else "SEND"
            message_text = f"""❌ {form_label} PDF generated failed
Error: Failed to {error_action}
Submitter: {full_name}
Email: {email}"""
            
            # Add Drive URL if available
            if drive_url:
                message_text += f"\nView PDF on Google Drive: {drive_url}"
            
            payload = {"text": message_text}
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Failure Slack notification sent")
                return True
            else:
                print(f"❌ Failure Slack notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send failure Slack notification: {str(e)}")
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
