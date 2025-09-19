
import os
from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farmers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Add this line

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Weather API Configuration
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'c755f4d85a3789cc9d3a47a524309386')
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Custom template filter for Indian currency format
@app.template_filter('inr')
def format_inr(value):
    """Format value as INR currency."""
    try:
        value = float(value)
        # Format with comma separators and ₹ symbol
        if value.is_integer():
            return f"₹{int(value):,}"
        else:
            return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return f"₹0"

# Indian crop data
INDIAN_CROPS = {
    'rice': {'seasons': ['Kharif'], 'states': ['West Bengal', 'UP', 'Punjab', 'AP']},
    'wheat': {'seasons': ['Rabi'], 'states': ['UP', 'Punjab', 'Haryana', 'MP']},
    'sugarcane': {'seasons': ['Whole Year'], 'states': ['UP', 'Maharashtra', 'Karnataka']},
    'cotton': {'seasons': ['Kharif'], 'states': ['Gujarat', 'Maharashtra', 'Telangana']},
    'maize': {'seasons': ['Kharif', 'Rabi'], 'states': ['Karnataka', 'MP', 'Maharashtra']},
    'pulses': {'seasons': ['Rabi', 'Kharif'], 'states': ['MP', 'Maharashtra', 'Rajasthan']},
    'oilseeds': {'seasons': ['Kharif', 'Rabi'], 'states': ['Gujarat', 'Rajasthan', 'MP']},
    'fruits': {'seasons': ['Whole Year'], 'states': ['Maharashtra', 'AP', 'Karnataka']},
    'vegetables': {'seasons': ['Whole Year'], 'states': ['West Bengal', 'UP', 'Bihar']}
}

# Indian government schemes
GOVERNMENT_SCHEMES = [
    {
        'name': 'PM-KISAN',
        'description': 'Financial assistance of ₹6,000 per year to small and marginal farmers',
        'eligibility': 'Small and marginal farmers',
        'link': 'https://pmkisan.gov.in'
    },
    {
        'name': 'Soil Health Card',
        'description': 'Provides soil health information and recommendations to farmers',
        'eligibility': 'All farmers',
        'link': 'https://soilhealth.dac.gov.in'
    },
    {
        'name': 'Pradhan Mantri Fasal Bima Yojana',
        'description': 'Crop insurance scheme to protect farmers against crop losses',
        'eligibility': 'All farmers',
        'link': 'https://pmfby.gov.in'
    },
    {
        'name': 'Kisan Credit Card',
        'description': 'Credit card for farmers with flexible repayment options',
        'eligibility': 'All farmers',
        'link': 'https://www.agriculture.gov.in'
    }
]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    farm_location = db.Column(db.String(200))
    farm_size = db.Column(db.Float)
    crops = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    language = db.Column(db.String(10), default='en')  # 'en' or 'hi'
    soil_type = db.Column(db.String(50))
    subscription = db.Column(db.Boolean, default=False)  # Weather alerts subscription
    
    # Relationship with orders
    orders = db.relationship('Order', backref='user_ref', lazy=True)
    # Relationship with forum posts
    posts = db.relationship('ForumPost', backref='author', lazy=True)
    # Relationship with comments
    comments = db.relationship('ForumComment', backref='author', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    in_stock = db.Column(db.Boolean, default=True)
    
    # Relationship with orders
    orders = db.relationship('Order', backref='product_ref', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    product = db.relationship('Product', foreign_keys=[product_id])

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='General')
    
    # Relationship with comments
    comments = db.relationship('ForumComment', backref='post', lazy=True)

class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
from datetime import datetime


# Add this context processor to make datetime functions available in templates
@app.context_processor
def utility_processor():
    import datetime
    return {
        'now': datetime.datetime.utcnow,
        'current_time': lambda fmt='%d %B, %Y': datetime.datetime.utcnow().strftime(fmt)
    }
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_weather_data(location):
    """
    Fetch real weather data from OpenWeatherMap API
    """
    if not WEATHER_API_KEY or WEATHER_API_KEY == 'your_openweather_api_key_here':
        # Return mock data if API key is not configured
        return get_mock_weather_data(location)
    
    try:
        params = {
            'q': location,
            'appid': WEATHER_API_KEY,
            'units': 'metric'  # Use metric units (Celsius)
        }
        
        response = requests.get(WEATHER_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant weather information
        weather_info = {
            'location': location,
            'temperature': round(data['main']['temp']),
            'condition': data['weather'][0]['main'],
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed'] * 3.6),  # Convert m/s to km/h
            'rainfall': data.get('rain', {}).get('1h', 0) if 'rain' in data else 0,
            'icon': get_weather_icon(data['weather'][0]['icon']),
            'description': data['weather'][0]['description'].title()
        }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {e}")
        return get_mock_weather_data(location)
    except (KeyError, IndexError) as e:
        print(f"Weather data parsing error: {e}")
        return get_mock_weather_data(location)

def get_mock_weather_data(location):
    """
    Return mock weather data when API is not available
    """
    # Simple hash of location to get consistent "random" data
    location_hash = hash(location) % 4
    
    conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain']
    temperatures = [28, 25, 22, 19]
    humidities = [65, 70, 75, 80]
    
    return {
        'location': location,
        'temperature': temperatures[location_hash],
        'condition': conditions[location_hash],
        'humidity': humidities[location_hash],
        'wind_speed': 12,
        'rainfall': 0 if location_hash != 3 else 2,
        'icon': 'sun' if location_hash == 0 else 'cloud-sun' if location_hash == 1 else 'cloud' if location_hash == 2 else 'cloud-rain',
        'description': conditions[location_hash],
        'is_mock': True  # Flag to indicate this is mock data
    }

def get_weather_icon(icon_code):
    """
    Map OpenWeatherMap icon codes to FontAwesome icons
    """
    icon_mapping = {
        '01d': 'sun',           # clear sky (day)
        '01n': 'moon',          # clear sky (night)
        '02d': 'cloud-sun',     # few clouds (day)
        '02n': 'cloud-moon',    # few clouds (night)
        '03d': 'cloud',         # scattered clouds
        '03n': 'cloud',
        '04d': 'cloud',         # broken clouds
        '04n': 'cloud',
        '09d': 'cloud-rain',    # shower rain
        '09n': 'cloud-rain',
        '10d': 'cloud-sun-rain',# rain (day)
        '10n': 'cloud-moon-rain',# rain (night)
        '11d': 'bolt',          # thunderstorm
        '11n': 'bolt',
        '13d': 'snowflake',     # snow
        '13n': 'snowflake',
        '50d': 'smog',          # mist
        '50n': 'smog'
    }
    return icon_mapping.get(icon_code, 'cloud')

def get_weather_forecast(location):
    """
    Generate a simple 3-day forecast based on current weather
    """
    current_weather = get_weather_data(location)
    
    # Simple forecast based on current conditions
    forecast = []
    conditions = [current_weather['condition']]
    temperatures = [current_weather['temperature']]
    
    # Vary conditions and temperatures for the forecast
    for i in range(1, 4):
        condition_idx = (hash(location + str(i)) % 4)
        temp_variation = [-2, 0, 2, -1][condition_idx]
        
        forecast_conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain']
        forecast.append({
            'day': f'In {i} day' + ('s' if i > 1 else ''),
            'condition': forecast_conditions[condition_idx],
            'high': current_weather['temperature'] + temp_variation + 2,
            'low': current_weather['temperature'] + temp_variation - 3,
            'icon': get_weather_icon(['01d', '02d', '03d', '09d'][condition_idx])
        })
    
    return forecast

def get_crop_calendar(crop_type, region):
    """
    Get planting and harvesting calendar for crops
    """
    calendar = {
        'rice': {
            'Kharif': {'sowing': 'June-July', 'harvesting': 'October-November'},
            'Rabi': {'sowing': 'November-December', 'harvesting': 'March-April'}
        },
        'wheat': {
            'Rabi': {'sowing': 'November-December', 'harvesting': 'March-April'}
        },
        'sugarcane': {
            'Whole Year': {'sowing': 'February-March', 'harvesting': 'December-March'}
        },
        'cotton': {
            'Kharif': {'sowing': 'June-July', 'harvesting': 'October-December'}
        },
        'maize': {
            'Kharif': {'sowing': 'June-July', 'harvesting': 'September-October'},
            'Rabi': {'sowing': 'October-November', 'harvesting': 'February-March'}
        }
    }
    
    return calendar.get(crop_type.lower(), {})

def get_market_prices(crop_name):
    """
    Get mock market prices for crops (in real app, this would come from an API)
    """
    prices = {
        'rice': {'min': 2500, 'max': 3200, 'unit': 'quintal'},
        'wheat': {'min': 2100, 'max': 2600, 'unit': 'quintal'},
        'sugarcane': {'min': 320, 'max': 380, 'unit': 'quintal'},
        'cotton': {'min': 6500, 'max': 7500, 'unit': 'quintal'},
        'maize': {'min': 1800, 'max': 2200, 'unit': 'quintal'},
        'tomato': {'min': 15, 'max': 40, 'unit': 'kg'},
        'potato': {'min': 12, 'max': 25, 'unit': 'kg'},
        'onion': {'min': 20, 'max': 45, 'unit': 'kg'}
    }
    
    return prices.get(crop_name.lower(), {'min': 0, 'max': 0, 'unit': 'kg'})

def get_soil_recommendations(soil_type, crops):
    """
    Get soil recommendations based on soil type and crops
    """
    recommendations = {
        'clay': ['Add organic matter', 'Improve drainage', 'Use raised beds'],
        'sandy': ['Add organic matter', 'Use mulch', 'Frequent irrigation'],
        'loamy': ['Maintain organic matter', 'Regular soil testing', 'Crop rotation'],
        'silt': ['Prevent compaction', 'Add organic matter', 'Proper drainage']
    }
    
    return recommendations.get(soil_type.lower(), ['Get soil tested regularly', 'Add organic matter'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recent orders
    recent_orders = Order.query.filter_by(
        user_id=current_user.id, 
        status='Ordered'
    ).order_by(Order.order_date.desc()).limit(3).all()
    
    # Get weather for user's location if available
    weather_data = None
    if current_user.farm_location:
        weather_data = get_weather_data(current_user.farm_location)
    
    # Get recent forum posts
    recent_posts = ForumPost.query.order_by(ForumPost.date_posted.desc()).limit(5).all()
    
    return render_template('dashboard.html', user=current_user, 
                          recent_orders=recent_orders, weather=weather_data,
                          recent_posts=recent_posts)

@app.route('/weather')
@login_required
def weather():
    location = request.args.get('location')
    
    # Use provided location, user's farm location, or default
    if not location and current_user.farm_location:
        location = current_user.farm_location
    elif not location:
        location = "New Delhi,IN"  # Default location
    
    # Get current weather
    weather_data = get_weather_data(location)
    
    # Get forecast
    forecast = get_weather_forecast(location)
    weather_data['forecast'] = forecast
    
    return render_template('weather.html', weather=weather_data, current_location=location)

@app.route('/subscribe_alerts', methods=['POST'])
@login_required
def subscribe_alerts():
    current_user.subscription = True
    db.session.commit()
    flash('You have successfully subscribed to weather alerts!', 'success')
    return redirect(url_for('weather'))

@app.route('/diseases')
@login_required
def diseases():
    alerts = [
        {
            'crop': 'Tomato',
            'disease': 'Late Blight',
            'risk': 'High',
            'description': 'Weather conditions are favorable for Late Blight development. Check plants regularly.',
            'prevention': 'Apply fungicides preventatively and ensure good air circulation.',
            'season': 'Rainy Season'
        },
        {
            'crop': 'Corn',
            'disease': 'Common Rust',
            'risk': 'Medium',
            'description': 'Rust spores have been detected in the region.',
            'prevention': 'Consider resistant varieties and fungicide application if disease is severe.',
            'season': 'Summer'
        },
        {
            'crop': 'Wheat',
            'disease': 'Powdery Mildew',
            'risk': 'Low',
            'description': 'Mild risk of powdery mildew due to moderate temperatures.',
            'prevention': 'Ensure proper spacing between plants for air circulation.',
            'season': 'Winter'
        }
    ]
    
    if current_user.crops:
        user_crops = [crop.strip().lower() for crop in current_user.crops.split(',')]
        filtered_alerts = [alert for alert in alerts if alert['crop'].lower() in user_crops]
        if filtered_alerts:
            alerts = filtered_alerts
    
    return render_template('diseases.html', alerts=alerts)

@app.route('/crop_calendar')
@login_required
def crop_calendar():
    crop_type = request.args.get('crop', '')
    calendar_data = {}
    
    if crop_type:
        calendar_data = get_crop_calendar(crop_type, current_user.farm_location or 'India')
    
    return render_template('crop_calendar.html', crop_type=crop_type, 
                          calendar_data=calendar_data, crops=INDIAN_CROPS)

@app.route('/market_prices')
@login_required
def market_prices():
    crop_name = request.args.get('crop', '')
    price_data = {}
    
    if crop_name:
        price_data = get_market_prices(crop_name)
    
    # Get all available crops for the dropdown
    available_crops = ['rice', 'wheat', 'sugarcane', 'cotton', 'maize', 'tomato', 'potato', 'onion']
    
    return render_template('market_prices.html', crop_name=crop_name, 
                          price_data=price_data, crops=available_crops)

@app.route('/government_schemes')
@login_required
def government_schemes():
    return render_template('government_schemes.html', schemes=GOVERNMENT_SCHEMES)

@app.route('/expert_advice')
@login_required
def expert_advice():
    return render_template('expert_advice.html')

@app.route("/soil-testing")
def soil_testing():
    recommendations = [
        "Use organic manure",
        "Improve irrigation",
        "Do regular pH testing"
    ]
    return render_template(
        "soil_testing.html",
        user=current_user,   # if you use Flask-Login
        recommendations=recommendations,
        now=datetime.now()   # pass current datetime
    )

@app.route('/loan_calculator', methods=['GET', 'POST'])
@login_required
def loan_calculator():
    # Default values
    loan_amount = 100000
    interest_rate = 7.5
    loan_tenure = 5
    emi = 0
    total_interest = 0
    total_amount = 0
    
    if request.method == 'POST':
        try:
            loan_amount = float(request.form.get('loan_amount', 100000))
            interest_rate = float(request.form.get('interest_rate', 7.5))
            loan_tenure = int(request.form.get('loan_tenure', 5))
            
            # EMI calculation formula: P × r × (1 + r)^n / ((1 + r)^n - 1)
            monthly_rate = interest_rate / 12 / 100
            tenure_months = loan_tenure * 12
            
            emi = (loan_amount * monthly_rate * (1 + monthly_rate)**tenure_months) / ((1 + monthly_rate)**tenure_months - 1)
            total_amount = emi * tenure_months
            total_interest = total_amount - loan_amount
            
        except (ValueError, ZeroDivisionError):
            flash('Please enter valid numbers for loan calculation', 'danger')
    
    return render_template('loan_calculator.html', 
                         loan_amount=loan_amount,
                         interest_rate=interest_rate,
                         loan_tenure=loan_tenure,
                         emi=emi,
                         total_interest=total_interest,
                         total_amount=total_amount)

@app.route('/forum')
@login_required
def forum():
    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if category == 'all':
        posts = ForumPost.query.order_by(ForumPost.date_posted.desc()).paginate(page=page, per_page=per_page)
    else:
        posts = ForumPost.query.filter_by(category=category).order_by(ForumPost.date_posted.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('forum.html', posts=posts, category=category)

@app.route('/forum/post/<int:post_id>')
@login_required
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('forum_post.html', post=post)

@app.route('/forum/create', methods=['GET', 'POST'])
@login_required
def create_forum_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', 'General')
        
        if not title or not content:
            flash('Title and content are required!', 'danger')
            return redirect(url_for('create_forum_post'))
        
        post = ForumPost(title=title, content=content, category=category, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been created!', 'success')
        return redirect(url_for('forum_post', post_id=post.id))
    
    return render_template('create_forum_post.html')

@app.route('/forum/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = ForumPost.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty!', 'danger')
        return redirect(url_for('forum_post', post_id=post_id))
    
    comment = ForumComment(content=content, user_id=current_user.id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    
    flash('Your comment has been added!', 'success')
    return redirect(url_for('forum_post', post_id=post_id))

@app.route('/shop')
@login_required
def shop():
    category = request.args.get('category', 'all')
    
    if category == 'all':
        products = Product.query.filter_by(in_stock=True).all()
    else:
        products = Product.query.filter_by(category=category, in_stock=True).all()
    
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('shop.html', products=products, categories=categories, current_category=category)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if not product.in_stock:
        flash('This product is out of stock!', 'danger')
        return redirect(url_for('shop'))
    
    # Check if product is already in user's cart
    existing_order = Order.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id, 
        status='Cart'
    ).first()
    
    if existing_order:
        existing_order.quantity += 1
        flash(f'Added another {product.name} to cart!', 'success')
    else:
        new_order = Order(
            user_id=current_user.id,
            product_id=product_id,
            quantity=1,
            status='Cart'
        )
        db.session.add(new_order)
        flash(f'{product.name} added to cart!', 'success')
    
    db.session.commit()
    return redirect(url_for('shop'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Order.query.filter_by(user_id=current_user.id, status='Cart').all()
    total = sum(item.product.price * item.quantity for item in cart_items) if cart_items else 0
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:order_id>/<action>')
@login_required
def update_cart(order_id, action):
    order = Order.query.get_or_404(order_id)
    
    # Verify the order belongs to the current user
    if order.user_id != current_user.id or order.status != 'Cart':
        flash('You cannot modify this cart item.', 'danger')
        return redirect(url_for('cart'))
    
    if action == 'increase':
        order.quantity += 1
        db.session.commit()
        flash('Cart updated!', 'success')
    elif action == 'decrease':
        if order.quantity > 1:
            order.quantity -= 1
            db.session.commit()
            flash('Cart updated!', 'success')
        else:
            db.session.delete(order)
            db.session.commit()
            flash('Item removed from cart.', 'info')
    elif action == 'remove':
        db.session.delete(order)
        db.session.commit()
        flash('Item removed from cart.', 'info')
    
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = Order.query.filter_by(user_id=current_user.id, status='Cart').all()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))
    
    for item in cart_items:
        item.status = 'Ordered'
        item.order_date = datetime.utcnow()
    
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter(
        Order.user_id == current_user.id, 
        Order.status != 'Cart'
    ).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.farm_location = request.form.get('farm_location')
        current_user.farm_size = request.form.get('farm_size')
        current_user.crops = request.form.get('crops')
        current_user.phone = request.form.get('phone')
        current_user.soil_type = request.form.get('soil_type')
        current_user.language = request.form.get('language', 'en')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=current_user)

@app.route('/api/weather/<location>')
def api_weather(location):
    weather_data = get_weather_data(location)
    return jsonify(weather_data)

def create_tables():
    with app.app_context():
        db.create_all()
        
        if not Product.query.first():
            # Prices in Indian Rupees (₹)
            sample_products = [
                Product(
                    name='NPK Fertilizer 10-10-10',
                    description='Balanced fertilizer for general use on most crops. Provides equal parts nitrogen, phosphorus, and potassium for healthy plant growth.',
                    price=499,
                    image='fertilizer1.jpg',
                    category='General Purpose',
                    in_stock=True
                ),
                Product(
                    name='Organic Compost',
                    description='100% organic compost for improving soil health. Rich in nutrients and beneficial microorganisms. Improves soil structure and water retention.',
                    price=349,
                    image='fertilizer2.jpg',
                    category='Organic',
                    in_stock=True
                ),
                Product(
                    name='Tomato Special Formula',
                    description='Specially formulated for tomatoes with extra calcium to prevent blossom end rot. Promotes healthy fruit development and higher yields.',
                    price=599,
                    image='fertilizer3.jpg',
                    category='Vegetable',
                    in_stock=True
                ),
                Product(
                    name='Potato Fertilizer',
                    description='High-potassium fertilizer for potatoes and root vegetables. Encourages strong root development and improves crop size and quality.',
                    price=549,
                    image='fertilizer4.jpg',
                    category='Vegetable',
                    in_stock=True
                ),
                Product(
                    name='Liquid Seaweed Extract',
                    description='Organic liquid fertilizer from seaweed. Rich in micronutrients and growth hormones. Improves plant resilience and stress tolerance.',
                    price=440,
                    image='fertilizer5.jpg',
                    category='Organic',
                    in_stock=True
                ),
                Product(
                    name='Slow-Release Granules',
                    description='Coated fertilizer granules that release nutrients gradually over 3 months. Reduces fertilizer burn and minimizes application frequency.',
                    price=600,
                    image='fertilizer6.jpg',
                    category='General Purpose',
                    in_stock=True
                ),
                    Product(
                    name='Urea (46% Nitrogen)',
                    description='High-nitrogen fertilizer essential for paddy crops. Promotes vigorous vegetative growth and enhances tillering in rice plants.',
                    price=270,
                    image='urea.jpg',
                    category='Nitrogen Fertilizer',
                    in_stock=True
                ),
                Product(
                name='Sulphur Fertilizer (90% WDG)',
                description='Provides sulphur to improve protein synthesis and enhance grain quality in rice. Corrects sulphur deficiency and supports higher yields.',
                price=700,
                image='sulphur.jpg',
                category='Secondary Nutrient',
                in_stock=True
                ),
                Product(
                name='Humic Acid 98%',
                description='Concentrated organic soil conditioner that improves nutrient uptake, enhances root development, and boosts soil microbial activity for paddy fields.',
                price=700,
                image='humic.jpg',
                category='Soil Conditioner',
                in_stock=True
            ),
                Product(
                name='Zinc Sulphate (21% Zn)',
                description='Essential micronutrient fertilizer for paddy crops. Prevents zinc deficiency (Khaira disease) and improves grain filling and plant vigor.',
                price=450,
                image='zinc.jpg',
                category='Micronutrient',
                in_stock=True
            ),
                Product(
                name='Paraquat Herbicide',
                description='Fast-acting non-selective herbicide for weed control in paddy fields. Effective against a wide range of grasses and broadleaf weeds.',
                price=550,
                image='paraquat.jpg',
                category='Herbicide',
                in_stock=True
            ),
           Product(
        name='DAP (Diammonium Phosphate)',
        description='Popular fertilizer providing both nitrogen and phosphorus. Encourages strong root growth and early plant establishment in paddy.',
        price=1350,
        image='dap.jpg',
        category='Phosphorus Fertilizer',
        in_stock=True
    ),
          Product(
        name='MOP (Muriate of Potash)',
        description='Potassium-rich fertilizer that strengthens plant stems, improves grain filling, and enhances resistance against pests and diseases in rice.',
        price=1400,
        image='mop.jpg',
        category='Potassium Fertilizer',
        in_stock=True
    )
            ]
            for product in sample_products:
                db.session.add(product)
            db.session.commit()
            print("Sample products added to database with Indian Rupee prices.")

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

