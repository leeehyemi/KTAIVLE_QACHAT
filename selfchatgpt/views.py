from dotenv import load_dotenv
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import OpenAIEmbeddings
from selfchatgpt.models import chatHistory
import pandas as pd 
from datetime import datetime
from langchain.schema import Document
from django.http import HttpResponse
from django.contrib import messages
from .forms import CSVUploadForm
from .models import faq
from django.utils.dateparse import parse_datetime

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=openai_api_key)
database = Chroma(persist_directory="./database", embedding_function=embeddings)

# get 요청
# Index view
def index(request):
    print(request.session)
    print(request.session.session_key)
    return render(request, 'selfgpt/index1.html')

def start_new_session_view(request):
    if request.method == 'POST':
            try:
                request.session.flush() # 기존 세션 삭제
                session_id = datetime.now().strftime('%Y%m%d%H%M%S%f') # 세션ID
                request.session['session_id'] = session_id
                request.session['chat_history'] = [] # 채팅 기록 초기화
                return JsonResponse({'message': 'New session started', 'session_id' : session_id})
            except Exception as e:
                return JsonResponse({'error': 'Error starting new session'}, status=500)

# post 요청 시 사용자 질문 처리, 응답
def chat(request):
    if request.method == 'POST':
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # post 요청에서 question 필드 가져오기
        query = request.POST.get('question')
        session_id = request.session.get('session_id')
        
        chat_history = request.session.get('chat_history', [])
        
        chat = ChatOpenAI(model="gpt-3.5-turbo")
        
        # 상위 3개의 결과가 반환되도록 설정 
        k = 3
        # chroma 데이터베이스에서 검색 기능을 초기화
        retriever = database.as_retriever(search_kwargs={"k": k})
        
        # 대화 메모리 생성
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", 
                                          return_messages=True)

        # 세션에 따른 메모리 관리
        if len(chat_history) > 10: # 기록이 10개를 초과하면 오래된 기록부터 삭제
            chat_history = chat_history[-10:]
            
        # ConversationalRetrievalQA 체인 생성
        qa = ConversationalRetrievalChain.from_llm(llm=chat, retriever=retriever, memory=memory, 
                                                   return_source_documents=True,  output_key="answer")

        # result = qa(query) # 질문을 체인에 전달
        result = qa({"question": query, "chat_history": chat_history})  # 질문과 대화 기록 전달
         # 답변이 딕셔너리면 result의 키의 값을 가져옴. 아니면 문자열로 변환
        answer = result['answer'] if isinstance(result, dict) and 'answer' in result else str(result)
        
        # 현재 질문과 답변을 채팅 기록에 추가
        chat_history.append({'question': query, 'answer': answer})
        request.session['chat_history'] = chat_history  # 수정된 채팅 기록을 세션에 저장
        
        # chatHistory 모델에 데이터 넣기 
        chatHistory.objects.create(question=query, answer=answer)
        
        # 응답 데이터 : 답변, 날짜
        response_data = {
            'result': answer,
            'datetime' : dt
        }
        
        # 응답 데이터를 json으로 반환
        return JsonResponse(response_data)
    

def upload_csv_for_users(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if check_csv(csv_file):
                messages.success(request, 'CSV 파일이 성공적으로 업로드되었습니다.')
            else:
                messages.error(request, '유효한 CSV 파일이 아닙니다. 올바른 형식의 파일을 업로드하세요.')
        else:
            messages.error(request, '유효하지 않은 입력입니다. 올바른 형식의 파일을 업로드하세요.')
    else:
        form = CSVUploadForm()
    
    return render(request, 'selfgpt/upload_csv.html', {'form': form})

def check_csv(csv_file):
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        required_columns = ['QA']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"필수 열 '{column}'이 누락되었습니다.")
            
        qa_list = df['QA'].dropna().tolist() # 빈 데이터 제거
        
        if len(qa_list) == 0:
            raise ValueError("csv 파일에 유효한 질문 데이터가 없습니다.")
        
        # 대용량 데이터를 분할하여 처리
        batch_size = 1000
        for i in range(0, len(qa_list), batch_size):
            batch = qa_list[i:i+batch_size]
            process_batch(batch)
        
        return True
    except Exception as e:
        print(f"csv 처리 중 오류 발생: {e}")
        return False

def process_batch(batch):
    new_list = []
    for question in batch:    
        score = database.similarity_search_with_score(question, k=1)
        if score and score[0][1] > 0.3:
            new_list.append(Document(page_content=question))
            faq.objects.create(answer=question)
            
    if new_list:
        database.add_documents(new_list)

    
def self_chat_gpt_index_view(request):
    if not request.session.get('session_id'):
        session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')  # 고유한 세션 ID 생성
        request.session['session_id'] = session_id
        request.session['chat_history'] = []
    return render(request, 'selfgpt/index1.html')

def start_new_session_view(request):
    if request.method == 'POST':
        try:
            request.session.flush()
            session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')  # 고유한 세션 ID 생성
            request.session['session_id'] = session_id
            request.session['chat_history'] = []  # Initialize chat history
            return JsonResponse({'message': 'New session started', 'session_id': session_id})
        except Exception as e:
            return JsonResponse({'error': 'Error starting new session'}, status=500)

def self_chat_gpt_response_view(request):
    if request.method == 'POST':
        try:
            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = request.POST.get('question')
            session_id = request.POST.get('session_id')

            # 이전에 저장된 채팅 기록 가져오기
            chat_history = request.session.get('chat_history', [])  

            chat = ChatOpenAI(model="gpt-3.5-turbo")
            retriever = database.as_retriever(search_kwargs={"k": 3})
            memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", return_messages=True)
            qa = ConversationalRetrievalChain.from_llm(llm=chat, retriever=retriever, memory=memory, return_source_documents=True, output_key="answer")

            # 이전 질문과 답변 가져오기
            prev_question = None
            prev_answer = None
            
            if chat_history:
                prev_question = chat_history[-1]['question']
                prev_answer = chat_history[-1]['answer']

            # 이전에 저장된 질문이 있는 경우와 "이전 질문"이 포함된 새로운 질문인 경우를 처리
            if "이전 질문" in query and prev_question:  
                try:
                    prev_answer_value = eval(prev_answer.split(' ')[-1])  
                    additional_value = int(query.split(' ')[-1]) 
                    answer_value = prev_answer_value + additional_value
                    answer = f"이전 답변에 {additional_value}을 더한 값은 {answer_value}입니다."
                except Exception as e:
                    answer = "이전 답변에서 숫자를 추출하는 데 문제가 발생했습니다."
            else:
                result = qa(query)
                answer = result['answer'] if isinstance(result, dict) and 'answer' in result else str(result)

            # 현재 질문과 답변을 채팅 기록에 추가
            chat_history.append({'question': query, 'answer': answer})

            # 수정된 채팅 기록을 세션에 다시 저장
            request.session['chat_history'] = chat_history

            # 질문과 답변을 데이터베이스에 저장
            chatHistory.objects.create(question=query, answer=answer)

            response_data = {
                'result': answer,
                'datetime': dt
            }

            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'error': '채팅 응답 처리 중 오류가 발생했습니다.'}, status=500)

def faq_list(request): # 추가 
    faqs = faq.objects.all()
    return render(request, 'selfgpt/faq_list.html', {'faqs':faqs} )

def history_list(request): # 추가
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        start_date = parse_datetime(start_date)
        end_date = parse_datetime(end_date)
        history = chatHistory.objects.filter(datetime__range=(start_date, end_date))
    else:
        history = chatHistory.objects.all()

    return render(request, 'selfgpt/history_list.html', {'history': history})
