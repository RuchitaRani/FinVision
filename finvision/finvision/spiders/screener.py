import scrapy
from scrapy.shell import inspect_response

class ScreenerSpider(scrapy.Spider):
    name = "screener"
    allowed_domains = ["www.screener.in"]
    start_urls = ["https://www.screener.in/company/NIFTY/"]

    def parse(self, response):
        name = response.xpath("//td/a/text()").getall()
        eps = response.xpath("//td[a]/following-sibling::td[4]/text()").getall()

        yield{
            'name': name,
            'eps' : eps
        }

