from urllib.parse import urlparse
import json

from starlette.applications import Starlette
from starlette.middleware.gzip import GZipMiddleware
from starlette.graphql import GraphQLApp
from starlette.config import Config

from newspaper import Article
import uvicorn
import redis
import graphene


config = Config('.env')
app = Starlette()


REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379')
PORT = config('PORT', cast=int, default=8000)
DEBUG = config('DEBUG', cast=bool, default=False)

redis_url = urlparse(REDIS_URL)
R = redis.Redis(
    host=redis_url.hostname,
    port=redis_url.port,
    password=redis_url.password,
    db=0
)


class ArticleSchema(graphene.ObjectType):
    hostname = graphene.String()
    article_html = graphene.String()
    title = graphene.String()
    text = graphene.String()
    summary = graphene.String()
    tags = graphene.List(graphene.String)
    top_image = graphene.String()
    authors = graphene.List(graphene.String)
    keywords = graphene.List(graphene.String)


def download_and_parse_article(url):
    data = None
    if R.get(url):
        data = R.get(url)
        return ArticleSchema(**json.loads(data))
    else:
        parsed_url = urlparse(url)
        article = Article(url, keep_article_html=True)
        article.download()
        article.parse()
        encodable = {
            'hostname': parsed_url.hostname,
            'article_html': article.article_html,
            'title': article.title,
            'text': article.text,
            'summary': article.summary,
            'tags': list(article.tags),
            'top_image': article.top_image,
            'authors': article.authors,
            'keywords': article.keywords
        }
        data = json.dumps(encodable)
        R.set(url, data)
        return ArticleSchema(**encodable)


class Query(graphene.ObjectType):
    article = graphene.Field(ArticleSchema, url=graphene.String(required=True))
    articles = graphene.List(ArticleSchema, urls=graphene.List(graphene.String))

    def resolve_article(self, info, url):
        return download_and_parse_article(url)

    def resolve_articles(self, info, urls):
        results = []
        for url in urls:
            try:
                result = download_and_parse_article(url)
                results.append(result)
            except Exception:
                pass

        return results


schema = graphene.Schema(query=Query)


@app.middleware('http')
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'max-age=6000'
    return response

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_route('/graphql', GraphQLApp(schema=graphene.Schema(query=Query)))

app.debug = DEBUG

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
