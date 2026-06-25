import json
from scrapy.crawler import CrawlerProcess
import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes_spider"
    start_urls = ["http://quotes.toscrape.com"]
    
    # Списки для акумуляції результатів під час роботи краулера
    quotes_data = []
    authors_data = []
    seen_authors = set()  # Множина для уникнення дублікатів авторів

    def parse(self, response):
        # Збір цитат на поточній сторінці
        for quote_block in response.css("div.quote"):
            tags = quote_block.css("div.tags a.tag::text").getall()
            author = quote_block.css("small.author::text").get().strip()
            quote_text = quote_block.css("span.text::text").get().strip()

            self.quotes_data.append({
                "tags": tags,
                "author": author,
                "quote": quote_text
            })

            # Перехід на сторінку автора (about), якщо ми його ще не парсили
            author_url = quote_block.css("span a::attr(href)").get()
            if author_url and author not in self.seen_authors:
                self.seen_authors.add(author)
                yield response.follow(author_url, callback=self.parse_author)

        # Перехід на наступну сторінку цитат (пагінація)
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_author(self, response):
        # Збір детальної інформації про автора у внутрішній сторінці
        fullname = response.css("h3.author-title::text").get().strip()
        born_date = response.css("span.author-born-date::text").get().strip()
        born_location = response.css("span.author-born-location::text").get().strip()
        description = response.css("div.author-description::text").get().strip()

        self.authors_data.append({
            "fullname": fullname,
            "born_date": born_date,
            "born_location": born_location,
            "description": description
        })


if __name__ == "__main__":
    print("Старт скрапінгу сайту ://toscrape.com...")
    
    # Ініціалізація та налаштування Scrapy процесу
    process = CrawlerProcess(settings={
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "LOG_LEVEL": "INFO"  # Показуватиме загальний прогрес без зайвого спаму в консоль
    })
    
    process.crawl(QuotesSpider)
    process.start()  # Блокуючий виклик: скрипт чекає завершення збору даних

    print("\nЗбір даних завершено. Збереження у JSON файли...")
    
    # Збереження цитат із чітким дотриманням UTF-8 (для збереження символів на кшталт "“", "”" тощо)
    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(QuotesSpider.quotes_data, f, ensure_ascii=False, indent=4)
        
    # Збереження авторів
    with open("authors.json", "w", encoding="utf-8") as f:
        json.dump(QuotesSpider.authors_data, f, ensure_ascii=False, indent=4)
        
    print("Файли quotes.json та authors.json успішно згенеровано у поточній папці!")
