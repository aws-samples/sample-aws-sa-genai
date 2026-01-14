-- Sample Test Queries for MOVIES_SV Semantic View

-- 1. Movies by genre with average ratings
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.genre, MOVIES_DASHBOARD.movie_title
  METRICS AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating
)
ORDER BY avg_rating DESC
LIMIT 10;

-- 2. Top rated movies
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.movie_title, MOVIES_DASHBOARD.movie_release_year
  METRICS AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating, COUNT(MOVIES_DASHBOARD.user_rating) AS rating_count
)
WHERE rating_count > 10
ORDER BY avg_rating DESC
LIMIT 10;

-- 3. User activity by country
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.user_country
  METRICS COUNT(MOVIES_DASHBOARD.user_rating) AS total_ratings, AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating
)
ORDER BY total_ratings DESC;

-- 4. Interaction types analysis
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.interaction_type
  METRICS COUNT(*) AS interaction_count
);

-- 5. Movies by release year
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.movie_release_year
  METRICS COUNT(DISTINCT MOVIES_DASHBOARD.movie_id) AS movie_count, AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating
)
ORDER BY movie_release_year DESC;

-- 6. User engagement by state
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.user_state, MOVIES_DASHBOARD.user_country
  METRICS COUNT(DISTINCT MOVIES_DASHBOARD.user_id) AS unique_users, COUNT(MOVIES_DASHBOARD.user_rating) AS total_ratings
)
ORDER BY unique_users DESC;

-- 7. Genre popularity
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.genre
  METRICS COUNT(DISTINCT MOVIES_DASHBOARD.movie_id) AS movie_count, 
          COUNT(MOVIES_DASHBOARD.user_rating) AS rating_count,
          AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating
)
ORDER BY rating_count DESC;

-- 8. Recent ratings activity
SELECT * FROM SEMANTIC_VIEW (
  MOVIES_SV
  DIMENSIONS MOVIES_DASHBOARD.rating_timestamp, MOVIES_DASHBOARD.movie_title
  METRICS AVG(MOVIES_DASHBOARD.user_rating) AS avg_rating
)
WHERE rating_timestamp >= DATEADD(year, -1, CURRENT_DATE())
ORDER BY rating_timestamp DESC
LIMIT 20;
