import math
import re
import scrapy
from urllib.parse import urljoin
from scrapy import Request
import json
from scrapy.shell import inspect_response

from scrapy_splash import SplashRequest

_ARTICLE_URL_RE = re.compile("/catalog/(\d+)/detail")
_DOM_INIT_JS_RE = re.compile("data: (\{[^\n]+)")


class ShoeProduct(scrapy.Item):
    item_idx = scrapy.Field()
    cat_name = scrapy.Field()
    #
    article = scrapy.Field()
    color = scrapy.Field()
    #
    old_price = scrapy.Field()
    new_price = scrapy.Field()
    #
    order_count = scrapy.Field()
    #
    brend_name = scrapy.Field()
    good_name = scrapy.Field()
    composition = scrapy.Field()
    description = scrapy.Field()
    #
    big_sale = scrapy.Field()
    #
    param_shoe_width_eur = scrapy.Field()
    param_insole_material = scrapy.Field()
    param_sole_material = scrapy.Field()
    param_lining_material = scrapy.Field()
    param_closing_types = scrapy.Field()
    param_sole_height = scrapy.Field()
    param_heel_height = scrapy.Field()
    param_gender = scrapy.Field()
    param_season = scrapy.Field()
    param_brend_country = scrapy.Field()
    param_manufacturer_country = scrapy.Field()
    #
    size_too_small_percentage = scrapy.Field()
    size_ok_percentage = scrapy.Field()
    size_too_big_percentage = scrapy.Field()
    #
    rating = scrapy.Field()
    rate_5_percentage = scrapy.Field()
    rate_4_percentage = scrapy.Field()
    rate_3_percentage = scrapy.Field()
    rate_2_percentage = scrapy.Field()
    rate_1_percentage = scrapy.Field()
    #
    related_goods = scrapy.Field()
    similar_goods = scrapy.Field()
    #
    bought_along_with = scrapy.Field()
    #
    search_tags = scrapy.Field()
    #
    data = scrapy.Field()


_PARAM_NAME_TO_FIELD = {
    'Полнота обуви (EUR)': 'param_shoe_width_eur',
    'Материал стельки': 'param_insole_material',
    'Материал подошвы обуви': 'param_sole_material',
    'Материал подкладки обуви': 'param_lining_material',
    'Вид застежки': 'param_closing_types',
    'Высота подошвы': 'param_sole_height',
    'Высота каблука': 'param_heel_height',
    'Пол': 'param_gender',
    'Сезон': 'param_season',
    'Страна бренда': 'param_brend_country',
    'Страна производитель': 'param_manufacturer_country'
}


class ShoesSpider(scrapy.Spider):

    _BASE_URL = 'https://www.wildberries.ru'

    name = 'shoes_spider'
    start_urls = [
        _BASE_URL + '/catalog/obuv/zhenskaya',
        _BASE_URL + '/catalog/obuv/muzhskaya'
    ]

    download_delay = 0.5

    def parse(self, response):
        categories = response.xpath("//ul[@class='sidemenu']/li[contains(@class, 'selected')]/ul/li/a/@href").extract()
        for cat_href in categories:
            cat_name = cat_href.split('/')[-1]
            yield Request(urljoin(self._BASE_URL, cat_href),
                          callback=lambda resp: self.parse_category(resp, cat_name))

    def parse_category(self, response, cat_name):
        total_items = int(response.xpath("//span[@class='total many']/span/text()").extract()[0])
        npages = math.ceil(total_items / 200)
        for i in range(0, npages):
            page_idx = i + 1
            yield Request(urljoin(self._BASE_URL, response.url) + "?page=%d&pagesize=200" % page_idx,
                          callback=lambda resp: self.parse_items_page(resp, page_idx, cat_name))

    def parse_items_page(self, response, page_idx, cat_name):
        item_ids = response.xpath("//div[@class='l_class']/@id").extract()
        for item_page_idx, item_id in enumerate(item_ids):
            item_id = item_id.lstrip('c')
            item_idx = (page_idx-1) * 200 + item_page_idx
            #yield Request(urljoin(self._BASE_URL, "/catalog/%s/detail.aspx" % item_id),
            #              callback=lambda resp: self.parse_item(resp, item_idx, cat_name))
            yield SplashRequest(urljoin(self._BASE_URL, "/catalog/%s/detail.aspx" % item_id),
                                callback=lambda resp: self.parse_item(resp, item_id, item_idx, cat_name),
                                endpoint='render.html',
                                args={'timeout': 90, 'wait': 0.5})

    def parse_item(self, response, item_id, item_idx, cat_name):
        p = ShoeProduct()
        #
        p['item_idx'] = item_idx
        p['cat_name'] = cat_name
        #
        article_tmp = response.xpath("//span[@class='j-article']/text()").extract()
        if not article_tmp:
            yield SplashRequest(urljoin(self._BASE_URL, "/catalog/%s/detail.aspx" % item_id),
                                callback=lambda resp: self.parse_item(resp, item_id, item_idx, cat_name),
                                endpoint='render.html',
                                args={'wait': 5.0})
        else:
            p['article'] = article_tmp[0]
            color_tmp = response.xpath("//span[@class='color j-color-name']/text()").extract()
            if color_tmp:
                p['color'] = color_tmp[0]
            #
            old_price_tmp = response.xpath("//span[@class='price-popup old-price']/del/text()").extract()
            if old_price_tmp:
                p['old_price'] = old_price_tmp[0].replace('\xa0', '')
            new_price_tmp = response.xpath("//span[@class='add-discount-text-price j-final-saving']/text()").extract()
            if new_price_tmp:
                p['new_price'] = new_price_tmp[0].replace('\xa0', '')
            #
            order_count_tmp = response.xpath("//span[@class='j-orders-count']/text()").extract()
            if order_count_tmp:
                p['order_count'] = order_count_tmp[0].replace('\xa0', '')
            #
            big_sale_img_tmp = response.xpath(
                "//div[@class='j-big-sale-icon-card-wrapper spec-actions i-spec-action']/img/@src").extract()
            if big_sale_img_tmp:
                p['big_sale'] = big_sale_img_tmp[0]
            #
            brend_name_tmp = response.xpath("//span[@class='h2-brend-name']/text()").extract()
            if brend_name_tmp:
                p['brend_name'] = brend_name_tmp[0]
            good_name_tmp = response.xpath("//span[@class='h2-good-name']/text()").extract()
            if good_name_tmp:
                p['good_name'] = good_name_tmp[0].strip('/ ')
            p['composition'] = ';'.join(response.xpath("//p[@class='composition']/span/text()").extract()[1:])
            description_tmp = response.xpath("//div[@class='j-description description-text']/p/text()").extract()
            if description_tmp:
                p['description'] = description_tmp[0]
            #
            param_names = response.xpath("//div[@class='params']/div[@class='pp']/span/b/text()").extract()
            param_values = response.xpath("//div[@class='params']/div[@class='pp']/span/text()").extract()
            for param_name, param_value in zip(param_names, param_values):
                if param_name in _PARAM_NAME_TO_FIELD:
                    p[_PARAM_NAME_TO_FIELD[param_name]] = param_value.strip()
            #
            related_goods_links = response.xpath(
                "//div[@class='standart-carousel-wrapper related-goods']//a[@class='standart-carousel-item']/@href")\
                .extract()
            p['related_goods'] = [_ARTICLE_URL_RE.search(l).group(1) for l in related_goods_links]
            #
            similar_goods_links = response.xpath(
                "//div[@data-another-goods-location='1']//a[@class='standart-carousel-item']/@href").extract()
            p['similar_goods'] = [_ARTICLE_URL_RE.search(l).group(1) for l in similar_goods_links]
            #
            bought_along_with_links = response.xpath(
                "//div[@data-another-goods-location='2']//a[@class='standart-carousel-item']/@href").extract()
            p['bought_along_with'] = [_ARTICLE_URL_RE.search(l).group(1) for l in bought_along_with_links]
            #
            p['search_tags'] = response.xpath("//li[@class='tags-group-item']/a/text()").extract()
            #
            size_percentages = response.xpath("//div[@class='circlechart']/@data-percentage").extract()
            if size_percentages:
                p['size_too_small_percentage'] = size_percentages[0]
                p['size_ok_percentage'] = size_percentages[1]
                p['size_too_big_percentage'] = size_percentages[2]
            #
            rating_tmp = response.xpath("//div[@class='result-value']/text()").extract()
            if rating_tmp:
                p['rating'] = rating_tmp[0]
            rate_percentages = response.xpath("//div[@class='line-value']/text()").extract()
            if rate_percentages:
                p['rate_5_percentage'] = rate_percentages[0]
                p['rate_4_percentage'] = rate_percentages[1]
                p['rate_3_percentage'] = rate_percentages[2]
                p['rate_2_percentage'] = rate_percentages[3]
                p['rate_1_percentage'] = rate_percentages[4]
            #
            dom_init_js = response.xpath("//script[contains(text(), 'DomReady')]/text()").extract()
            if dom_init_js:
                re_match = _DOM_INIT_JS_RE.search(dom_init_js[0])
                p['data'] = json.loads(re_match.group(1).rstrip(','))
            yield p
