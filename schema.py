from graphene import ObjectType, String, List


class ArticleSchema(ObjectType):
    hostname = String()
    article_html = String()
    title = String()
    text = String()
    summary = String()
    tags = List(String)
    top_image = String()
    authors = List(String)
    keywords = List(String)
