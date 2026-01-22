def format_movies_table(movies):
    if not movies:
        return "Результатів немає."

    table = f"{'ID':<5} {'Назва':<50} {'Рік':<6} {'Жанр':<15}\n"
    table += "-" * 80 + "\n"

    for m in movies:
        table += f"{m['film_id']:<5} {m['title']:<50} {m['release_year']:<6} {m['genre']:<15}\n"

    return table
