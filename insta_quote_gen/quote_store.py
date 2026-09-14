import json
from pathlib import Path


class QuoteStore:
    def __init__(self, quotes_file, index_file):
        self.quotes_file = Path(quotes_file)
        self.index_file = Path(index_file)

    def read(self):
        if not self.quotes_file.exists():
            return {"quotes": []}
        with self.quotes_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return {"quotes": data.get("quotes", [])}

    def append_unique(self, quotes):
        data = self.read()
        existing_texts = {quote["text"] for quote in data["quotes"]}
        unique_quotes = [
            quote for quote in quotes if quote["text"] not in existing_texts
        ]
        if unique_quotes:
            data["quotes"].extend(unique_quotes)
            self.quotes_file.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        return len(unique_quotes)

    def next(self):
        quotes = self.read()["quotes"]
        if not quotes:
            raise ValueError("No quotes available")

        current_index = 0
        if self.index_file.exists():
            current_index = int(self.index_file.read_text(encoding="utf-8").strip())

        quote = quotes[current_index % len(quotes)]
        next_index = (current_index + 1) % len(quotes)
        self.index_file.write_text(str(next_index), encoding="utf-8")
        return quote