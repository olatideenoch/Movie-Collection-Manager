from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")

db = SQLAlchemy(app)



# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)

with app.app_context():
    db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )

# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

class RateMovieForm(FlaskForm):
    rating = StringField("Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.id))
    all_movies = result.scalars().all()
    return render_template("index.html", movies = all_movies)

@app.route("/edit", methods = ["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    update_movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        update_movie.rating = form.rating.data
        update_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=update_movie)

@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    delete_movie = db.get_or_404(Movie, movie_id)
    db.session.delete(delete_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods = ["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie = form.title.data
        url = "https://api.themoviedb.org/3/search/movie"
        headers = {
            "accept": "application/json",
            "Authorization": BEARER_TOKEN
        }
        params = {
            "query": movie,
            "include_adult": False,
            "page": 1,
            "language": "en-US"
            }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        results = data["results"]
        return render_template("select.html", results = results)
    return render_template("add.html", form = form)

@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie"
        MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
        api_key = os.environ.get("API_KEY")
        movie_url = f"{MOVIE_INFO_URL}/{movie_id}"
        response = requests.get(movie_url, params={"language": "en-US","api_key": api_key})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data["poster_path"]}",
            description=data["overview"],
            rating = 1.0,
            review = "This movie is so good",
            ranking = 5

        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=False)
