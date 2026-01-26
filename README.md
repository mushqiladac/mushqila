# Mushqila - B2B Flight Booking System

একটি সম্পূর্ণ B2B flight booking management system যা Travelport Galileo GDS integration সহ তৈরি।

## 🌟 Features

- ✈️ **Flight Search**: Travelport Galileo GDS দিয়ে real-time flight search
- 🎫 **Complete Ticket Management**: 
  - ✅ Booking (PNR creation)
  - ✅ Issue (Ticket issuance)
  - ✅ Reissue (Ticket exchange)
  - ✅ Refund (Full/Partial refund)
  - ✅ Void (Within 24 hours)
  - ✅ Cancel (Booking cancellation)
- 👥 **User Management**: Multi-role authentication (Admin, Agent, Supplier)
- 💰 **Financial Management**: Wallet, commission, invoicing
- 📧 **Email Notifications**: AWS SES integration
- 🐳 **Docker Deployment**: Production-ready containerized deployment
- 🔄 **CI/CD**: GitHub Actions automatic deployment

## 🚀 Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/mushqiladac/mushqila.git
cd mushqila

# Using Docker
docker-compose up --build

# Access at http://localhost:8000
```

### AWS Production Deployment
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.104.186

# Run setup (one-time)
cd /home/ubuntu/mushqila
chmod +x setup-ec2.sh
./setup-ec2.sh

# Deploy
./deploy.sh
```

**বিস্তারিত দেখুন:** [QUICK-START.md](QUICK-START.md) | [DEPLOYMENT.md](DEPLOYMENT.md)

## 📋 AWS Infrastructure

- **EC2 Instance**: `i-035811fd86b8a4974`
- **Elastic IP**: `16.170.104.186`
- **RDS PostgreSQL**: `database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com`
- **AWS SES**: Configured for email notifications
- **GitHub CI/CD**: Auto-deployment on push to main

## 🔧 Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL (AWS RDS)
- **Cache/Queue**: Redis, Celery
- **GDS Integration**: Travelport Galileo REST API
- **Deployment**: Docker, Docker Compose, GitHub Actions
- **Email**: AWS SES SMTP
- **Web Server**: Gunicorn + WhiteNoise

## 📚 Documentation

- [Quick Start Guide](QUICK-START.md) - দ্রুত deployment শুরু করুন
- [Deployment Guide](DEPLOYMENT.md) - সম্পূর্ণ deployment documentation
- [Galileo Setup Guide](GALILEO-SETUP.md) - Galileo API integration সম্পূর্ণ guide
- [Galileo Quick Reference](GALILEO-QUICK-REFERENCE.md) - দ্রুত code examples

## 🔐 Environment Variables

### Production (.env.production)
```bash
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=16.170.104.186,mushqila.com

# AWS RDS
DB_HOST=database-1.c3mceceowav8.eu-north-1.rds.amazonaws.com
DB_NAME=mushqila
DB_USER=postgres
DB_PASSWORD=your-password

# AWS SES
EMAIL_HOST=email-smtp.eu-north-1.amazonaws.com
EMAIL_HOST_USER=AKIAUQETDVDPECKLURNW
EMAIL_HOST_PASSWORD=your-ses-password

# Travelport Galileo
TRAVELPORT_USERNAME=your-username
TRAVELPORT_PASSWORD=your-password
TRAVELPORT_BRANCH_CODE=P702214
```

## 🛠️ Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic
```

## 📞 Support

- **GitHub Issues**: [Create an issue](https://github.com/mushqiladac/mushqila/issues)
- **Email**: support@mushqila.com
- **Website**: https://mushqila.com

## 📄 License

Proprietary - All rights reserved

---

Made with ❤️ for B2B travel industry