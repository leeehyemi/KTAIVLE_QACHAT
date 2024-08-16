from selfchatgpt.models import faq

def save_faq(dlist):
    for item in dlist:
        faq.objects.create(answer=item)