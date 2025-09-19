# Farmer's Assistant

A full-stack web application for farmers to get weather forecasts, disease alerts, and purchase fertilizers.

## Features

- User authentication system
- Weather forecasting dashboard
- Farming alerts and disease information
- Fertilizer e-commerce section
- Responsive design for all devices

## Installation

1. Clone or download this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python app.py`
6. Open your browser and go to `http://localhost:5000`

## Deployment

### Heroku Deployment

1. Create a Heroku account and install the Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set secret key: `heroku config:set SECRET_KEY=your-secret-key`
5. Deploy: `git push heroku master`

### Other Platforms

The app can be deployed to:
- AWS Elastic Beanstalk
- PythonAnywhere
- DigitalOcean App Platform
- Google App Engine

## Database

The application uses SQLite by default (good for development). For production, consider using PostgreSQL.

## License

This project is licensed under the MIT License.