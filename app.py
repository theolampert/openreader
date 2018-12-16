from urllib.parse import urlparse

from newspaper import Article
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.config import environ
from starlette.middleware.gzip import GZipMiddleware
from starlette.graphql import GraphQLApp
from starlette.config import Config
import graphene

import uvicorn


config = Config('.env')
app = Starlette()

PORT = config('PORT', cast=int, default=8000)
DEBUG = config('DEBUG', cast=bool, default=False)


def download_and_parse_article(url):
    article = Article(url, preserve_html=True)
    article.download()
    article.parse()
    article.nlp()
    return article


class ArticleSchema(graphene.ObjectType):
    hostname = graphene.String()
    title = graphene.String()
    text = graphene.String()
    summary = graphene.String()
    tags = graphene.List(graphene.String)
    top_image = graphene.String()
    authors = graphene.List(graphene.String)
    keywords = graphene.List(graphene.String)


class Query(graphene.ObjectType):
    article = graphene.Field(ArticleSchema, url=graphene.String(required=True))
    articles = graphene.List(ArticleSchema, urls=graphene.List(graphene.String))

    def resolve_article(self, info, url):
        result = download_and_parse_article(url)
        return ArticleSchema(
            hostname=urlparse(url).hostname,
            title=result.title,
            text=result.text,
            summary=result.summary,
            tags=list(result.tags),
            top_image=result.top_image,
            authors=result.authors,
            keywords=result.keywords
        )

    def resolve_articles(self, info, urls):
        results = []
        for url in urls:
            result = download_and_parse_article(url)
            results.append(ArticleSchema(
                hostname=urlparse(url).hostname,
                title=result.title,
                text=result.text,
                summary=result.summary,
                tags=list(result.tags),
                top_image=result.top_image,
                authors=result.authors,
                keywords=result.keywords
            ))
        return results


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
