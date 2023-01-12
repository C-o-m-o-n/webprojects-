#import all the necessary packages
from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os
from sqlalchemy import MetaData
from flask_migrate import Migrate

#initialise Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
app.config['SECRET_KEY']='sqlite:///database'

#for user session
app.permanent_session_lifetime = timedelta(minutes=10)

#initialise SQLAlchemy with Flask


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app,db,render_as_batch=True)



login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

#define the BlogPost table
class BlogPost(db.Model,UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  date_posted = db.Column(db.DateTime)
  content = db.Column(db.String())
  post_img = db.Column(db.String())
  #foreign key to link to users
  poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  likes = db.relationship('Likes', backref='post')

#define the Users table
class Users(db.Model,UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50))
  email = db.Column(db.String(50))
  password = db.Column(db.String(50))
  profile_pic = db.Column(db.String(50), default='user.png')
  pic_file_path = db.Column(db.String(100))
  # date_posted = db.Column(db.DateTime)
  #user can have many ppsts
  blog_post = db.relationship('BlogPost', backref='poster')
  likes = db.relationship('Likes', backref='liker')
  
#define the Likes table
class Likes(db.Model,UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.Integer, db.ForeignKey('users.id'))#represents the user
  date_posted = db.Column(db.DateTime)
  #user can have many ppsts
  post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))


#main app code starts here****************((*))
  
with app.app_context(): 
  #put all the code inside the app context
  #the homepage
  @app.route('/')
  def index():
    posts = BlogPost.query.all()
    return render_template("index.html", posts=posts, current_user=current_user )
    
  #like
  @app.route('/like/<int:post_id>', methods=['GET'])
  @login_required
  def like(post_id):
    post = BlogPost.query.filter_by(id=post_id).one()
    
    like = Likes.query.filter_by(username=current_user.id, post_id=post_id).first()
    if not post:
      flash('the post does not exist', 'error')
    elif like:
      db.create_all()
      db.session.delete(like)
      db.session.commit()
    else:
      like= Likes(username=current_user.id, post_id=post_id)
      db.create_all()
      db.session.add(like)
      db.session.commit()
    return redirect(url_for('index'))
  #the post page
  @app.route('/post/<int:post_id>')
  def post(post_id):
    post = BlogPost.query.filter_by(id=post_id).one()
    date_posted = post.date_posted.strftime('%B, %d, %Y')
    return render_template("post.html", post=post, date_posted=date_posted)
  #the page for adding posts 8 the frontend  
  @app.route('/add')
  @login_required
  def add():
    return render_template("add.html")
    
  #handles the posts
  def save_post_img(form_pic): 
    random_pic_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_pic.filename)
    post_pic_file_name = random_pic_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/assets/post_img', post_pic_file_name)
    form_pic.save(picture_path)
    
    return post_pic_file_name
    
  @app.route('/addpost', methods=['POST'])
  def addpost():
    content_img = request.files['post_img']
    content = request.form['content']
    poster = current_user.id
    if content_img:
      post_img = save_post_img(request.files['post_img'])
      post = BlogPost(post_img=post_img, poster_id=poster, content=content, date_posted=datetime.now())
    elif content_img and content:
      post = BlogPost(post_img=post_img, poster_id=poster, content=content, date_posted=datetime.now())
    elif not content_img:
      post = BlogPost(poster_id=poster, content=content, date_posted=datetime.now())
    db.create_all()
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('index'))
  #posts code ends*************((*))
  
  #user accounts starts************((*))
  @login_manager.user_loader
  def load_user(id):
    return Users.query.get(int(id))

  @app.route('/login', methods=['POST', 'GET'])
  def login():
    if current_user.is_authenticated:
      flash("you are already loged in", 'error')
      return redirect(url_for('index'))
    if request.method == 'POST':
      session.permanent = True
      email = request.form['email']
      password = request.form['password']
      username = request.form['username']
      user = Users.query.filter_by(email=email).first()
      if user:
        password_is_same =check_password_hash(user.password, password)
        if password_is_same:
          flash("loged in successfully", 'success')
          session["user"]=username
          login_user(user, remember=True)
          next_page = request.args.get('next')
          return redirect(url_for(next_page)) if next_page else redirect(url_for('index'))
        else:
          flash("The username or password is incorrect", 'error')
      else:
        flash("email does not exist", "error")
    return render_template('login.html')
    
  #save the image to the file system
  def save_pic(form_pic): 
    random_pic_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_pic.filename)
    pic_file_name = random_pic_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/assets/profile_img', pic_file_name)
    form_pic.save(picture_path)
    
    return pic_file_name
    
  #user profile
  @app.route('/user', methods=['POST', 'GET'])
  @login_required
  def user():
    profile_pic = url_for('static', filename='assets/profile_img/'+ current_user.profile_pic)
    #updating the profile details
    if request.method == "POST":
      if request.files['profile_pic']:
        picture_file = save_pic(request.files['profile_pic'])
        current_user.profile_pic = picture_file
        
      
      #get username and email from the form
      username = request.form['username']
      email = request.form['email']
      #check if username and email exists 
      email_exists = Users.query.filter_by(email=email).first()
      username_exists = Users.query.filter_by(username=username).first()  
      if not username and not email:
        flash('username and email cannot be empty!', 'error')
      elif email_exists and username_exists:
        flash('username and email already exist', 'error')
      else:
        current_user.username = username
        current_user.email = email
        db.session.commit()
        flash("your profile has been updated successfully", "success")
        return redirect(url_for('user'))
        
    if 'user' in session:
      user_session = session["user"]
      user = Users.query.filter_by(username=current_user.username).first()
      return render_template("user.html",title="profile", user_session=user_session, current_user=current_user, profile_pic=profile_pic)
    else:
      return redirect(url_for('login'))
      
  @app.route('/signup', methods=['POST', 'GET'])
  def signup():
    if current_user.is_authenticated:
      flash("you are already signed up", 'error')
      return redirect(url_for('index'))
    if request.method == 'POST':
      username = request.form['username']
      email = request.form['email']
      password1 = request.form['password1']
      password2 = request.form['password2']
      
      email_exists = Users.query.filter_by(email=email).first()
      username_exists = Users.query.filter_by(username=username).first()
      if email_exists:
        flash('email i already in use', 'error')
      elif username_exists:
        flash('username i already in use', 'error')
      elif password1 != password2:
          flash('passwords do not match', 'error')
      elif len(username) <= 2:
        flash('username is too short', 'error')
      elif len(password1) <= 6:
        flash('password is too short', 'error')
      elif len(email) <= 4:
        flash('email is invalid', 'error')
      else:
        new_user = Users(username=username, email=email, password=generate_password_hash(password1, method='sha256'))
        db.create_all()
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        flash('user created successfully','success')
        return redirect(url_for('index'))
    return render_template('signup.html')
    #logout
  @app.route('/logout')
  @login_required
  def logout():
    logout_user()
    session.pop("user", None)
    return redirect(url_for('index'))
  
  #run the Flask app
  if __name__ == "__main__":
    app.run(debug=True)
