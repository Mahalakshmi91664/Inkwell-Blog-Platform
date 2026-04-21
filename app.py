from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    posts = db.relationship('Post', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {'id': self.id, 'username': self.username}


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.user.username,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%B %d, %Y · %I:%M %p'),
            'comment_count': len(self.comments)
        }


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'username': self.user.username,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'created_at': self.created_at.strftime('%B %d, %Y · %I:%M %p')
        }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return jsonify({'message': 'Backend running'})


# Auth
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Account created successfully', 'user': user.to_dict()}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200


# Posts
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts])


@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    user_id = data.get('user_id')

    if not title or not content or not user_id:
        return jsonify({'error': 'Title, content, and user_id are required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    post = Post(title=title, content=content, user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()
    user_id = data.get('user_id')
    post = Post.query.get_or_404(post_id)

    if post.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    post.title = title
    post.content = content
    db.session.commit()
    return jsonify(post.to_dict())


@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.get_json()
    user_id = data.get('user_id')
    post = Post.query.get_or_404(post_id)

    if post.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted'})


# Comments
@app.route('/comments/<int:post_id>', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments])


@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    text = data.get('text', '').strip()
    user_id = data.get('user_id')
    post_id = data.get('post_id')

    if not text or not user_id or not post_id:
        return jsonify({'error': 'Text, user_id, and post_id are required'}), 400

    user = User.query.get(user_id)
    post = Post.query.get(post_id)
    if not user or not post:
        return jsonify({'error': 'User or post not found'}), 404

    comment = Comment(text=text, user_id=user_id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    data = request.get_json()
    user_id = data.get('user_id')
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted'})


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✓ Database ready")
    print("✓ Blog Platform API running on http://localhost:5000")
    app.run(debug=True, port=5000)
