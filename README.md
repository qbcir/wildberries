#### Setup:
1. Install docker: https://docs.docker.com/install/
2. Install python requirements:
```
pip3 install -r requirements.txt
```

#### Running:
1. Launch splash
```
docker run -p 8050:8050 scrapinghub/splash
```
2. Start parser:
```
scrapy crawl shoes_spider -o result.json -t jsonlines
```
3. Results json will contain results
