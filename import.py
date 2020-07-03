import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))
# Configure session to use filesystem
#app.config["SQLALCHEMY_DATABASE URI"] = "postgres://kuemuxdskkddiy:589546675e05179303035e9d4ccc5af56d1eadf4fe3750a9ca7cf0389e4f70fb@ec2-54-159-138-67.compute-1.amazonaws.com:5432/db0cm71dt31mcn"

# Set up database

db = scoped_session(sessionmaker(bind=engine))
db.execute("CREATE TABLE reviews (id smallint, review text)")
#with open("books.csv", 'r') as csvfile:
#    reader = csv.DictReader(csvfile)

#    for row in reader:
#        isbn = row['isbn']
#        title = row['title']
#        author = row['author']
#        year = row['year']
#        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
db.commit()
