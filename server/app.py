#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in Restaurant.query.all()]
    return make_response(jsonify(restaurants), 200)

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant_by_id(id):
    restaurant = Restaurant.query.filter_by(id=id).first()
    if restaurant is None:
        return make_response(jsonify({"error": "Restaurant not found"}), 404)
    
    response_dict = restaurant.to_dict()
    response_dict['restaurant_pizzas'] = [
        {
            'id': rp.id,
            'price': rp.price,
            'pizza_id': rp.pizza_id,
            'restaurant_id': rp.restaurant_id,
            'pizza': rp.pizza.to_dict(only=('id', 'name', 'ingredients'))
        }
        for rp in restaurant.pizzas
    ]
    return make_response(jsonify(response_dict), 200)

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.filter_by(id=id).first()
    if restaurant is None:
        return make_response(jsonify({"error": "Restaurant not found"}), 404)

    db.session.delete(restaurant)
    db.session.commit()
    return make_response({}, 204)

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in Pizza.query.all()]
    return make_response(jsonify(pizzas), 200)

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    try:
        price = int(data.get('price'))
        if price < 1 or price > 30:
            raise ValueError("validation errors")
        
        restaurant_pizza = RestaurantPizza(
            pizza_id=data.get('pizza_id'),
            restaurant_id=data.get('restaurant_id'),
            price=price,
        )
        db.session.add(restaurant_pizza)
        db.session.commit()

        response_dict = restaurant_pizza.to_dict()
        response_dict['pizza'] = restaurant_pizza.pizza.to_dict(only=('id', 'name', 'ingredients'))
        response_dict['restaurant'] = restaurant_pizza.restaurant.to_dict(only=('id', 'name', 'address'))
        return make_response(jsonify(response_dict), 201)
    except ValueError as ve:
        return make_response(jsonify({"errors": [str(ve)]}), 400)
    except Exception as e:
        return make_response(jsonify({"errors": ["validation errors"]}), 400)

if __name__ == "__main__":
    app.run(port=5555, debug=True)