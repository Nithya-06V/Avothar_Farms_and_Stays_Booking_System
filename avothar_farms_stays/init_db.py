import json
from datetime import datetime

from flask import Flask
from werkzeug.security import generate_password_hash

from models import Admin, Booking, Payment, Property, Review, User, db


SEED_PROPERTIES = [
    {
        "property_type": "Villa",
        "name": "Premium Villa",
        "location": "Bengaluru, Karnataka",
        "price_per_night": 8000,
        "bedrooms": 4,
        "guests": 8,
        "facilities": "Infinity Pool, Wi-Fi, Air Conditioning, Housekeeping, Parking",
        "description": "A premium luxury villa designed for a grand countryside getaway with a private pool, landscaped gardens, and scenic mountain views.",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "Villa",
        "name": "Swimming Pool Villa",
        "location": "Coorg, Karnataka",
        "price_per_night": 10000,
        "bedrooms": 3,
        "guests": 6,
        "facilities": "Swimming Pool, Terrace, Wi-Fi, Balcony, BBQ Area",
        "description": "A charming villa with a private pool and expansive terraces, perfect for family gatherings and relaxed vacations.",
        "image_url": "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "Villa",
        "name": "Luxury Garden Villa",
        "location": "Mysuru, Karnataka",
        "price_per_night": 12000,
        "bedrooms": 5,
        "guests": 10,
        "facilities": "Garden, Jacuzzi, Smart TV, Air Conditioning, Concierge",
        "description": "Opulent villa set amidst lush greenery with a premium interior, dedicated staff, and panoramic views of the countryside.",
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "Farmhouse",
        "name": "Green Valley Farmhouse",
        "location": "Wayanad, Kerala",
        "price_per_night": 5000,
        "bedrooms": 3,
        "guests": 6,
        "facilities": "Open Lawn, Organic Farm, Bonfire, Wi-Fi, Parking",
        "description": "A serene farmhouse surrounded by paddy fields and plantations, ideal for a relaxing family retreat in nature.",
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "Farmhouse",
        "name": "Avothar Nature Farm",
        "location": "Chikmagalur, Karnataka",
        "price_per_night": 6500,
        "bedrooms": 4,
        "guests": 7,
        "facilities": "Nature Trail, Campfire, Wi-Fi, Dining Area, Parking",
        "description": "A beautiful nature farmhouse featuring coffee plantation views, relaxing courtyards, and a warm rural ambiance.",
        "image_url": "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "Farmhouse",
        "name": "Royal Farm Stay",
        "location": "Ooty, Tamil Nadu",
        "price_per_night": 7500,
        "bedrooms": 4,
        "guests": 8,
        "facilities": "Private Deck, Wi-Fi, Breakfast Included, Firepit, Parking",
        "description": "Combines royal comfort with the peaceful charm of hill-country farm living for memorable holidays.",
        "image_url": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": True,
        "is_available": True,
    },
    {
        "property_type": "House",
        "name": "Premium Family House",
        "location": "Pune, Maharashtra",
        "price_per_night": 3500,
        "bedrooms": 3,
        "guests": 5,
        "facilities": "Parking, Kitchen, Wi-Fi, Laundry, AC",
        "description": "A stylish family house with ample indoor space and bright balconies, ideal for road trip getaways.",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
    {
        "property_type": "House",
        "name": "Modern Holiday House",
        "location": "Goa",
        "price_per_night": 4500,
        "bedrooms": 3,
        "guests": 6,
        "facilities": "Sea View, Wi-Fi, Balcony, Fully Equipped Kitchen",
        "description": "Modern holiday home with clean design, lush interiors, and close access to beaches and local attractions.",
        "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
    {
        "property_type": "House",
        "name": "Garden View House",
        "location": "Nashik, Maharashtra",
        "price_per_night": 5000,
        "bedrooms": 4,
        "guests": 7,
        "facilities": "Garden, Wi-Fi, Air Conditioning, Rooftop Seating, Parking",
        "description": "A relaxing home with a beautiful courtyard garden and comfortable rooms for quality family time.",
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
    {
        "property_type": "Cottage",
        "name": "Wooden Cottage",
        "location": "Kodaikanal, Tamil Nadu",
        "price_per_night": 2500,
        "bedrooms": 2,
        "guests": 4,
        "facilities": "Wooden Finish, Balcony, Fireplace, Wi-Fi",
        "description": "A cozy cottage with warm natural textures and a mountain-view balcony for quiet, restorative breaks.",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
    {
        "property_type": "Cottage",
        "name": "Nature View Cottage",
        "location": "Munnar, Kerala",
        "price_per_night": 3000,
        "bedrooms": 2,
        "guests": 4,
        "facilities": "Garden, Sunrise View, Wi-Fi, Breakfast, Parking",
        "description": "A scenic cottage tucked in the hills with calming views, ideal for romantic and nature-focused stays.",
        "image_url": "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
    {
        "property_type": "Cottage",
        "name": "Premium Cottage",
        "location": "Kullu, Himachal Pradesh",
        "price_per_night": 4000,
        "bedrooms": 2,
        "guests": 5,
        "facilities": "Private Deck, Wi-Fi, Hot Water, Fireplace, Parking",
        "description": "A premium cottage with modern amenities and a private deck that embraces the peaceful mountain landscape.",
        "image_url": "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80"
        ],
        "featured": False,
        "is_available": True,
    },
]


def seed_reviews():
    reviews = [
        {
            "customer_name": "Aarav S.",
            "review_text": "The stay was incredibly smooth, beautiful, and the property matched the pictures perfectly.",
            "rating": 5,
            "property_name": "Premium Villa",
        },
        {
            "customer_name": "Meera N.",
            "review_text": "Loved the warm hospitality and the peaceful atmosphere. The farmhouse was a perfect family retreat.",
            "rating": 5,
            "property_name": "Avothar Nature Farm",
        },
        {
            "customer_name": "Karthik R.",
            "review_text": "Professional service, gorgeous location, and a really comfortable experience throughout the stay.",
            "rating": 5,
            "property_name": "Royal Farm Stay",
        },
    ]
    for review_data in reviews:
        existing = Review.query.filter_by(customer_name=review_data["customer_name"]).first()
        if not existing:
            review = Review(**review_data)
            db.session.add(review)
    db.session.commit()


def init_database(app=None):
    if app is not None:
        with app.app_context():
            db.create_all()
            _seed_data()
    else:
        db.create_all()
        _seed_data()


def _seed_data():
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin", password_hash=generate_password_hash("admin123"))
        db.session.add(admin)

    if Property.query.count() == 0:
        for data in SEED_PROPERTIES:
            property_data = dict(data)
            property_data["gallery_images"] = json.dumps(property_data.get("gallery_images", []))
            property_obj = Property(**property_data)
            db.session.add(property_obj)

    if Review.query.count() == 0:
        seed_reviews()

    db.session.commit()
