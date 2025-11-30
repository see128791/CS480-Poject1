import random
from datetime import datetime

import mysql.connector
from faker import Faker

from app import DB_CONFIG

fake = Faker() # object to be used to create fake data
random.seed(42)

# specific to our use case of fake data
################
BIOS = ["Sharing moments, ideas, and things that inspire me.",
                "Just here for good vibes, good people, and good memories.",
                "Collecting snapshots of life one post at a time.",
                "Stories, highlights, and everything in between.",
                "Living life, capturing it, and posting the best parts."]

CAPTIONS = ["Mood powered by whatever’s playing right now.",
            "Finding that song that hits different.",
            "Today’s soundtrack on repeat.",
            "Good music, good energy, good day.",
            "If it sounds right, it feels right."]

COMMENTS = ["This one’s been on repeat all week.",
            "Didn’t expect to like this as much as I do.",
            "Instantly added to my playlist."
            "The vibe here is crazy good.",
            "Why does this fit my mood perfectly?"]

DESCRIPTIONS = ["A collection of songs that match the moment.",
                "Your soundtrack for calm mornings and easy nights.",
                "A mix of everything I’ve had on repeat lately.",
                "Handpicked tracks for when you just want to feel something.",
                "Music for focusing, thinking, or just existing."]
################

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_max_id(cursor, table, col):
    cursor.execute(f"SELECT COALESCE(MAX({col}), 0) FROM {table}")
    return cursor.fetchone()[0]


def seed_users(cursor, count=10):
    max_id = get_max_id(cursor, "Users", "User_ID")
    start_id = max_id + 1
    usernames = set()
    users = []

    for i in range(count):
        username = fake.user_name()
        while username in usernames:
            username = fake.user_name()
        usernames.add(username)
        users.append(
            (
                start_id + i,
                username,
                fake.password(length=10),
                fake.name(),
                random.choice(BIOS),
                "https://picsum.photos/842/741",
            )
        )

    cursor.executemany(
        """
        INSERT INTO Users (User_ID, Username, Password, Display_Name, Bio, Profile_Picture)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        users,
    )
    return [u[0] for u in users]


def seed_tracks(cursor, count=50):
    max_id = get_max_id(cursor, "Tracks", "Track_ID")
    start_id = max_id + 1
    tracks = []

    for i in range(count):
        tracks.append(
            (
                start_id + i,
                fake.word().title(),
                " ".join(fake.words(nb=2)).title(),
                "https://picsum.photos/842/741",
                fake.name(),
                random.randint(1990, datetime.now().year),
            )
        )

    cursor.executemany(
        """
        INSERT INTO Tracks (Track_ID, Name, Album, Cover_Image, Artist, Year)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        tracks,
    )
    return [t[0] for t in tracks]


def seed_playlists(cursor, user_ids, count=10):
    max_id = get_max_id(cursor, "Playlists", "Playlist_ID")
    start_id = max_id + 1
    playlists = []

    for i in range(count):
        playlists.append(
            (
                start_id + i,
                random.choice(user_ids),
                fake.word().capitalize() + " Mix",
                random.choice(DESCRIPTIONS),
                "https://picsum.photos/842/741",
                random.choice([True, False]),
            )
        )

    cursor.executemany(
        """
        INSERT INTO Playlists (Playlist_ID, User_ID, Name, Description, Cover_Image, Is_Favorites)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        playlists,
    )
    return [p[0] for p in playlists]


def seed_playlist_contents(cursor, playlist_ids, track_ids, max_tracks_per_playlist=8):
    rows = []
    for playlist_id in playlist_ids:
        tracks = random.sample(track_ids, k=random.randint(1, max_tracks_per_playlist))
        rows.extend((playlist_id, tid) for tid in tracks)

    cursor.executemany(
        """
        INSERT INTO Playlist_Contents (Playlist_ID, Track_ID)
        VALUES (%s, %s)
        """,
        rows,
    )


def seed_friendships(cursor, user_ids, count=10):
    max_id = get_max_id(cursor, "Friendships", "Friendship_ID")
    start_id = max_id + 1
    seen_pairs = set()
    friendships = []

    while len(friendships) < count:
        u1, u2 = random.sample(user_ids, 2)
        pair = tuple(sorted((u1, u2)))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        status = random.choice(["Pending", "Accepted", "Rejected"])
        friendships.append((start_id + len(friendships), u1, u2, status))

    cursor.executemany(
        """
        INSERT INTO Friendships (Friendship_ID, User_ID_1, User_ID_2, Status)
        VALUES (%s, %s, %s, %s)
        """,
        friendships,
    )


def seed_posts(cursor, user_ids, track_ids, count=50):
    max_id = get_max_id(cursor, "Posts", "Post_ID")
    start_id = max_id + 1
    posts = []

    for i in range(count):
        posts.append(
            (
                start_id + i,
                random.choice(user_ids),
                random.choice(track_ids),
                random.choice(CAPTIONS),
                fake.date_time_this_year(),
            )
        )

    cursor.executemany(
        """
        INSERT INTO Posts (Post_ID, User_ID, Track_ID, Caption, Time)
        VALUES (%s, %s, %s, %s, %s)
        """,
        posts,
    )
    return [p[0] for p in posts]


def seed_likes(cursor, post_ids, user_ids, max_likes_per_post=5):
    max_id = get_max_id(cursor, "Likes", "Like_ID")
    next_id = max_id + 1
    likes = []

    for post_id in post_ids:
        likers = random.sample(user_ids, k=random.randint(0, max_likes_per_post))
        for uid in likers:
            likes.append((next_id, post_id, uid))
            next_id += 1

    cursor.executemany(
        """
        INSERT IGNORE INTO Likes (Like_ID, Post_ID, User_ID)
        VALUES (%s, %s, %s)
        """,
        likes,
    )


def seed_comments(cursor, post_ids, user_ids, count=25):
    max_id = get_max_id(cursor, "Comments", "Comment_ID")
    start_id = max_id + 1
    comments = []

    for i in range(count):
        comments.append(
            (
                start_id + i,
                random.choice(post_ids),
                random.choice(user_ids),
                random.choice(COMMENTS),
            )
        )

    cursor.executemany(
        """
        INSERT INTO Comments (Comment_ID, Post_ID, User_ID, Comment)
        VALUES (%s, %s, %s, %s)
        """,
        comments,
    )


def main():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        user_ids = seed_users(cursor)
        track_ids = seed_tracks(cursor)
        playlist_ids = seed_playlists(cursor, user_ids)
        seed_playlist_contents(cursor, playlist_ids, track_ids)
        seed_friendships(cursor, user_ids)
        post_ids = seed_posts(cursor, user_ids, track_ids)
        seed_likes(cursor, post_ids, user_ids)
        seed_comments(cursor, post_ids, user_ids)
        conn.commit()
        print("Seeding completed successfully.")
    except Exception as exc:
        conn.rollback()
        print(f"Error during seeding: {exc}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
