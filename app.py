from urllib.parse import urlparse
import json

from starlette.applications import Starlette
from starlette.graphql import GraphQLApp, GraphQLError
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from newspaper import Article
import uvicorn
import graphene

from settings import DEBUG, PORT
from cache import cache
from schema import ArticleSchema


app = Starlette()


def download_and_parse_article(url):
    article = Article(url, keep_article_html=True)
    article.download()
    article.parse()
    return article


def get_article(url):
    data = None
    if cache.get(url):
        data = cache.get(url)
        return json.loads(data)
    else:
        parsed_url = urlparse(url)
        article = download_and_parse_article(url)
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
        cache.set(url, data)
        return encodable


class Query(graphene.ObjectType):
    article = graphene.Field(ArticleSchema, url=graphene.String(required=True))
    articles = graphene.List(ArticleSchema, urls=graphene.List(graphene.String))

    def resolve_article(self, info, url):
        result = get_article(url)
        return ArticleSchema(**result)

    def resolve_articles(self, info, urls):
        results = []
        for url in urls:
            try:
                result = get_article(url)
                results.append(ArticleSchema(**result))
            except Exception:
                # results.append(
                    # GraphQLError('Failed to parse url {}'.format(url)))
                pass

        return results


schema = graphene.Schema(query=Query)


@app.middleware('http')
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'max-age=6000'
    print(response)  # Might be able to strip null values here
    return response

app.add_middleware(GZipMiddleware, minimum_size=1000)
app = Starlette(debug=True, template_directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')


@app.route('/')
async def homepage(request):
    template = app.get_template('index.html')
    content = template.render(request=request)
    return HTMLResponse(content)

app.add_route('/graphql', GraphQLApp(schema=schema))

app.debug = DEBUG

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
