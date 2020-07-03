import os
import logging
import requests
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "gG4ZTsypMOQFHap8SpLrg", "isbns": "9781632168146"})

username = ""
@app.route("/", methods = ["POST", "GET"])
def index():
    if session.get("username") is None:
        session['username'] = request.form.get("logname")
        session['pass'] = str(request.form.get("pass"))
        typedpass = db.execute("SELECT password FROM users WHERE username = :username", {"username": session['username']}).fetchone()
        if request.method == "GET":
            return render_template("index.html", message="")
        else:
            if typedpass[0] == session['pass']:
                return render_template("loggedin.html", username=session['username'])
            else:
                return render_template("error.html", message="Login")
    else:
        return render_template("loggedin.html", username=session['username'])

@app.route("/logout", methods = ["GET"])
def logout():
    session.pop('username', None)
    return render_template("index.html", message="Logged Out")

@app.route("/loggedin", methods = ["GET", "POST"])
def loggedin():
    if request.method == "GET":
        return render_template("loggedin.html")

@app.route("/searchresult", methods = ["GET", "POST"])
def searchresult():
    if request.method == "GET":
        return render_template("searchresult.html")
    else:
        year = request.form.get("searchbook")
        if year[1].isalpha():
            searchterm = (request.form.get("searchbook").title() + "%")
            result = db.execute("SELECT * FROM books where isbn LIKE :searched or author LIKE :searched or title LIKE :searched",
             {"searched": searchterm}).fetchall()
        else:
            number = int(year)
            result = db.execute("SELECT * FROM books WHERE year = :searched", {"searched": number}).fetchall()

        return render_template("searchresult.html", result=result)

@app.route("/register", methods = ["POST", "GET"])
def register():
    newuser = request.form.get("newuser")
    password = str(request.form.get("regpass"))
    confirmpass = str(request.form.get("confirmpass"))
    if request.method == "POST":
        if db.execute("SELECT username FROM users WHERE username = :username", {"username": newuser}).rowcount == 0 and confirmpass == password:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",{"username":newuser, "password":password})
            db.commit()
            return render_template("success.html", message="Successfully Registered")
        else:
            return render_template("error.html", message="User already exists or something")

    return render_template("register.html")

@app.route("/searchresult/<int:book_id>", methods = ["POST", "GET"])
def bookinfo(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :bookid", {"bookid": book_id}).fetchone()
    sum = db.execute("SELECT sum(rating) FROM ratings WHERE bookid = :bookid", {"bookid":book_id}).fetchone()
    all_rating = db.execute("SELECT sum(rating) FROM ratings WHERE bookid = :bookid", {"bookid":book_id}).fetchone()
    userid = db.execute("SELECT id FROM users WHERE username = :username", {"username":session['username']}).fetchone()
    #userid = db.execute("SELECT * FROM users WHERE ")
    if db.execute("SELECT count(*) FROM ratings WHERE bookid = :bookid", {"bookid":book_id}).rowcount == 0:
        count = 0
    else:
        count = db.execute("SELECT count(*) FROM ratings WHERE bookid = :bookid", {"bookid":book_id}).fetchone()
    if sum[0] == 0:
        avg_rating = 0
        all_rating = 0
    elif count[0] != 0:
        avg_rating = all_rating[0]/count[0]
    elif count[0] == 0:
        avg_rating = all_rating[0]
    review = db.execute("SELECT review FROM reviews WHERE bookid = :bookid",{"bookid":book_id}).fetchall()
    if request.method == "GET":
        if book == 0:
            return render_template("error.html", message="no book")
        else:
            rendered = 1
            return render_template("bookinfo.html", book = book, avg_rating = round(avg_rating,2), review = review, count = count[0], rendered=rendered, res=res.json())
    elif request.method == "POST":
        #If this user hasn't rated the book or reviewed
        if (db.execute("SELECT rating FROM ratings WHERE userid = :userid AND bookid = :bookid", {"userid": userid[0], "bookid": book_id}).rowcount != 0
         or db.execute("SELECT review FROM reviews WHERE userid = :userid AND bookid = :bookid", {"userid": userid[0], "bookid": book_id}).rowcount != 0):
            rendered = 2
            current_review = request.form.get("review")
            rating = request.form.get("rating")
            #if the written review is blank, but rating is not (because it's posting), set the rating
            if current_review == None:
                db.execute("INSERT into ratings (bookid, userid, rating) VALUES (:bookid, :userid, :rating)",
                {"bookid": book_id, "userid": userid[0], "rating": rating})
                db.commit()
                all_rating = all_rating[0] + int(rating[0])
                count = count[0]+1
                avg_rating = all_rating/count
            else:
                db.execute("INSERT into reviews (bookid, review, userid) VALUES (:bookid, :review, :userid)",
                {"bookid": book_id, "review":current_review, "userid": userid[0]})
                db.commit()
                review = db.execute("SELECT review FROM reviews WHERE bookid = :bookid",{"bookid":book_id}).fetchall()
                #which_user = db.execute("SELECT u.username FROM u.users JOIN reviews r ON r.userid = u.id WHERE bookid = :bookid",{"bookid":book_id}).fetchone()

            return render_template("bookinfo.html", book = book, avg_rating = round(avg_rating,2), review = review, count = count[0], rendered=rendered)
        else:
            rendered = 4
            return render_template("error.html", message="You already Reviewed!")
