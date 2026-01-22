import pymysql
from pymysql.cursors import DictCursor


class MySQLConnector:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor
            )
            print("Підключення до MySQL встановлено ✅")
        except pymysql.MySQLError as e:
            print(f"Помилка підключення до MySQL: {e}")

    def close(self):
        if self.connection:
            self.connection.close()

    # ───────────────────────────────────────────────
    # ЖАНРИ
    # ───────────────────────────────────────────────
    def get_all_genres(self):
        query = """
        SELECT name
        FROM category
        ORDER BY name
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
            return [row["name"] for row in result]
        except pymysql.MySQLError as e:
            print(f"Помилка жанрів: {e}")
            return []

    # ───────────────────────────────────────────────
    # ПОШУК ПО КЛЮЧОВОМУ СЛОВУ
    # ───────────────────────────────────────────────
    def search_by_keyword(self, keyword, limit=10, offset=0):
        query = """
        SELECT
            f.film_id,
            f.title,
            f.release_year,
            f.rating,
            GROUP_CONCAT(c.name SEPARATOR ', ') AS genres
        FROM film f
        LEFT JOIN film_category fc ON f.film_id = fc.film_id
        LEFT JOIN category c ON fc.category_id = c.category_id
        WHERE f.title LIKE %s
        GROUP BY f.film_id
        ORDER BY f.title
        LIMIT %s OFFSET %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (f"%{keyword}%", limit, offset))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Помилка пошуку по слову: {e}")
            return []

    # ───────────────────────────────────────────────
    # ПОШУК ПО ЖАНРУ ТА РОКАХ
    # ───────────────────────────────────────────────
    def search_by_genre_year(self, genre, year_from, year_to, limit=10, offset=0):
        query = """
        SELECT
            f.film_id,
            f.title,
            f.release_year,
            f.rating,
            GROUP_CONCAT(c.name SEPARATOR ', ') AS genres
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE c.name = %s
          AND f.release_year BETWEEN %s AND %s
        GROUP BY f.film_id
        ORDER BY f.release_year DESC
        LIMIT %s OFFSET %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (genre, year_from, year_to, limit, offset))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Помилка пошуку по жанру/роках: {e}")
            return []
    # ───────────────────────────────────────────────
    # ДІАПАЗОН РОКІВ
    # ───────────────────────────────────────────────
    def get_year_range(self):
        query = """
        SELECT
            MIN(release_year) AS min_year,
            MAX(release_year) AS max_year
        FROM film
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Помилка отримання діапазону років: {e}")
            return {"min_year": None, "max_year": None}
