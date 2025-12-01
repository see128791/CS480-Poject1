from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
import datetime
import random

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "",
    "password": "",
    "database": "SpotSocialDB",
}

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_string"

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

CAPTIONS = [
    "Mood powered by whatever's playing right now.",
    "Finding that song that hits different.",
    "Today's soundtrack on repeat.",
    "Good music, good energy, good day.",
    "If it sounds right, it feels right.",
]

DESCRIPTIONS = [
    "A collection of songs that match the moment.",
    "Your soundtrack for calm mornings and easy nights.",
    "A mix of everything I've had on repeat lately.",
    "Handpicked tracks for when you just want to feel something.",
    "Music for focusing, thinking, or just existing.",
]

def create_demo_content_for_user(user_id: int):
    conn = get_db_connection()
    if conn is None:
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT Track_ID FROM Tracks")
        track_ids = [r[0] for r in cur.fetchall()]
        if not track_ids:
            print("No tracks in DB, run faker_db.py first.")
            return
        cur.execute("SELECT COALESCE(MAX(Post_ID), 0) FROM Posts")
        next_post_id = cur.fetchone()[0] + 1
        cur.execute("SELECT COALESCE(MAX(Playlist_ID), 0) FROM Playlists")
        next_playlist_id = cur.fetchone()[0] + 1
        now = datetime.datetime.now()
        posts = []
        for i in range(3):
            posts.append(
                (
                    next_post_id,
                    user_id,
                    random.choice(track_ids),
                    random.choice(CAPTIONS),
                    now - datetime.timedelta(minutes=i * 3),
                )
            )
            next_post_id += 1
        cur.executemany(
            """
            INSERT INTO Posts (Post_ID, User_ID, Track_ID, Caption, Time)
            VALUES (%s, %s, %s, %s, %s)
            """,
            posts,
        )
        cur.execute(
            """
            INSERT INTO Playlists (Playlist_ID, User_ID, Name, Description, Cover_Image, Is_Favorites)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                next_playlist_id,
                user_id,
                "My First Mix",
                random.choice(DESCRIPTIONS),
                "https://picsum.photos/842/741",
                False,
            ),
        )
        conn.commit()
        print(f"Demo content created for user {user_id}")
    except Exception as e:
        conn.rollback()
        print("Error in create_demo_content_for_user:", e)
    finally:
        cur.close()
        conn.close()

@app.route("/register", methods=["POST"])
def register_user():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    username = data.get("username")
    password = data.get("password")
    display_name = data.get("display_name")
    if not all([username, password, display_name]):
        msg = "Missing required fields"
        if request.is_json:
            return jsonify({"message": msg}), 400
        return render_template("register.html", error=msg)
    conn = get_db_connection()
    if conn is None:
        msg = "Server error: Could not connect to database"
        if request.is_json:
            return jsonify({"message": msg}), 500
        return render_template("register.html", error=msg)
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(User_ID), 0) FROM Users")
    max_id = cursor.fetchone()[0]
    new_user_id = max_id + 1
    insert_query = """
        INSERT INTO Users (User_ID, Username, Password, Display_Name)
        VALUES (%s, %s, %s, %s)
    """
    try:
        cursor.execute(insert_query, (new_user_id, username, password, display_name))
        conn.commit()
        create_demo_content_for_user(new_user_id)
        if request.is_json:
            return (
                jsonify(
                    {
                        "message": "User registered successfully!",
                        "user_id": new_user_id,
                    }
                ),
                201,
            )
        else:
            return redirect(url_for("login_user"))
    except mysql.connector.IntegrityError:
        conn.rollback()
        msg = f'Username "{username}" is already taken.'
        if request.is_json:
            return jsonify({"message": msg}), 409
        return render_template("register.html", error=msg)
    except Exception as e:
        conn.rollback()
        msg = f"An unexpected error occurred: {e}"
        if request.is_json:
            return jsonify({"message": msg}), 500
        return render_template("register.html", error=msg)
    finally:
        cursor.close()
        conn.close()

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("register.html")
    return register_user()

@app.route("/login", methods=["GET", "POST"])
def login_user():
    if request.method == "GET":
        return render_template("login.html")
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    username = data.get("username")
    password = data.get("password")
    if not all([username, password]):
        msg = "Missing username or password"
        if request.is_json:
            return jsonify({"message": msg}), 400
        return render_template("login.html", error=msg)
    conn = get_db_connection()
    if conn is None:
        msg = "Server error: Could not connect to database"
        if request.is_json:
            return jsonify({"message": msg}), 500
        return render_template("login.html", error=msg)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT User_ID, Password, Display_Name FROM Users WHERE Username = %s"
    try:
        cursor.execute(query, (username,))
        user_record = cursor.fetchone()
        if user_record and password == user_record["Password"]:
            session["user_id"] = user_record["User_ID"]
            session["display_name"] = user_record["Display_Name"]
            if request.is_json:
                return (
                    jsonify(
                        {
                            "message": "Login successful!",
                            "user_id": user_record["User_ID"],
                            "display_name": user_record["Display_Name"],
                        }
                    ),
                    200,
                )
            else:
                return redirect(url_for("profile"))
        else:
            msg = "Invalid username or password."
            if request.is_json:
                return jsonify({"message": msg}), 401
            return render_template("login.html", error=msg)
    except Exception as e:
        msg = f"An unexpected error occurred during login: {e}"
        if request.is_json:
            return jsonify({"message": msg}), 500
        return render_template("login.html", error="Unexpected error during login.")
    finally:
        cursor.close()
        conn.close()

@app.route("/tracks/search", methods=["GET"])
def search_tracks():
    search_term = request.args.get("q", "")
    if not search_term:
        return (
            jsonify(
                {"message": 'Please provide a search query using the "q" parameter.'}
            ),
            400,
        )
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Server error: Could not connect to database"}), 500
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT Track_ID, Name, Album, Cover_Image, Artist, Year
        FROM Tracks
        WHERE Name LIKE %s OR Artist LIKE %s
    """
    search_pattern = f"%{search_term}%"
    try:
        cursor.execute(query, (search_pattern, search_pattern))
        tracks = cursor.fetchall()
        return jsonify(tracks), 200
    except Exception as e:
        return (
            jsonify({"message": f"An unexpected error occurred during search: {e}"}),
            500,
        )
    finally:
        cursor.close()
        conn.close()

@app.route("/posts", methods=["POST"])
def create_post():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    user_id = data.get("user_id")
    track_id = data.get("track_id")
    caption = data.get("caption", "")
    if not all([user_id, track_id]):
        return (
            jsonify({"message": "Missing required fields: user_id and track_id"}),
            400,
        )
    try:
        user_id = int(user_id)
        track_id = int(track_id)
    except ValueError:
        return jsonify({"message": "user_id and track_id must be integers"}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Server error: Could not connect to database"}), 500
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(Post_ID), 0) FROM Posts")
    max_id = cursor.fetchone()[0]
    new_post_id = max_id + 1
    post_time = datetime.datetime.now()
    insert_query = """
        INSERT INTO Posts (Post_ID, User_ID, Track_ID, Caption, Time)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(
            insert_query, (new_post_id, user_id, track_id, caption, post_time)
        )
        conn.commit()
        return (
            jsonify(
                {
                    "message": "Music post created successfully!",
                    "post_id": new_post_id,
                    "time": post_time.isoformat(),
                }
            ),
            201,
        )
    except mysql.connector.Error as e:
        conn.rollback()
        return (
            jsonify(
                {
                    "message": f"Database error: Could not create post. Check if User_ID or Track_ID are valid. Error: {e}"
                }
            ),
            500,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"An unexpected error occurred: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/posts/<int:post_id>/like", methods=["POST"])
def toggle_like(post_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT Like_ID FROM Likes WHERE Post_ID = %s AND User_ID = %s",
            (post_id, user_id),
        )
        row = cursor.fetchone()
        if row:
            cursor.execute("DELETE FROM Likes WHERE Like_ID = %s", (row[0],))
            liked = False
        else:
            cursor.execute("SELECT COALESCE(MAX(Like_ID), 0) FROM Likes")
            max_like_id = cursor.fetchone()[0]
            new_like_id = max_like_id + 1
            cursor.execute(
                "INSERT INTO Likes (Like_ID, Post_ID, User_ID) VALUES (%s, %s, %s)",
                (new_like_id, post_id, user_id),
            )
            liked = True
        conn.commit()
        cursor.execute(
            "SELECT COUNT(*) FROM Likes WHERE Post_ID = %s",
            (post_id,),
        )
        like_count = cursor.fetchone()[0]
        return jsonify({"liked": liked, "like_count": like_count}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error toggling like: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    data = request.get_json() if request.is_json else request.form
    text = data.get("comment", "").strip()
    if not text:
        return jsonify({"message": "Comment cannot be empty"}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(Comment_ID), 0) FROM Comments")
        max_id = cursor.fetchone()[0]
        new_comment_id = max_id + 1
        cursor.execute(
            """
            INSERT INTO Comments (Comment_ID, Post_ID, User_ID, Comment)
            VALUES (%s, %s, %s, %s)
            """,
            (new_comment_id, post_id, user_id, text),
        )
        conn.commit()
        cursor.execute(
            "SELECT COUNT(*) FROM Comments WHERE Post_ID = %s",
            (post_id,),
        )
        comment_count = cursor.fetchone()[0]
        return (
            jsonify(
                {
                    "message": "Comment added",
                    "comment_id": new_comment_id,
                    "comment_count": comment_count,
                }
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error adding comment: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/posts/<int:post_id>/comments", methods=["GET"])
def list_comments(post_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT c.Comment_ID,
                   c.Comment,
                   u.Username,
                   u.Display_Name
            FROM Comments c
            JOIN Users u ON c.User_ID = u.User_ID
            WHERE c.Post_ID = %s
            ORDER BY c.Comment_ID ASC
            """,
            (post_id,),
        )
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching comments: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/friends/request", methods=["POST"])
def send_friend_request():
    data = request.get_json() if request.is_json else request.form
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    if not all([sender_id, recipient_id]):
        return (
            jsonify(
                {"message": "Missing required fields: sender_id and recipient_id"}
            ),
            400,
        )
    try:
        sender_id = int(sender_id)
        recipient_id = int(recipient_id)
    except ValueError:
        return jsonify({"message": "User IDs must be integers"}), 400
    if sender_id == recipient_id:
        return jsonify({"message": "Cannot send a friend request to yourself."}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Server error: Could not connect to database"}), 500
    cursor = conn.cursor()
    check_query = """
        SELECT Friendship_ID, Status FROM Friendships
        WHERE (User_ID_1 = %s AND User_ID_2 = %s)
           OR (User_ID_1 = %s AND User_ID_2 = %s)
    """
    try:
        cursor.execute(check_query, (sender_id, recipient_id, recipient_id, sender_id))
        existing_friendship = cursor.fetchone()
        if existing_friendship:
            status = existing_friendship[1]
            if status == "Accepted":
                return (
                    jsonify({"message": "You are already friends with this user."}),
                    409,
                )
            elif status == "Pending":
                return (
                    jsonify({"message": "A pending friend request already exists."}),
                    409,
                )
        cursor.execute("SELECT COALESCE(MAX(Friendship_ID), 0) FROM Friendships")
        max_id = cursor.fetchone()[0]
        new_friendship_id = max_id + 1
        insert_query = """
            INSERT INTO Friendships (Friendship_ID, User_ID_1, User_ID_2, Status)
            VALUES (%s, %s, %s, 'Pending')
        """
        cursor.execute(insert_query, (new_friendship_id, sender_id, recipient_id))
        conn.commit()
        return (
            jsonify(
                {
                    "message": "Friend request sent successfully!",
                    "friendship_id": new_friendship_id,
                }
            ),
            201,
        )
    except mysql.connector.Error as e:
        conn.rollback()
        return (
            jsonify(
                {"message": f"Database error: Could not send request. Error: {e}"}
            ),
            500,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"An unexpected error occurred: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/friends/response", methods=["POST"])
def respond_friend_request():
    data = request.get_json() if request.is_json else request.form
    recipient_id = data.get("recipient_id")
    sender_id = data.get("sender_id")
    action = data.get("action")
    if not all([recipient_id, sender_id, action]):
        return (
            jsonify(
                {
                    "message": "Missing required fields: recipient_id, sender_id, or action"
                }
            ),
            400,
        )
    try:
        recipient_id = int(recipient_id)
        sender_id = int(sender_id)
    except ValueError:
        return jsonify({"message": "User IDs must be integers"}), 400
    if action not in ["Accept", "Reject"]:
        return jsonify({"message": 'Invalid action. Must be "Accept" or "Reject"'}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Server error: Could not connect to database"}), 500
    cursor = conn.cursor()
    find_query = """
        SELECT Friendship_ID FROM Friendships
        WHERE User_ID_1 = %s AND User_ID_2 = %s AND Status = 'Pending'
    """
    try:
        cursor.execute(find_query, (sender_id, recipient_id))
        friendship_record = cursor.fetchone()
        if not friendship_record:
            return (
                jsonify({"message": "Pending request not found between these users."}),
                404,
            )
        friendship_id = friendship_record[0]
        new_status = "Accepted" if action == "Accept" else "Rejected"
        update_query = """
            UPDATE Friendships
            SET Status = %s
            WHERE Friendship_ID = %s
        """
        cursor.execute(update_query, (new_status, friendship_id))
        conn.commit()
        return (
            jsonify(
                {
                    "message": f"Friend request {action.lower()}ed successfully!",
                    "friendship_id": friendship_id,
                    "status": new_status,
                }
            ),
            200,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"An unexpected error occurred: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/friends/request/by-username", methods=["POST"])
def send_friend_request_by_username():
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401
    data = request.get_json() if request.is_json else request.form
    target_username = data.get("target_username")
    if not target_username:
        return jsonify({"message": "Missing target_username"}), 400
    sender_id = session["user_id"]
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT User_ID FROM Users WHERE Username = %s",
            (target_username,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"message": "User not found"}), 404
        recipient_id = row["User_ID"]
        if sender_id == recipient_id:
            return jsonify({"message": "You cannot add yourself as a friend."}), 400
        cursor.execute(
            """
            SELECT Friendship_ID, Status
            FROM Friendships
            WHERE (User_ID_1 = %s AND User_ID_2 = %s)
               OR (User_ID_1 = %s AND User_ID_2 = %s)
            """,
            (sender_id, recipient_id, recipient_id, sender_id),
        )
        existing = cursor.fetchone()
        if existing:
            status = existing["Status"]
            if status == "Accepted":
                return jsonify({"message": "You are already friends."}), 409
            if status == "Pending":
                return jsonify({"message": "Friend request already pending."}), 409
        cursor.execute("SELECT COALESCE(MAX(Friendship_ID), 0) AS maxid FROM Friendships")
        maxid = cursor.fetchone()["maxid"]
        new_id = maxid + 1
        cursor.execute(
            """
            INSERT INTO Friendships (Friendship_ID, User_ID_1, User_ID_2, Status)
            VALUES (%s, %s, %s, 'Pending')
            """,
            (new_id, sender_id, recipient_id),
        )
        conn.commit()
        return jsonify({"message": "Friend request sent!", "friendship_id": new_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error sending friend request: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/")
def home():
    return redirect(url_for("login_user"))

@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_user"))
    conn = get_db_connection()
    if conn is None:
        return "Database error", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT User_ID, Username, Display_Name, Bio, Profile_Picture
            FROM Users
            WHERE User_ID = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        cursor.execute(
            """
            SELECT p.Post_ID,
                   p.Caption,
                   p.Time,
                   t.Name AS Track_Name,
                   t.Artist,
                   t.Cover_Image,
                   COALESCE(lc.LikeCount, 0) AS Like_Count,
                   COALESCE(cc.CommentCount, 0) AS Comment_Count
            FROM Posts p
            JOIN Tracks t ON p.Track_ID = t.Track_ID
            LEFT JOIN (
                SELECT Post_ID, COUNT(*) AS LikeCount
                FROM Likes
                GROUP BY Post_ID
            ) lc ON p.Post_ID = lc.Post_ID
            LEFT JOIN (
                SELECT Post_ID, COUNT(*) AS CommentCount
                FROM Comments
                GROUP BY Post_ID
            ) cc ON p.Post_ID = cc.Post_ID
            WHERE p.User_ID = %s
            ORDER BY p.Time DESC
            """,
            (user_id,),
        )
        posts = cursor.fetchall()
        cursor.execute(
            """
            SELECT Playlist_ID, Name, Description, Cover_Image, Is_Favorites
            FROM Playlists
            WHERE User_ID = %s
            """,
            (user_id,),
        )
        playlists = cursor.fetchall()
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM Friendships
            WHERE (User_ID_1 = %s OR User_ID_2 = %s)
              AND Status = 'Accepted'
            """,
            (user_id, user_id),
        )
        friend_count = cursor.fetchone()["cnt"]
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Posts WHERE User_ID = %s",
            (user_id,),
        )
        post_count = cursor.fetchone()["cnt"]
        cursor.execute(
            """
            SELECT f.Friendship_ID,
                   f.User_ID_1 AS Sender_ID,
                   u.Username AS Sender_Username,
                   u.Display_Name AS Sender_Display_Name
            FROM Friendships f
            JOIN Users u ON f.User_ID_1 = u.User_ID
            WHERE f.User_ID_2 = %s AND f.Status = 'Pending'
            """,
            (user_id,),
        )
        pending_requests = cursor.fetchall()
        return render_template(
            "profile.html",
            user=user,
            posts=posts,
            playlists=playlists,
            friend_count=friend_count,
            post_count=post_count,
            pending_requests=pending_requests,
        )
    finally:
        cursor.close()
        conn.close()
        
@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_user"))

    conn = get_db_connection()
    if conn is None:
        return "Database error", 500

    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == "GET":
            cursor.execute(
                """
                SELECT User_ID, Username, Display_Name, Bio, Profile_Picture
                FROM Users
                WHERE User_ID = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            if not user:
                return "User not found", 404
            return render_template("edit_profile.html", user=user)

        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        profile_picture = request.form.get("profile_picture", "").strip()

        if not display_name:
            cursor.execute(
                """
                SELECT User_ID, Username, Display_Name, Bio, Profile_Picture
                FROM Users
                WHERE User_ID = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            error = "Display name cannot be empty."
            return render_template("edit_profile.html", user=user, error=error)

        cursor.execute(
            """
            UPDATE Users
            SET Display_Name = %s,
                Bio = %s,
                Profile_Picture = %s
            WHERE User_ID = %s
            """,
            (display_name, bio or None, profile_picture or None, user_id),
        )
        conn.commit()
        session["display_name"] = display_name
        return redirect(url_for("profile"))
    except Exception as e:
        conn.rollback()
        return f"Error updating profile: {e}", 500
    finally:
        cursor.close()
        conn.close()



@app.route("/feed")
def feed():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_user"))
    conn = get_db_connection()
    if conn is None:
        return "DB error", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN User_ID_1 = %s THEN User_ID_2
                    ELSE User_ID_1
                END AS Friend_ID
            FROM Friendships
            WHERE (User_ID_1 = %s OR User_ID_2 = %s)
              AND Status = 'Accepted'
            """,
            (user_id, user_id, user_id),
        )
        rows = cursor.fetchall()
        friend_ids = [r["Friend_ID"] for r in rows]
        feed_user_ids = [user_id] + friend_ids
        if not feed_user_ids:
            feed_posts = []
        else:
            placeholders = ", ".join(["%s"] * len(feed_user_ids))
            query = f"""
                SELECT p.Post_ID,
                       p.Caption,
                       p.Time,
                       t.Name AS Track_Name,
                       t.Artist,
                       t.Cover_Image,
                       u.Display_Name,
                       u.Username,
                       u.Profile_Picture,
                       COALESCE(lc.LikeCount, 0) AS Like_Count,
                       COALESCE(cc.CommentCount, 0) AS Comment_Count
                FROM Posts p
                JOIN Tracks t ON p.Track_ID = t.Track_ID
                JOIN Users u ON p.User_ID = u.User_ID
                LEFT JOIN (
                    SELECT Post_ID, COUNT(*) AS LikeCount
                    FROM Likes
                    GROUP BY Post_ID
                ) lc ON p.Post_ID = lc.Post_ID
                LEFT JOIN (
                    SELECT Post_ID, COUNT(*) AS CommentCount
                    FROM Comments
                    GROUP BY Post_ID
                ) cc ON p.Post_ID = cc.Post_ID
                WHERE p.User_ID IN ({placeholders})
                ORDER BY p.Time DESC
                LIMIT 50
            """
            cursor.execute(query, tuple(feed_user_ids))
            feed_posts = cursor.fetchall()
        return render_template("feed.html", posts=feed_posts, user_id=user_id)
    finally:
        cursor.close()
        conn.close()

@app.route("/playlist")
def playlist():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_user"))
    conn = get_db_connection()
    if conn is None:
        return "DB error", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN User_ID_1 = %s THEN User_ID_2
                    ELSE User_ID_1
                END AS Friend_ID
            FROM Friendships
            WHERE (User_ID_1 = %s OR User_ID_2 = %s)
            AND Status = 'Accepted'
            """,
            (user_id, user_id, user_id),
        )
        rows = cursor.fetchall()
        friend_ids = [r["Friend_ID"] for r in rows]
        feed_user_ids = [user_id] + friend_ids
        if not feed_user_ids:
            feed_posts = []
        else:
            placeholders = ", ".join(["%s"] * len(feed_user_ids))
            query = f"""
                SELECT p.Post_ID,
                    p.Caption,
                    p.Time,
                    t.Name AS Track_Name,
                    t.Artist,
                    t.Cover_Image,
                    u.Display_Name,
                    u.Username,
                    u.Profile_Picture,
                    COALESCE(lc.LikeCount, 0) AS Like_Count,
                    COALESCE(cc.CommentCount, 0) AS Comment_Count
                FROM Posts p
                JOIN Tracks t ON p.Track_ID = t.Track_ID
                JOIN Users u ON p.User_ID = u.User_ID
                LEFT JOIN (
                    SELECT Post_ID, COUNT(*) AS LikeCount
                    FROM Likes
                    GROUP BY Post_ID
                ) lc ON p.Post_ID = lc.Post_ID
                LEFT JOIN (
                    SELECT Post_ID, COUNT(*) AS CommentCount
                    FROM Comments
                    GROUP BY Post_ID
                ) cc ON p.Post_ID = cc.Post_ID
                WHERE p.User_ID IN ({placeholders})
                ORDER BY p.Time DESC
                LIMIT 50
            """
            cursor.execute(query, tuple(feed_user_ids))
            feed_posts = cursor.fetchall()
        return render_template("playlist.html", posts=feed_posts, user_id=user_id)
    finally:
        cursor.close()
        conn.close()


@app.route("/posts/playlist", methods=["POST"])
def post_playlist():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    data = request.get_json() if request.is_json else request.form
    Name = data.get("Name", "").strip()
    Description = data.get("Description", "").strip()
    Cover_Image = data.get("Cover_Image", "").strip()
    Is_Favorites = 0
    if not Name:
        return jsonify({"message": "Name cannot be empty"}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(Playlist_ID), 0) FROM Playlists")
        max_id = cursor.fetchone()[0]
        new_playlist_id = max_id + 1
        cursor.execute(
            """
            INSERT INTO Playlists (Playlist_ID, User_ID, Name, Description, Cover_Image, Is_Favorites)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (new_playlist_id, user_id, Name, Description, Cover_Image, Is_Favorites),
        )
        conn.commit()
        return (
            jsonify(
                {
                    "Message": "playlist added"
                }
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error adding playlist: {e}"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/playlist/get", methods=["GET"])
def get_playlists():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT Playlist_ID, Name, Description, Cover_Image, Is_Favorites
            FROM Playlists
            WHERE User_ID = %s
            ORDER BY Is_Favorites DESC, Name ASC;
            """,
            (user_id,),
        )
        
        playlists = cursor.fetchall()
        return playlists
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error adding playlist: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/playlist/get/contents/tracks/<int:playlist_id>")
def get_playlist_tracks(playlist_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT Playlists.Playlist_ID, Tracks.Name, Tracks.Album, Tracks.Cover_Image, Tracks.Artist, Tracks.Year 
            FROM Playlists
            JOIN Playlist_Contents ON Playlists.Playlist_ID = Playlist_Contents.Playlist_ID
            JOIN Tracks ON Playlist_Contents.Track_ID = Tracks.Track_ID
            WHERE Playlists.Playlist_ID = %s
            ORDER BY Tracks.Album, Tracks.Name;
            """,
            (playlist_id,),
        )
        
        tracks = cursor.fetchall()
        return tracks
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({"message": f"Error adding playlist: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/posts/playlist/content", methods=["POST"])
def post_playlist_content():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Not logged in"}), 401
    data = request.get_json() if request.is_json else request.form
    Track_ID = data.get("Track_ID", "").strip()
    Playlist_ID = data.get("Playlist_ID", "").strip()
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "DB connection error"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Playlist_Contents (Playlist_ID, Track_ID)
            VALUES (%s, %s)
            """,
            (Playlist_ID, Track_ID),
        )
        conn.commit()
        return (
            jsonify(
                {
                    "Message": "playlist added"
                }
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error adding playlist: {e}"}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True)
