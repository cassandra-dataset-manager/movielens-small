from zipfile import ZipFile
from pandas import read_csv

from cassandra.cqlengine.models import Model
from cassandra.cqlengine.columns import *
from cassandra.cqlengine.connection import set_session


class Movie(Model):
    __table_name__ = 'movies'
    id = Integer(primary_key=True)
    name = Text()
    release_date = Date()
    video_release_date = Date()
    url = Text()
    tags = Set(Text)

class User(Model):
    __table_name__ = "users"
    id = Integer(primary_key=True)
    age = Integer()
    gender = Text()
    occupation = Text()
    zip = Text()


def main(context):
    context.feedback("Installing movielens")
    fp = context.download("http://files.grouplens.org/datasets/movielens/ml-100k.zip")
    zf = ZipFile(file=fp)
    tmp = zf.open("ml-100k/u.item")
    items = read_csv(tmp, sep="|", header=None, index_col=0,
                    names=[ "id", "name", "release_date", "video_release_date", "url", "unknown",
                            "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
                            "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",  "Musical",
                            "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"])
    for row in items.itertuples():
        # context.feedback(row.name)
        try:
            Movie.create(id=row.Index, name=row.name.encode("utf-8"),
                         url=str(row.url))
        except Exception as e:
            print e, row
    users = zf.open("ml-100k/u.user")
    users = read_csv(users, sep="|", header=None,
                     names=["id", "age", "gender", "occupation", "zip"], index_col=0)

    for user in users.itertuples():
        try:
            User.create(id=user.Index, age=user.age, gender=user.gender,
                        occupation=user.occupation, zip=user.zip)
        except Exception as e:
            print user.id, e

    # user id | item id | rating | timestamp
    data = zf.open("ml-100k/u.data")
    prepared = context.session.prepare("INSERT INTO ratings_by_movie (movie_id, user_id, rating, timestamp) VALUES (?, ?, ?, ?)")
    ratings = read_csv(data, sep="|", header=None,
                       names=["user_id", "movie_id", "rating", "timestamp"])

    for r in ratings.itertuples():
        try:
            context.session.execute(prepared, (r.movie_id, r.user_id, r.rating, r.timestamp))
        except Exception as e:
            print r, e



if __name__ == "__main__":
    from cdm import install_local
    install_local("movielens-small", main)
