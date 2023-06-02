
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
import os

CACHE_TYPE = os.environ['CACHE_TYPE']
CACHE_REDIS_HOST = os.environ['CACHE_REDIS_HOST']
CACHE_REDIS_PORT = os.environ['CACHE_REDIS_PORT']
CACHE_REDIS_DB = os.environ['CACHE_REDIS_DB']
CACHE_REDIS_URL = os.environ['CACHE_REDIS_URL']
CACHE_DEFAULT_TIMEOUT = os.environ['CACHE_DEFAULT_TIMEOUT']

config ={
    "CACHE_TYPE":CACHE_TYPE,
    "CACHE_REDIS_HOST":CACHE_REDIS_HOST,
    "CACHE_REDIS_PORT":CACHE_REDIS_PORT,
    "CACHE_REDIS_DB":CACHE_REDIS_DB,
    "CACHE_REDIS_URL":CACHE_REDIS_URL,
    "CACHE_DEFAULT_TIMEOUT":CACHE_DEFAULT_TIMEOUT
    
    
}
app = Flask(__name__)
# app.config.from_object('config.Config')  # Set the configuration variables to the flask application
app.config.from_mapping(config)
cache = Cache(app) # Initialize Cache


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://<username>:<pass>@<rds endpoint>/mypostgres'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
@app.route('/')
def hello():
    return 'Hello, world!'



@app.route('/users', methods=['GET'])
def get_users():
    cache_key = f'result_{request.args.get("username")}_{request.args.get("id")}'
    users = cache.get(cache_key)
    if users is None:
        # No cache found so querying db server for data
        users = User.query.all()
        # Cache the result for a specific duration
        cache.set(cache_key, users, timeout=10)  # Cache for 60 seconds
        print("not cached")
        user_list = [{'id': user.id, 'username': user.username} for user in users]
        return jsonify({'users': user_list,"status":"Not Cached"})
    else:
        print("yes")
        user_list = [{'id': user.id, 'username': user.username} for user in users]
        return jsonify({'users': user_list,"status":"cached"})

@app.route('/users', methods=['POST'])
def create_user():
    username = request.json['username']
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'})

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    else:
        return jsonify({'message': 'User not found'}), 404

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=3000,debug=True)