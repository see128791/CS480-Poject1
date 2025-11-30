CREATE DATABASE SpotSocialDB;

USE SpotSocialDB;

-- 1. Users Table (Account)
CREATE TABLE Users (
    User_ID INT PRIMARY KEY,
    Username VARCHAR(255) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Display_Name VARCHAR(255),
    Bio VARCHAR(500),
    Profile_Picture VARCHAR(255)
);

-- 2. Tracks Table (Music Data) 
CREATE TABLE Tracks (
    Track_ID INT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Album VARCHAR(255),
    Cover_Image VARCHAR(255),
    Artist VARCHAR(255),
    Year INT -- Added based on requirements
);

-- 3. Playlists Table (Music Data)
CREATE TABLE Playlists (
    Playlist_ID INT PRIMARY KEY,
    User_ID INT NOT NULL, -- Assumes playlists belong to a user
    Name VARCHAR(255) NOT NULL,
    Description VARCHAR(500),
    Cover_Image VARCHAR(255),
    Is_Favorites BOOLEAN, -- Flag to identify a user's 'favorites' list
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);

-- 4. Playlist_Contents Table (Junction for Playlists and Tracks)
CREATE TABLE Playlist_Contents (
    Playlist_ID INT,
    Track_ID INT,
    PRIMARY KEY (Playlist_ID, Track_ID),
    FOREIGN KEY (Playlist_ID) REFERENCES Playlists(Playlist_ID),
    FOREIGN KEY (Track_ID) REFERENCES Tracks(Track_ID)
);

-- 5. Friendships Table (Friend Requests and Connections)
CREATE TABLE Friendships (
    Friendship_ID INT PRIMARY KEY,
    User_ID_1 INT NOT NULL,
    User_ID_2 INT NOT NULL,
    Status VARCHAR(50), -- e.g., 'Pending', 'Accepted', 'Rejected'
    FOREIGN KEY (User_ID_1) REFERENCES Users(User_ID),
    FOREIGN KEY (User_ID_2) REFERENCES Users(User_ID),
    -- Constraint to prevent self-friend requests
    CONSTRAINT CHK_DifferentUsers CHECK (User_ID_1 <> User_ID_2)
);

-- 6. Posts Table (Feed Content)
CREATE TABLE Posts (
    Post_ID INT PRIMARY KEY,
    User_ID INT NOT NULL, -- Who created the post
    Track_ID INT NOT NULL, -- Which track is attached
    Caption VARCHAR(500),
    Time DATETIME NOT NULL, -- Used for sorting the feed
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID),
    FOREIGN KEY (Track_ID) REFERENCES Tracks(Track_ID)
);

-- 7. Likes Table (Tracking Post Likes)
CREATE TABLE Likes (
    Like_ID INT PRIMARY KEY,
    Post_ID INT NOT NULL,
    User_ID INT NOT NULL,
    FOREIGN KEY (Post_ID) REFERENCES Posts(Post_ID),
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID),
    UNIQUE (Post_ID, User_ID)
);

-- 8. Comments Table (Post Comments)
CREATE TABLE Comments (
    Comment_ID INT PRIMARY KEY,
    Post_ID INT NOT NULL,
    User_ID INT NOT NULL,
    Comment VARCHAR(500) NOT NULL,
    FOREIGN KEY (Post_ID) REFERENCES Posts(Post_ID),
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);