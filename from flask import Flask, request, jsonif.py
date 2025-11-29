from flask import Flask, request, jsonify
import mysql.connector
import datetime

# --- 1. Database Configuration ---
# NOTE: Replace these with your actual MySQL credentials
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_username',
    'password': 'see123456',# this is my password. change it
    'database': 'SpotSocialDB' # Or whatever you named your database
}

app = Flask(__name__)

# Helper function to establish a database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# --- 2. API Endpoint: User Sign Up (Register) ---

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    display_name = data.get('display_name')

    if not all([username, password, display_name]):
        return jsonify({'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

    cursor = conn.cursor()
    
    # Get next User_ID (Should be handled by AUTO_INCREMENT in production)
    cursor.execute("SELECT MAX(User_ID) FROM Users")
    max_id = cursor.fetchone()[0]
    new_user_id = (max_id if max_id is not None else 0) + 1
    insert_query = """
    INSERT INTO Users (User_ID, Username, Password, Display_Name)
    VALUES (%s, %s, %s, %s)
    """
    try:
        cursor.execute(insert_query, (new_user_id, username, password, display_name))
        conn.commit()
        return jsonify({
            'message': 'User registered successfully!',
            'user_id': new_user_id
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({'message': f'Username "{username}" is already taken.'}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500
    finally:
        cursor.close()
        conn.close()

# --- 3. API Endpoint: User Login ---

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password') 

    if not all([username, password]):
        return jsonify({'message': 'Missing username or password'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

    cursor = conn.cursor(dictionary=True)
    query = "SELECT User_ID, Password, Display_Name FROM Users WHERE Username = %s"

    try:
        cursor.execute(query, (username,))
        user_record = cursor.fetchone()
        
        if user_record:
            if password == user_record['Password']:
                return jsonify({
                    'message': 'Login successful!',
                    'user_id': user_record['User_ID'],
                    'display_name': user_record['Display_Name']
                }), 200
            else:
                return jsonify({'message': 'Invalid username or password.'}), 401
        else:
            return jsonify({'message': 'Invalid username or password.'}), 401
            
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred during login: {e}'}), 500
    finally:
        cursor.close()
        conn.close()

# --- 4. API Endpoint: Track Search ---

@app.route('/tracks/search', methods=['GET'])
def search_tracks():
    search_term = request.args.get('q', '') 

    if not search_term:
        return jsonify({'message': 'Please provide a search query using the "q" parameter.'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

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
        return jsonify({'message': f'An unexpected error occurred during search: {e}'}), 500
    finally:
        cursor.close()
        conn.close()

# --- 5. API Endpoint: Create Music Post ---

@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    user_id = data.get('user_id')
    track_id = data.get('track_id')
    caption = data.get('caption', '')

    if not all([user_id, track_id]):
        return jsonify({'message': 'Missing required fields: user_id and track_id'}), 400
    
    try:
        user_id = int(user_id)
        track_id = int(track_id)
    except ValueError:
        return jsonify({'message': 'user_id and track_id must be integers'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

    cursor = conn.cursor()
    
    # Get next Post_ID 
    cursor.execute("SELECT MAX(Post_ID) FROM Posts")
    max_id = cursor.fetchone()[0]
    new_post_id = (max_id if max_id is not None else 0) + 1
    
    post_time = datetime.datetime.now()

    insert_query = """
    INSERT INTO Posts (Post_ID, User_ID, Track_ID, Caption, Time)
    VALUES (%s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(insert_query, (new_post_id, user_id, track_id, caption, post_time))
        conn.commit()
        return jsonify({
            'message': 'Music post created successfully!',
            'post_id': new_post_id,
            'time': post_time.isoformat()
        }), 201

    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'message': f'Database error: Could not create post. Check if User_ID or Track_ID are valid. Error: {e}'}), 500
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500
    finally:
        cursor.close()
        conn.close()

# --- 6. API Endpoint: Send Friend Request ---

@app.route('/friends/request', methods=['POST'])
def send_friend_request():
    data = request.get_json()
    sender_id = data.get('sender_id')
    recipient_id = data.get('recipient_id')

    if not all([sender_id, recipient_id]):
        return jsonify({'message': 'Missing required fields: sender_id and recipient_id'}), 400
    
    try:
        sender_id = int(sender_id)
        recipient_id = int(recipient_id)
    except ValueError:
        return jsonify({'message': 'User IDs must be integers'}), 400
        
    if sender_id == recipient_id:
        return jsonify({'message': 'Cannot send a friend request to yourself.'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

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
            if status == 'Accepted':
                return jsonify({'message': 'You are already friends with this user.'}), 409
            elif status == 'Pending':
                return jsonify({'message': 'A pending friend request already exists.'}), 409
        
        # Get next Friendship_ID
        cursor.execute("SELECT MAX(Friendship_ID) FROM Friendships")
        max_id = cursor.fetchone()[0]
        new_friendship_id = (max_id if max_id is not None else 0) + 1
        
        insert_query = """
        INSERT INTO Friendships (Friendship_ID, User_ID_1, User_ID_2, Status)
        VALUES (%s, %s, %s, 'Pending')
        """
        cursor.execute(insert_query, (new_friendship_id, sender_id, recipient_id))
        conn.commit()
        
        return jsonify({
            'message': 'Friend request sent successfully!',
            'friendship_id': new_friendship_id
        }), 201

    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'message': f'Database error: Could not send request. Error: {e}'}), 500
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500
    finally:
        cursor.close()
        conn.close()


# --- 7. API Endpoint: Accept/Reject Friend Request ---

@app.route('/friends/response', methods=['POST'])
def respond_friend_request():
    """
    Handles accepting or rejecting a pending friend request.
    Expects JSON data with: recipient_id, sender_id, action (Accept/Reject).
    """
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    sender_id = data.get('sender_id')
    action = data.get('action') # 'Accept' or 'Reject'

    # 1. Basic Input Validation
    if not all([recipient_id, sender_id, action]):
        return jsonify({'message': 'Missing required fields: recipient_id, sender_id, or action'}), 400
    
    try:
        recipient_id = int(recipient_id)
        sender_id = int(sender_id)
    except ValueError:
        return jsonify({'message': 'User IDs must be integers'}), 400

    if action not in ['Accept', 'Reject']:
        return jsonify({'message': 'Invalid action. Must be "Accept" or "Reject"'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Server error: Could not connect to database'}), 500

    cursor = conn.cursor()
    
    # 2. Find the PENDING request
    # Note: The original request was sent as (User_ID_1=sender, User_ID_2=recipient)
    find_query = """
    SELECT Friendship_ID FROM Friendships
    WHERE User_ID_1 = %s AND User_ID_2 = %s AND Status = 'Pending'
    """
    
    try:
        cursor.execute(find_query, (sender_id, recipient_id))
        friendship_record = cursor.fetchone()

        if not friendship_record:
            return jsonify({'message': 'Pending request not found between these users.'}), 404
        
        friendship_id = friendship_record[0]
        
        # 3. Update the Status
        new_status = 'Accepted' if action == 'Accept' else 'Rejected'
        
        update_query = """
        UPDATE Friendships
        SET Status = %s
        WHERE Friendship_ID = %s
        """
        cursor.execute(update_query, (new_status, friendship_id))
        conn.commit()
        
        return jsonify({
            'message': f'Friend request {action.lower()}ed successfully!',
            'friendship_id': friendship_id,
            'status': new_status
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)