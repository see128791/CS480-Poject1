DROP DATABASE IF EXISTS spotsocialdb;
CREATE DATABASE spotsocialdb;
USE spotsocialdb;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255),
    display_name VARCHAR(255),
    bio VARCHAR(255),
    profile_picture VARCHAR(255)
);

CREATE TABLE friendships (
    friendship_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id_1 INT,
    user_id_2 INT,
    FOREIGN KEY (user_id_1) references users(user_id),
    FOREIGN KEY (user_id_2) references users(user_id)
);

CREATE TABLE tracks (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    album VARCHAR(255),
    cover_image VARCHAR(255),
    artist VARCHAR(255)
);

CREATE TABLE playlists (
    playlist_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    description VARCHAR(255),
    cover_image VARCHAR(255),
    is_favorites BOOLEAN
);

CREATE TABLE playlist_contents (
    playlist_id INT,
    track_id INT,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) references playlists(playlist_id),
    FOREIGN KEY (track_id) references tracks(track_id)
);

CREATE TABLE posts (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    track_id INT,
    caption VARCHAR(255),
    time DATETIME,
    FOREIGN KEY (user_id) references users(user_id),
    FOREIGN KEY (track_id) references tracks(track_id)
);

CREATE TABLE likes (
    like_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT,
    user_id INT,
    FOREIGN KEY (user_id) references users(user_id),
    FOREIGN KEY (post_id) references posts(post_id)
);

CREATE TABLE comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT,
    user_id INT,
    comment VARCHAR(255),
    FOREIGN KEY (post_id) references posts(post_id),
    FOREIGN KEY (user_id) references users(user_id)
);
