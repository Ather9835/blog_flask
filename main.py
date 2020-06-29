from flask import Flask, request, session, redirect
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import os
import json
from math import ceil

with open("config.json", "r") as f:
    params = json.load(f)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]

)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    slug = db.Column(db.String(40), nullable=False)
    img = db.Column(db.String(100), nullable=False)
    tag_line = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def home2():
    posts = Posts.query.filter_by().all()
    last = ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page=1
    page = int(page)

    posts = posts[(page-1)*params['no_of_posts']:(page*params['no_of_posts'])]

    if page == 1:
        prev = "#"
        ext = '/?page=' + str(page+1)
    elif page == last:
        prev = '/?page=' + str(page-1)
        ext = "#"
    else:
        prev = '/?page=' + str(page - 1)
        ext = '/?page=' + str(page+1)

    return render_template("index.html", params=params, posts=posts, prev=prev, ext=ext)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/login", methods=["GET", "POST"])
def login():
    print(session)
    if ('user' in session) and (session['user'] == params['admin_user']):
        posts = Posts.query.filter_by().all()
        return render_template("dashboard.html",params=params, posts=posts)
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username == params['admin_user'] and password == params['admin_password']:
            session['user'] = username
            posts = Posts.query.filter_by().all()
            return render_template("dashboard.html",params=params, posts=posts)
        else:
            return render_template("login.html",params=params)
    else:
        return render_template("login.html",params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, email=email, phone=phone, msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from Blog',
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone)

    return render_template("contact.html", params=params)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if ('user' in session) and (session['user'] == params['admin_user']):
        if request.method == "POST":
            req_title = request.form.get('title')
            req_img = request.form.get('img')
            req_tagline = request.form.get('tagline')
            req_content = request.form.get('content')
            req_slug = request.form.get('slug')
            req_date = datetime.now()
            if sno == '0':
                post = Posts(title=req_title,tag_line=req_tagline, slug=req_slug, content=req_content, date=req_date, img=req_img)
                db.session.add(post)
                db.session.commit()
                return redirect('/login')
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = req_title
                post.slug = req_slug
                post.tag_line = req_tagline
                post.date = req_date
                post.img= req_img
                post.content= req_content
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post, sno=sno)


@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if ('user' in session) and (session['user'] == params['admin_user']):
        if request.method == "POST":
            f = request.files['file1']
            print(f)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
            return "Uploaded Successfully"


@app.route("/delete/<string:sno>", methods= ["GET"])
def delete(sno):
    if ('user' in session) and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/login")


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/")






app.run(debug=True)
