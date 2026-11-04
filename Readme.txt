# Film Search App

A desktop application for searching movies from the Sakila database with search query logging in MongoDB.

## Features

- Search movies by keyword
- Search movies by genre and year range
- View Top-5 most popular search queries
- Logging of all user searches into MongoDB

## Tech Stack

- **Python**
- **Tkinter** (GUI)
- **MySQL** (Sakila sample database)
- **MongoDB** (search query logging)

## Project Structure

```text
main.py              # Main application entry point
mysql_connector.py   # MySQL database connection and queries
log_writer.py        # MongoDB logging
formatter.py         # Data formatting helpers
requirements.txt     # Dependencies

How to Run
Clone the repository:
Bashgit clone https://github.com/SirkO95/final_projekt.git
cd final_projekt
Install dependencies:
Bashpip install -r requirements.txt
Make sure MySQL (Sakila) and MongoDB are running.
Start the application:
Bashpython main.py
Author Oleksandr Zakharchuktext
