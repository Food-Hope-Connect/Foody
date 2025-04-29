import requests
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource

# Initialize the Flask app and API
app = Flask(__name__)
api = Api(app)

# Set up the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_donation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# OpenRouter API key
OPENROUTER_API_KEY = "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"  # <-- update this

# Create a model for donations
class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    pickup_time = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

# Route for Home Page (Web Interface)
@app.route('/')
def index():
    donations = Donation.query.all()
    return render_template('index.html', donations=donations)

# API: Get all donations
class DonationListResource(Resource):
    def get(self):
        donations = Donation.query.all()
        result = []
        for donation in donations:
            donation_data = {
                'id': donation.id,
                'food_type': donation.food_type,
                'quantity': donation.quantity,
                'pickup_time': donation.pickup_time,
                'location': donation.location
            }
            result.append(donation_data)
        return jsonify(result)

    def post(self):
        data = request.get_json()
        new_donation = Donation(
            food_type=data['food_type'],
            quantity=data['quantity'],
            pickup_time=data['pickup_time'],
            location=data['location']
        )
        db.session.add(new_donation)
        db.session.commit()
        return jsonify({'message': 'Donation added successfully!'}), 201

# API: Get a single donation by ID
class DonationResource(Resource):
    def get(self, donation_id):
        donation = Donation.query.get(donation_id)
        if not donation:
            return {'message': 'Donation not found'}, 404
        donation_data = {
            'id': donation.id,
            'food_type': donation.food_type,
            'quantity': donation.quantity,
            'pickup_time': donation.pickup_time,
            'location': donation.location
        }
        return jsonify(donation_data)

# Add API resources to the app
api.add_resource(DonationListResource, '/api/donations')
api.add_resource(DonationResource, '/api/donations/<int:donation_id>')

# Function to call OpenRouter API for Chatbot
def ask_openrouter(query):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "mistralai/mistral-7b-instruct",  # you can change the model if you want
            "messages": [
                {"role": "user", "content": query}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

# Route for Chatbot
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_message = request.form['message']
        bot_response = ask_openrouter(user_message)  # use OpenRouter now
        return render_template('chat.html', user_message=user_message, bot_response=bot_response)
    return render_template('chat.html', user_message=None, bot_response=None)

# Route for Donation Form
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        food_type = request.form['food_type']
        quantity = request.form['quantity']
        pickup_time = request.form['pickup_time']
        location = request.form['location']

        new_donation = Donation(
            food_type=food_type,
            quantity=quantity,
            pickup_time=pickup_time,
            location=location
        )
        db.session.add(new_donation)
        db.session.commit()
        return render_template('donate_success.html')

    return render_template('donate.html')

if __name__ == '__main__':
    app.run(debug=True)


