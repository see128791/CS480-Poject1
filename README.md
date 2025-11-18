# SpotSocial

## 1. Requirement Analysis

### 1.1 Project Overview

**SpotSocial** is a web-based social music platform where users create profiles, add friends, and share songs or playlists with each other. Each user maintains a personalized feed of “music posts” from themselves and their friends, can like/comment on posts, and can bookmark tracks they enjoy.

The system uses a **client–server architecture**:

- **Client:** A web interface (HTML/CSS/JavaScript) where users browse music, create posts, and interact with friends.
- **Server:** A Flask application responsible for authentication, business logic, and database operations.
- **Database:** Stores users, friendships, playlists, tracks, posts, likes, and comments.

---

### 1.2 User Abilities

#### **Account**
- Users can sign up with email/username and password so that I have an account.
- Users can log in and log out securely so that thier data is protected.
- Users can view and edit profiles, including display name, short bio, and profile picture.
- A user account has: username, password, display name, bio, profile picture

#### **Friendship**
- Users can search for other users by username.
- Users can send, accept, and reject friend requests.
- Users can see thier list of friends.
- A friendship has: username1, username2, status

#### **Tracks & Playlists**
- Users can search for a track by name or artist.
- Users can view additional information about a track.
- Users can save a track to my favorites.
- Users can create playlists.
- A track has: title, album, cover art, artist, year
- A playlist has: playlist name, list of tracks

#### **Feed & Posts**
- Users can create a music post and attach a track.
- Users have a home feed that shows recent posts from thier friends, sorted by time.
- Users can click a post to see detailed info about the track and all comments.
- A post has: track, track cover art, caption, likes, comments

#### **Likes & Comments**
- Users can like a music post and see the like count.
- Users can comment on a post.
- Users can see who liked a post.
- A comment has: username, comment

---

## 2. ER Diagram

<img width="861" height="757" alt="image" src="https://github.com/user-attachments/assets/6f5a6282-1a17-4eba-b7f8-f2ba068e4e71" />


---

## 3. Technologies
- Basic HTML/CSS for front end


- Lucid.app for ER Diagram Creation
- MySQL for database
- Python Flask for Data Retrieval
