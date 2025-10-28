# LOI Questions PDF Generator

A FastAPI-based application that generates professional Letter of Intent PDFs for business acquisitions, with automated email delivery, Google Drive storage, and Slack notifications.

## Features

- 📝 Web form for LOI questions submissions
- 📄 Professional PDF generation with custom styling
- 📧 Automated email delivery with PDF attachments
- ☁️ Google Drive upload (Shared Drive support)
- 💬 Slack notifications with Drive links
- ⚡ Background processing with Celery
- 🗄️ PostgreSQL database storage

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy
- **Task Queue**: Celery with Redis
- **PDF Generation**: ReportLab
- **Email**: SMTP (Gmail)
- **Cloud Storage**: Google Drive API
- **Notifications**: Slack Webhooks

## Project Structure

```
lol-pdf-gen/
├── app.py                  # FastAPI application entry point
├── views.py                # Route handlers
├── models.py               # Database models
├── services.py             # Email, PDF, Slack services
├── tasks.py                # Celery background tasks
├── google_drive.py         # Google Drive integration
├── slack_utils.py          # Slack notification utilities
├── config.py               # Configuration settings
├── database.py             # Database connection
├── celery_app.py           # Celery configuration
├── templates/              # HTML templates
│   ├── index.html
│   └── business_form.html
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── service_account.json    # Google service account credentials

```

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd lol-pdf-gen
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL Database
```bash
createdb lol-pdf-db
```

### 5. Configure Environment Variables
Create a `.env` file:
```bash
# Database
DATABASE_URL=postgresql://postgres:root@localhost/lol-pdf-db

# Email (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Drive (Shared Drive)
GOOGLE_DRIVE_FOLDER_ID=your-shared-drive-folder-id
GOOGLE_DRIVE_CREDENTIALS_PATH=service_account.json

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#business-submissions

# Application
DEBUG=True
HOST=0.0.0.0
PORT=8000s
SECRET_KEY=your-secret-key-change-in-production
```

### 6. Google Drive Setup
1. Create a Google Cloud project
2. Enable Google Drive API
3. Create a service account
4. Download `service_account.json` to project root
5. Create a Shared Drive folder
6. Share folder with service account email
7. Copy folder ID to `.env`

### 7. Slack Setup
1. Create a Slack app
2. Enable Incoming Webhooks
3. Add webhook to your channel
4. Copy webhook URL to `.env`

## Running the Application

### Start Services

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
celery -A celery_app.celery_app worker --loglevel=info
```

**Terminal 3 - FastAPI:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Access Application
- Web Interface: `http://localhost:8000`
- Business Form: `http://localhost:8000/business-form`
- API Health: `http://localhost:8000/health`

## Workflow

1. **User submits form** → Data saved to PostgreSQL
2. **Celery task starts** → Background processing begins
3. **PDF generated** → Professional Letter of Intent created
4. **Upload to Google Drive** → PDF stored in Shared Drive
5. **Email sent** → PDF attached to confirmation email
6. **Slack notification** → Team notified with Drive link
7. **Cleanup** → Temporary files removed

## API Endpoints

### Pages
- `GET /` - Home page
- `GET /business-form` - Submission form
- `POST /submit-business` - Handle form submission

### API
- `GET /api/submissions` - List all submissions
- `GET /api/submissions/{id}` - Get specific submission
- `GET /api/submissions/{id}/pdf` - Regenerate PDF
- `GET /health` - Health check

## Testing

### Verify Setup
```bash
python verify_setup.py
```

Expected output:
```
✅ Environment Config: OK
✅ Google Drive: OK
✅ Slack: OK
🎉 All systems ready\!
```

### Test Submission
1. Navigate to `http://localhost:0/business-form`
2. Fill out the form
3. Submit
4. Check Celery logs for processing status
5. Verify email received
6. Check Google Drive for PDF
7. Check Slack for notification

## Configuration

### Email Settings
- Uses Gmail SMTP by default
- Requires app-specific password
- Supports TLS encryption

### Google Drive
- Uses service account authentication
- Supports Shared Drives with `supportsAllDrives=True`
- Generates shareable links automatically

### Slack
- Rich formatted messages with blocks
- Includes submission details
- Clickable Drive link button

## Troubleshooting

### Google Drive Upload Fails
- Verify `service_account.json` exists
- Check folder is shared with service account
- Ensure `GOOGLE_DRIVE_FOLDER_ID` is correct
- Confirm Shared Drive permissions

### Email Not Sending
- Verify SMTP credentials
- Check app password (not regular password)
- Ensure "Less secure apps" enabled (if applicable)

### Celery Task Not Running
- Confirm Redis is running: `redis-cli ping`
- Check Celery worker is started
- Review Celery logs for errors

### Slack Notification Fails
- Verify webhook URL is correct
- Test webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`
- Check channel permissions

## Development

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### Code Style
- Follow PEP 8
- Use type hints
- Keep functions focused and simple
- Minimal comments, self-documenting code

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS
- [ ] Restrict CORS origins
- [ ] Use production-grade database
- [ ] Configure proper logging
- [ ] Set up monitoring

### Performance
- Use Gunicorn/Uvicorn workers
- Configure Celery concurrency
- Enable Redis persistence
- Optimize database queries
- Implement caching

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
