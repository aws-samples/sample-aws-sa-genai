# Field Descriptions

## Movie Fields

- **GENRE**: The type of movie genre, such as action, comedy, drama, etc., that categorizes the movie's style, tone, and content.
- **MOVIE_ID**: Unique identifier for each movie in the database.
- **MOVIE_RELEASE_YEAR**: The year in which the movie was released.
- **MOVIE_TITLE**: The title of the movie.

## User Fields

- **USER_ID**: Unique identifier for the user who interacted with the movie.
- **USER_FIRSTNAME**: The first name of the user who interacted with the movie.
- **USER_LASTNAME**: The last name of the user who interacted with the movie.
- **USER_EMAIL**: The email address of the user who interacted with the movie content.
- **USER_PHONENUMBER**: The phone number of the user who interacted with the movie content.
- **USER_CITY**: The city where the user is located.
- **USER_STATE**: The state in which the user is located.
- **USER_COUNTRY**: The country where the user is located.

## Interaction Fields

- **INTERACTION_TIMESTAMP**: The timestamp when a user interacted with the movie, representing the number of seconds that have elapsed since January 1, 1970, at 00:00:00 UTC.
- **INTERACTION_TYPE**: The type of interaction a user had with a movie, either clicking on it or watching it.

## Rating Fields

- **RATING_TIMESTAMP**: The date and time when a movie rating was recorded.
- **USER_RATING**: Average rating given by users to a movie, on a scale of 1 to 5.

---

**Note**: QuickSight API doesn't directly support setting field descriptions via `create_data_set`. Field descriptions are typically set through the QuickSight UI or by using calculated fields. This structure provides the foundation for the dataset.
