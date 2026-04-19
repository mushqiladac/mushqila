# Mushqila - Travel Agency Management System

A comprehensive Django-based travel agency management system with integrated webmail, flight booking (Galileo GDS), B2C customer portal, and accounting features.

## Features

### 🎫 Flight Booking System
- Galileo GDS integration for real-time flight search and booking
- Multi-airline support
- PNR management
- Ticket issuance and void
- Booking history and reports

### 📧 Webmail System
- AWS SES integration for email sending/receiving
- Individual inbox for each email account
- Password management with forgot password feature
- S3-based email storage
- Automatic email account setup

### 👥 User Management
- Multi-level user hierarchy (Admin, Agent, Sub-agent)
- Role-based access control
- Commission management
- Agent balance tracking

### 💼 B2C Customer Portal
- Customer registration and login
- Booking management
- Loyalty program
- Referral system
- Support ticket system

### 💰 Accounting System
- Automated transaction tracking
- Commission calculations
- Financial reporting
- Invoice generation
- Agent balance management

## Tech Stack

- **Backend**: Django 5.0+
- **Database**: PostgreSQL
- **Cloud Services**: AWS (SES, S3)
- **GDS**: Galileo/Travelport
- **Frontend**: Bootstrap 5, JavaScript
- **Deployment**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- AWS Account (for SES and S3)
- Galileo GDS credentials (for flight booking)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila
```

2. Create virtual environment:
```bash
python -m venv menv
source menv/bin/activate  # On Windows: menv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Setup Guides
- [Deployment Guide](docs/DEPLOYMENT-GUIDE.md)
- [AWS Setup (Bangla)](docs/AWS-SETUP-BANGLA-GUIDE.md)
- [Deploy Guide (Bangla)](docs/DEPLOY-BANGLA-GUIDE.md)
- [Quick Setup Reference](docs/QUICK-SETUP-REFERENCE.md)
- [GitHub Actions Setup](docs/GITHUB-ACTIONS-SETUP.md)

### Feature Documentation
- [Webmail Account Management](docs/WEBMAIL-ACCOUNT-MANAGEMENT.md)
- [Webmail Forgot Password](docs/WEBMAIL-FORGOT-PASSWORD-FEATURE.md)
- [Webmail Update Summary](docs/WEBMAIL-UPDATE-SUMMARY.md)
- [Webmail Setup Complete](docs/WEBMAIL-SETUP-COMPLETE.md)
- [AWS SES Webmail Setup](docs/AWS-SES-WEBMAIL-COMPLETE-SETUP.md)
- [AWS SES Quick Start (Bangla)](docs/AWS-SES-QUICK-START-BANGLA.md)
- [AWS SES Email Receiving](docs/AWS-SES-EMAIL-RECEIVING-SETUP.md)
- [Galileo Integration Guide](docs/GALILEO-API-INTEGRATION-GUIDE.md)
- [Galileo Setup](docs/GALILEO-SETUP.md)
- [Galileo Integration Checklist](docs/GALILEO-INTEGRATION-CHECKLIST.md)
- [Galileo Integration Ready](docs/GALILEO-INTEGRATION-READY.md)
- [B2C Setup Complete](docs/B2C-SETUP-COMPLETE.md)

## Project Structure

```
mushqila/
├── accounts/          # User management and authentication
├── b2c/              # B2C customer portal
├── config/           # Django settings and configuration
├── flights/          # Flight booking and GDS integration
├── webmail/          # Webmail system
├── static/           # Static files (CSS, JS, images)
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```

## Key Management Commands

### Webmail Commands

```bash
# Create new email account
python manage.py create_webmail_account \
  --email user@mushqila.com \
  --password SecurePass123 \
  --first-name "User" \
  --last-name "Name"

# Setup all email accounts in AWS SES
python manage.py setup_all_email_accounts

# Verify email accounts
python manage.py verify_email_accounts

# Set default passwords for existing accounts
python manage.py set_default_passwords
```

### Accounting Commands

```bash
# Initialize accounting system
python manage.py setup_accounting

# Initialize accounts
python manage.py initialize_accounts

# Delete demo data
python manage.py delete_demo_data
```

### Flight Commands

```bash
# Load airports data
python manage.py load_airports
```

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=mushqila_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=mushqila-emails

# Email
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
DEFAULT_FROM_EMAIL=noreply@mushqila.com

# Galileo GDS
GALILEO_USERNAME=your-username
GALILEO_PASSWORD=your-password
GALILEO_TARGET_BRANCH=your-branch
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

See [Deployment Guide](docs/DEPLOYMENT-GUIDE.md) for detailed production deployment instructions.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions:
- Email: support@mushqila.com
- Documentation: See `docs/` directory

## Acknowledgments

- Django Framework
- AWS Services (SES, S3)
- Galileo/Travelport GDS
- Bootstrap Framework
