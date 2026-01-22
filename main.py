import tkinter as tk
from tkinter import ttk, messagebox
from mysql_connector import MySQLConnector
from log_writer import MongoLogger
from formatter import format_movies_table
from config import MYSQL_CONFIG, MONGO_CONFIG


class FilmSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Пошук фільмів 🎬")
        self.root.geometry("1000x700")

        self.mysql_conn = MySQLConnector(**MYSQL_CONFIG)
        self.mysql_conn.connect()
        self.logger = MongoLogger(**MONGO_CONFIG)

        self.current_mode = None
        self.current_params = None
        self.offset = 0
        self.current_results = []

        self.create_main_ui()

    def create_main_ui(self):
        # ─── Вибір режиму ───────────────────────────────────────
        mode_frame = ttk.Frame(self.root)
        mode_frame.pack(fill='x', padx=15, pady=(10, 5))

        self.mode_var = tk.StringVar(value="keyword")

        ttk.Radiobutton(
            mode_frame, text="По ключовому слову", value="keyword",
            variable=self.mode_var, command=self.switch_search_mode
        ).pack(side='left', padx=20)

        ttk.Radiobutton(
            mode_frame, text="По жанру та рокам", value="genre_year",
            variable=self.mode_var, command=self.switch_search_mode
        ).pack(side='left', padx=20)

        ttk.Button(
            mode_frame, text="Топ-5 запитів", command=self.show_top_searches
        ).pack(side='left', padx=20)

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=5)

        # ─── Пошуковий рядок (буде змінюватись) ─────────────────
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.pack(fill='x', padx=15, pady=10)

        # ─── Результати ─────────────────────────────────────────
        results_frame = ttk.Frame(self.root)
        results_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))

        self.tree = ttk.Treeview(results_frame, show='headings')
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill='both', expand=True)

        # початкові колонки (можна міняти пізніше для топу)
        self.set_tree_columns_movies()

        # ─── Кнопка "Завантажити ще" ────────────────────────────
        self.load_more_btn = ttk.Button(
            self.root, text="Показати наступні 10", command=self.load_more
        )
        self.load_more_btn.pack(pady=10)
        self.load_more_btn.pack_forget()

        # одразу показуємо режим за замовчуванням
        self.switch_search_mode()

    def set_tree_columns_movies(self):
        columns = ("title", "year", "genres", "rating")
        self.tree["columns"] = columns
        self.tree.heading("title", text="Назва", anchor='w')
        self.tree.heading("year", text="Рік", anchor='center')
        self.tree.heading("genres", text="Жанри", anchor='w')
        self.tree.heading("rating", text="Рейтинг", anchor='center')

        self.tree.column("title", width=450, anchor='w', stretch=True)
        self.tree.column("year", width=80, anchor='center')
        self.tree.column("genres", width=280, anchor='w')
        self.tree.column("rating", width=100, anchor='center')

    def set_tree_columns_top(self):
        columns = ("pos", "type", "params", "count")
        self.tree["columns"] = columns
        self.tree.heading("pos", text="№", anchor='center')
        self.tree.heading("type", text="Тип", anchor='w')
        self.tree.heading("params", text="Параметри", anchor='w')
        self.tree.heading("count", text="Кількість", anchor='center')

        self.tree.column("pos", width=50, anchor='center')
        self.tree.column("type", width=160, anchor='w')
        self.tree.column("params", width=500, anchor='w')
        self.tree.column("count", width=120, anchor='center')

    def clear_search_frame(self):
        for w in self.search_frame.winfo_children():
            w.destroy()

    def switch_search_mode(self):
        mode = self.mode_var.get()
        self.clear_search_frame()
        self.load_more_btn.pack_forget()
        self.current_mode = mode
        self.current_params = None
        self.offset = 0
        self.current_results = []

        if mode == "keyword":
            ttk.Label(self.search_frame, text="Ключове слово:").pack(side='left', padx=(0, 8))
            self.entry = ttk.Entry(self.search_frame, width=50)
            self.entry.pack(side='left', padx=5, fill='x', expand=True)
            ttk.Button(self.search_frame, text="Шукати", command=self.do_keyword_search).pack(side='left', padx=8)
            self.entry.focus()

        elif mode == "genre_year":
            genres = self.mysql_conn.get_all_genres() or ["-- оберіть --"]

            ttk.Label(self.search_frame, text="Жанр:").pack(side='left', padx=(0, 8))
            self.genre_cb = ttk.Combobox(self.search_frame, values=genres, width=25, state="readonly")
            self.genre_cb.current(0)
            self.genre_cb.pack(side='left', padx=5)

            ttk.Label(self.search_frame, text="Роки від–до:").pack(side='left', padx=(20, 8))
            self.year_from = ttk.Entry(self.search_frame, width=8)
            self.year_from.insert(0, "1990")
            self.year_from.pack(side='left')
            ttk.Label(self.search_frame, text="–").pack(side='left', padx=4)
            self.year_to = ttk.Entry(self.search_frame, width=8)
            self.year_to.insert(0, "2025")
            self.year_to.pack(side='left', padx=5)

            ttk.Button(self.search_frame, text="Шукати", command=self.do_genre_year_search).pack(side='left', padx=12)
            self.genre_cb.focus()

    def do_keyword_search(self):
        keyword = self.entry.get().strip()
        if not keyword:
            messagebox.showwarning("Помилка", "Введіть слово для пошуку")
            return

        self.offset = 0
        self.current_params = keyword
        results = self.mysql_conn.search_by_keyword(keyword, offset=0)
        self.show_movies(results)
        self.logger.log_search("keyword", {"keyword": keyword}, len(results))
        self.offset = 10
        self.current_results = results

    def do_genre_year_search(self):
        genre = self.genre_cb.get().strip()
        if not genre or genre == "-- оберіть --":
            messagebox.showwarning("Помилка", "Оберіть жанр")
            return

        try:
            y_from = int(self.year_from.get() or "1990")
            y_to = int(self.year_to.get() or "2025")
        except ValueError:
            messagebox.showwarning("Помилка", "Роки мають бути числами")
            return

        # обмеження діапазону
        y_from = max(1990, y_from)
        y_to = min(2025, y_to)

        if y_from > y_to:
            y_from, y_to = y_to, y_from

        self.offset = 0
        self.current_params = (genre, y_from, y_to)
        results = self.mysql_conn.search_by_genre_year(genre, y_from, y_to, offset=0)
        self.show_movies(results)
        self.logger.log_search("genre_year", {"genre": genre, "from": y_from, "to": y_to}, len(results))
        self.offset = 10
        self.current_results = results

    def load_more(self):
        if not self.current_mode or not self.current_params:
            return

        if self.current_mode == "keyword":
            new_results = self.mysql_conn.search_by_keyword(self.current_params, offset=self.offset)
        else:
            genre, y_from, y_to = self.current_params
            new_results = self.mysql_conn.search_by_genre_year(genre, y_from, y_to, offset=self.offset)

        if not new_results:
            messagebox.showinfo("Кінець", "Більше немає результатів")
            self.load_more_btn.pack_forget()
            return

        self.current_results.extend(new_results)
        self.show_movies(self.current_results)
        self.logger.log_search(self.current_mode, self.current_params, len(new_results))
        self.offset += 10

    def show_movies(self, results):
        self.set_tree_columns_movies()
        self.tree.delete(*self.tree.get_children())
        self.load_more_btn.pack_forget()

        if not results:
            self.tree.insert("", "end", values=("Нічого не знайдено", "", "", ""))
            return

        for row in results:
            title = row.get('title', '—')
            year = row.get('release_year', '—')
            genres = row.get('genres', row.get('category', '—'))
            rating = row.get('rating', '—')
            if isinstance(genres, (list, tuple)):
                genres = ', '.join(str(g) for g in genres)
            elif isinstance(genres, str):
                genres = genres.replace('|', ', ').replace(';', ', ')

            self.tree.insert("", "end", values=(title, year, genres, str(rating)))

        if len(results) >= 10:
            self.load_more_btn.pack(pady=10)

    def show_top_searches(self):
        self.clear_search_frame()
        self.load_more_btn.pack_forget()
        self.current_mode = None
        self.current_params = None

        top = self.logger.get_top_searches()

        self.set_tree_columns_top()
        self.tree.delete(*self.tree.get_children())

        if not top:
            self.tree.insert("", "end", values=("", "Ще немає запитів", "", ""))
            return

        for i, item in enumerate(top[:5], 1):
            params = item.get('params', {})
            search_type = item.get('search_type', '—')
            results_count = item.get('results_count', 0)

            # Якщо params словник – формуємо красиво, інакше просто рядок
            if isinstance(params, dict):
                if search_type == "keyword":
                    params_str = params.get("keyword", "—")
                elif search_type == "genre_year":
                    params_str = f"{params.get('genre', '—')} ({params.get('from', '—')}–{params.get('to', '—')})"
                else:
                    params_str = str(params)
            elif isinstance(params, list):
                params_str = ', '.join(str(p) for p in params)
            else:
                params_str = str(params)

            self.tree.insert("", "end", values=(
                i,
                search_type,
                params_str,
                results_count
            ))


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add('*Font', 'Helvetica 13')
    style = ttk.Style()
    style.theme_use('clam')
    app = FilmSearchApp(root)
    root.mainloop()
