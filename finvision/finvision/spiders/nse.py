import scrapy
from scrapy_splash import SplashRequest


class NseSpider(scrapy.Spider):
    name = "nse"
    allowed_domains = ["www.nseindia.com"]

    script = '''
        function main(splash, args)
            splash:set_custom_headers({
                ["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                ["Referer"] = "https://www.nseindia.com/"
            })
            splash.resource_timeout = 120.0
            assert(splash:go(args.url))
            splash:wait(math.random(5, 10))  -- Random delay to simulate browsing
            splash:set_viewport_full()
            return splash:html()
        end
    '''

    def start_requests(self):
        yield SplashRequest(
            url="https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%2050",
            callback=self.parse,
            endpoint="execute",
            args={'lua_source': self.script}
        )

    def parse(self, response):
        # Debug response to ensure correct data rendering
        with open("debug.html", "wb") as f:
            f.write(response.body)

        # Extract table rows excluding the header
        rows = response.xpath("//tr[position() > 1]")
        for row in rows:
            # Extract specific <td> values
            ltp = row.xpath(".//td[contains(@class, 'text-right')][5]/text()").get()
            change = row.xpath(".//td[contains(@class, 'text-right')][8]/text()").get()
            volume = row.xpath(".//td[contains(@class, 'text-right')][9]/text()").get()
            high_52w = row.xpath(".//td[contains(@class, 'text-right')][10]/text()").get()
            low_52w = row.xpath(".//td[contains(@class, 'text-right')][11]/text()").get()

            yield {
                'LTP': ltp,
                'Change': change,
                'Volume': volume,
                '52W High': high_52w,
                '52W Low': low_52w
            }

        # Extract company names and links for further navigation
        companies = response.xpath("//a[@class='symbol-word-break']")
        for company in companies:
            name = company.xpath(".//text()").get()
            link = company.xpath(".//@href").get()

            if link:
                yield SplashRequest(
                    url=response.urljoin(link),
                    callback=self.parse_company_details,
                    endpoint="execute",
                    args={'lua_source': self.script},
                    meta={'name': name}  # Pass the name to the next request
                )

    def parse_company_details(self, response):
        # Get the name from meta
        name = response.meta['name']

        # Extract additional details
        market_cap = response.xpath("//span[@id='orderBookTradeTMC']/text()").get()
        upper_band = response.xpath("//span[@id='upperbandVal']/text()").get()
        lower_band = response.xpath("//span[@id='lowerbandVal']/text()").get()
        pe = response.xpath("(//td[contains(@class,'text-right')])[6]/text()").get()

        yield {
            'name': name,
            'Market Cap': market_cap,
            'Upper Band': upper_band,
            'Lower Band': lower_band,
            'PE': pe,
        }
