# 🎮 LoL PDF Generator

A FastAPI web application that generates personalized PDF profiles for League of Legends players. Users can fill out a questionnaire about their gaming experience and receive a beautifully formatted PDF document.

## ✨ Features

- **Modern Web Interface**: Clean, responsive design using Bootstrap
- **Interactive Forms**: User-friendly questionnaire with LoL-specific fields
- **PDF Generation**: Creative, visually appealing PDF documents with player information
- **Database Storage**: PostgreSQL integration to store user submissions
- **Notification System**: Placeholder implementations for email and Slack notifications
- **Professional Design**: Bootstrap primary and light color scheme

## 🛠️ Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **Frontend**: HTML5, Bootstrap 5, CSS3
- **PDF Generation**: ReportLab
- **ORM**: SQLAlchemy
- **ASGI Server**: Uvicorn
- **Template Engine**: Jinja2

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL
- Virtual environment (recommended)

## 🚀 Installation & Setup

### 1. Clone the Repository
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

### 4. Database Setup

#### Create PostgreSQL Database
```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE "lol-pdf-db";
CREATE USER postgres WITH PASSWORD 'root';
GRANT ALL PRIVILEGES ON DATABASE "lol-pdf-db" TO postgres;
```

#### Initialize Database Tables
```bash
# Run the database initialization script
python init_db.py
```

### 5. Environment Configuration

Update the database connection string in `app.py` if needed:
```python
DATABASE_URL = "postgresql://postgres:root@localhost/lol-pdf-db"
```

### 6. Run the Application
```bash
# Method 1: Direct execution
python app.py

# Method 2: Using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at `http://localhost:8000`

## 📱 Usage

1. **Home Page**: Visit the main page and click "LoL Questions"
2. **Fill Form**: Complete the questionnaire with your League of Legends information
   - **Required**: Name and Email
   - **Optional**: Favorite Champion, Rank, Main Role, Years Playing
3. **Generate PDF**: Submit the form to automatically generate and download your personalized PDF
4. **Notifications**: Email and Slack notifications are sent (currently placeholders)

## 🗄️ Database Models

### LoLQuestion
- `id`: Primary key
- `name`: Player name (required)
- `email`: Email address (required)
- `favorite_champion`: Favorite LoL champion
- `rank`: Current game rank
- `main_role`: Primary game role
- `years_playing`: Years of experience
- `created_at`: Submission timestamp

### CIMQuestion
- `id`: Primary key
- `name`: User name (required)
- `email`: Email address (required)
- `company`: Company name
- `position`: Job position
- `experience_years`: Professional experience
- `created_at`: Submission timestamp

## 📄 PDF Features

The generated PDFs include:
- **Creative Design**: Modern layout with Bootstrap color scheme
- **Player Information**: Name, email, submission date
- **Game Statistics**: Champion, rank, role, experience
- **Visual Elements**: Icons, tables, and professional formatting
- **Responsive Layout**: Optimized for printing and digital viewing

## 🔧 Configuration

### Database Configuration
Update the connection string in `app.py`:
```python
DATABASE_URL = "postgresql://username:password@host:port/database"
```

### Environment Variables
For production, use environment variables:
```bash
export DATABASE_URL="postgresql://username:password@host:port/database"
```

## 📧 Notification Setup

### Email Notifications
Replace the placeholder in `send_email_notification()` with actual email service:
- SMTP configuration
- Email templates
- Error handling

### Slack Notifications
Replace the placeholder in `send_slack_notification()` with:
- Slack webhook URL
- Channel configuration
- Message formatting

## 🎨 Customization

### Styling
- Modify `templates/base.html` for global styles
- Update Bootstrap variables in CSS
- Customize PDF styling in `generate_lol_pdf()`

### Form Fields
- Add new fields to the SQLAlchemy models in `app.py`
- Update HTML forms in `templates/lol_form.html`
- Update the FastAPI endpoint parameters
- Modify PDF generation to include new fields

## 📁 Project Structure

```
lol-pdf-gen/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   └── lol_form.html    # Form page
├── static/              # Static assets
│   └── assets/          # Bootstrap files
│       ├── css/         # CSS files
│       └── js/          # JavaScript files
└── venv/               # Virtual environment
```

## 🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check database credentials in `DATABASE_URL`
- Ensure database exists
- Run `python init_db.py` to create tables

### PDF Generation Errors
- Verify ReportLab installation
- Check file permissions for temporary files
- Ensure sufficient disk space

### FastAPI Issues
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is available
- Verify uvicorn is installed

### Bootstrap Assets
- Verify Bootstrap files exist in `static/assets/`
- Check static file mounting in FastAPI
- Ensure proper CSS/JS linking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🎯 Future Enhancements

- [ ] User authentication system
- [ ] Multiple questionnaire types
- [ ] PDF template customization
- [ ] Email service integration
- [ ] Slack webhook implementation
- [ ] File upload capabilities
- [ ] Admin dashboard
- [ ] API endpoints
- [ ] Docker containerization
- [ ] Unit tests

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the Flask and PostgreSQL documentation

---

**Happy Gaming! 🎮**
