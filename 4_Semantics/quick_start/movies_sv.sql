-- Create Semantic View from YAML definition
CREATE OR REPLACE SEMANTIC VIEW MOVIES_SV
COMMENT = 'this is the semantic view for our movies'

TABLES (
  MOVIES_DASHBOARD AS MOVIES.PUBLIC.MOVIES_DASHBOARD
    PRIMARY KEY (MOVIE_ID)
    COMMENT = 'This table stores information about movies, user ratings, and user interactions with the movies. It captures movie details such as title, release year, and genre, as well as user information including name, location, and contact details. The table also tracks user ratings and interactions with the movies, including the timestamp of the interaction and the type of interaction.'
)

DIMENSIONS (
  MOVIES_DASHBOARD.genre AS MOVIES_DASHBOARD.GENRE
    COMMENT = 'The type of movie genre, such as action, comedy, drama, etc., that categorizes the movie''s style, tone, and content.',
  
  MOVIES_DASHBOARD.interaction_timestamp AS MOVIES_DASHBOARD.INTERACTION_TIMESTAMP
    COMMENT = 'The timestamp when a user interacted with the movie, representing the number of seconds that have elapsed since January 1, 1970, at 00:00:00 UTC.',
  
  MOVIES_DASHBOARD.interaction_type AS MOVIES_DASHBOARD.INTERACTION_TYPE
    COMMENT = 'The type of interaction a user had with a movie, either clicking on it or watching it.',
  
  MOVIES_DASHBOARD.movie_id AS MOVIES_DASHBOARD.MOVIE_ID
    COMMENT = 'Unique identifier for each movie in the database.',
  
  MOVIES_DASHBOARD.movie_release_year AS MOVIES_DASHBOARD.MOVIE_RELEASE_YEAR
    COMMENT = 'The year in which the movie was released.',
  
  MOVIES_DASHBOARD.movie_title AS MOVIES_DASHBOARD.MOVIE_TITLE
    COMMENT = 'The title of the movie.',
  
  MOVIES_DASHBOARD.user_city AS MOVIES_DASHBOARD.USER_CITY
    COMMENT = 'The city where the user is located.',
  
  MOVIES_DASHBOARD.user_country AS MOVIES_DASHBOARD.USER_COUNTRY
    COMMENT = 'The country where the user is located.',
  
  MOVIES_DASHBOARD.user_email AS MOVIES_DASHBOARD.USER_EMAIL
    COMMENT = 'The email address of the user who interacted with the movie content.',
  
  MOVIES_DASHBOARD.user_firstname AS MOVIES_DASHBOARD.USER_FIRSTNAME
    COMMENT = 'The first name of the user who interacted with the movie.',
  
  MOVIES_DASHBOARD.user_id AS MOVIES_DASHBOARD.USER_ID
    COMMENT = 'Unique identifier for the user who interacted with the movie.',
  
  MOVIES_DASHBOARD.user_lastname AS MOVIES_DASHBOARD.USER_LASTNAME
    COMMENT = 'The last name of the user who interacted with the movie.',
  
  MOVIES_DASHBOARD.user_phonenumber AS MOVIES_DASHBOARD.USER_PHONENUMBER
    COMMENT = 'The phone number of the user who interacted with the movie content.',
  
  MOVIES_DASHBOARD.user_state AS MOVIES_DASHBOARD.USER_STATE
    COMMENT = 'The state in which the user is located.',
  
  MOVIES_DASHBOARD.rating_timestamp AS MOVIES_DASHBOARD.RATING_TIMESTAMP
    COMMENT = 'The date and time when a movie rating was recorded.'
)

FACTS (
  MOVIES_DASHBOARD.user_rating AS MOVIES_DASHBOARD.USER_RATING
    COMMENT = 'Average rating given by users to a movie, on a scale of 1 to 5.'
);
