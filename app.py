from flask import Flask, request, jsonify
import google.generativeai as genai
import asyncio
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import random
import string
import os
import logging
import json

# Настройка Google Gemini API
genai.configure(api_key='AIzaSyBxoiv6GT1CKCZ9cq-iRDKyb8Y55imzTwE')
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql+pymysql://root:123123@192.168.1.245/db_name')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

CORS(
    app,
    origins=["http://localhost:3000", "http://192.168.1.249:3000"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

logging.basicConfig(level=logging.INFO)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')  # Динамический Origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Test(db.Model):
    __tablename__ = 'Test'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.String(150), nullable=False)

class Question(db.Model):
    __tablename__ = 'Question'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('Test.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'test' или 'text'
    options = db.Column(db.JSON)  # для хранения вариантов ответов

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'message': 'Електронна пошта вже використовується'}), 400
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Реєстрація успішна!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Успішний вхід!'}), 200
    return jsonify({'message': 'Неправильні облікові дані'}), 401

@app.route('/test-log', methods=['GET'])
def test_log():
    logging.info("Hello from /test-log route")
    return jsonify({"message": "Test log route works"})

@app.route('/create-test', methods=['POST'])
def create_test():
    data = request.get_json()
    print('Received data:', data)
    print('Type of data["subject"]:', type(data.get('subject')))  # Debug log

    if not data or 'title' not in data or 'questions' not in data or 'subject' not in data:
        return jsonify({'message': 'Неправильні дані'}), 400

    if not isinstance(data['subject'], str):
        return jsonify({'msg': 'Subject must be a string', 'received_subject': data['subject']}), 422

    # Генеруємо унікальний код для тесту
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    new_test = Test(code=code, title=data['title'], subject=data['subject'], created_by="anonymous")
    db.session.add(new_test)
    db.session.commit()

    for question in data['questions']:
        if 'question_text' not in question or 'answer' not in question:
            return jsonify({'message': 'Неправильні дані питання'}), 400
        new_question = Question(test_id=new_test.id, question_text=question['question_text'], answer=question['answer'])
        db.session.add(new_question)
    db.session.commit()

    return jsonify({'message': 'Тест створено успішно!', 'code': code}), 201

@app.route('/get-test/<code>', methods=['GET'])
def get_test(code):
    test = Test.query.filter_by(code=code).first()
    if not test:
        return jsonify({'message': 'Тест не найден'}), 404
    
    questions = Question.query.filter_by(test_id=test.id).all()
    questions_list = [{'question_text': q.question_text, 'answer': q.answer} for q in questions]
    
    # Run the async function synchronously
    variant_questions = asyncio.run(generate_test_variant(questions_list, test))
    
    return jsonify({
        'title': test.title,
        'questions': variant_questions
    }), 200

async def generate_test_variant(original_test, test):
    subject = test.subject.lower()

    if subject == "math":
        prompt = f"""Ты - опытный учитель математики. Твоя задача - создать похожие варианты для каждого примера.

        Исходные задания:
        {str(original_test)}

        Правила:
        1. Создай точно такое же количество примеров, как в исходном задании
        2. Каждый новый пример должен быть похож на соответствующий исходный пример
        3. Сохраняй тот же тип задачи и уровень сложности

        Примеры преобразования:
        Исходный: "2+3" -> Новый: "4+5" (тот же тип - сложение)
        Исходный: "Дискриминант x²-5x+6" -> Новый: "Дискриминант x²-3x+2" (тот же тип - дискриминант)
        Исходный: "4x=8" -> Новый: "3x=6" (тот же тип - линейное уравнение)

        Для дискриминанта всегда давай ответ в виде одного числа!
        Пример: "Дискриминант x²-3x+2" -> ответ: "1" (не выражение, а число)

        Верни точно {len(original_test)} примеров в формате JSON:
        [
            {{"question_text": "новый_пример", "answer": "ответ"}},
            {{"question_text": "новый_пример", "answer": "ответ"}}
        ]
        """
    
    print("Sending prompt to AI:", prompt)

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        response_text = response.text.strip()
        print("AI Response:", response_text)
        
        try:
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                print("Extracted JSON:", json_str)
                questions = json.loads(json_str)
                
                # Проверяем количество вопросов
                if len(questions) != len(original_test):
                    print(f"Wrong number of questions. Expected: {len(original_test)}, Got: {len(questions)}")
                    return original_test
                
                # Проверяем ответы для дискриминанта
                for q in questions:
                    if "дискриминант" in q["question_text"].lower():
                        try:
                            float(q["answer"])  # Проверяем, что ответ - число
                        except ValueError:
                            print(f"Invalid discriminant answer: {q['answer']}")
                            return original_test
                
                return questions
            
            print("Failed to find valid JSON in response")
            return original_test
            
        except json.JSONDecodeError as e:
            print("JSON decode error:", str(e))
            return original_test
            
    except Exception as e:
        print("Error generating variant:", str(e))
        return original_test

def parse_gpt_response(response: str) -> list:
    try:
        # Попытка разобрать ответ как JSON
        if isinstance(response, str):
            try:
                questions = json.loads(response)
                if isinstance(questions, list):
                    return questions
            except json.JSONDecodeError:
                pass
        
        # Если не удалось разобрать как JSON, разбираем текстовый формат
        questions = []
        lines = response.split('\n')
        current_question = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Вопрос:') or line.startswith('Question:'):
                if current_question:
                    questions.append(current_question)
                current_question = {'question_text': line.split(':', 1)[1].strip()}
            elif line.startswith('Ответ:') or line.startswith('Answer:'):
                if current_question:
                    current_question['answer'] = line.split(':', 1)[1].strip()
        
        if current_question:
            questions.append(current_question)
            
        return questions
    except Exception as e:
        print(f"Error parsing GPT response: {e}")
        return []

            

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
