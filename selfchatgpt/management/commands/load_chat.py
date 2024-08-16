from django.core.management.base import BaseCommand
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from selfchatgpt.scripts.save_faq import save_faq

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        database = Chroma(persist_directory="./database", embedding_function=embeddings)
        dlist = database.get()['documents']
        save_faq(dlist)
        self.stdout.write(self.style.SUCCESS('데이터베이스 저장 성공'))