from pymongo import MongoClient
from datetime import datetime
import certifi


class MongoLogger:
    def __init__(self, uri, db_name, collection_name):
        """
        Підключення до MongoDB Atlas
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.connect()

    def connect(self):
        """Встановлює підключення до MongoDB"""
        try:
            self.client = MongoClient(
                self.uri,
                tlsCAFile=certifi.where()
            )
            self.collection = self.client[self.db_name][self.collection_name]
            print("Підключення до MongoDB встановлено ✅")
        except Exception as e:
            print(f"Помилка підключення до MongoDB: {e}")

    def log_search(self, search_type, params, results_count):
        """
        Зберігає пошуковий запит у MongoDB
        """
        doc = {
            "timestamp": datetime.utcnow(),
            "search_type": search_type,
            "params": params,
            "results_count": results_count
        }

        try:
            self.collection.insert_one(doc)
        except Exception as e:
            print(f"Помилка при збереженні у MongoDB: {e}")

    def get_top_searches(self, limit=5):
        """
        Повертає топ пошукових запитів по частоті
        """
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "search_type": "$search_type",
                            "params": "$params"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]

            result = list(self.collection.aggregate(pipeline))

            top = []
            for item in result:
                top.append({
                    "search_type": item["_id"]["search_type"],
                    "params": item["_id"]["params"],
                    "results_count": item["count"]
                })

            return top

        except Exception as e:
            print(f"Помилка при отриманні топ-запитів: {e}")
            return []
