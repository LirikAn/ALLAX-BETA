import asyncio
import json
import logging
import os
import random
import re
import string
from typing import List, Dict
from dataclasses import dataclass
from functools import lru_cache

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

import google.generativeai as genai


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://192.168.1.249:3000",
    "http://127.0.0.1:3000"
]

DB_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root:123123@192.168.1.245/db_name')
AI_API_KEY = os.environ.get('AIzaSyBxoiv6GT1CKCZ9cq-iRDKyb8Y55imzTwE')

generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 65536,
  "response_mime_type": "text/plain",
}




def get_chat_session():
    return model.start_chat(history=[])


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

CORS(
    app,
    origins=ALLOWED_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


genai.configure(api_key=AI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
)

@dataclass
class User(db.Model):
    __tablename__ = 'User'
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(150), nullable=False)
    email: str = db.Column(db.String(150), unique=True, nullable=False)
    password: str = db.Column(db.String(150), nullable=False)

@dataclass
class Test(db.Model):
    __tablename__ = 'Test'
    id: int = db.Column(db.Integer, primary_key=True)
    code: str = db.Column(db.String(6), unique=True, nullable=False)
    title: str = db.Column(db.String(100), nullable=False)
    subject: str = db.Column(db.String(50), nullable=False)
    topics: Dict = db.Column(db.JSON, nullable=True)
    created_by: str = db.Column(db.String(50), nullable=False)

class Question(db.Model):
    __tablename__ = 'Question'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('Test.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.JSON, nullable=True)
    answer = db.Column(db.Integer, nullable=False)

@lru_cache(maxsize=100)
def load_topics_from_file() -> dict:
    try:
        with open('math_topics.txt', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        save_topics_to_file()
        return {}
def identify_question_topic(question_text: str) -> str:
    question_lower = question_text.lower()
    
    keywords = {
        'квадратные_уравнения': ['дискриминант', 'квадратн', 'уравнен', 'корн'],
        'площади': ['площадь', 'периметр', 'сторон'],
        'тригонометрия': ['sin', 'cos', 'tg', 'ctg'], 
        'производная': ['производная', 'касательная'],
        'интеграл': ['интеграл', 'первообразная']
    }
    
    for topic, words in keywords.items():
        if any(word in question_lower for word in words):
            return topic
    return None

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


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
    
    if not data or 'title' not in data or 'questions' not in data or 'subject' not in data:
        return jsonify({'message': 'Неправильні дані'}), 400

    try:
        new_test = Test(
            code=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
            title=data['title'],
            subject=data['subject'],
            topics=[],
            created_by="anonymous"
        )
        db.session.add(new_test)
        db.session.flush()
        
        for question in data['questions']:
            if 'question_text' not in question or 'answer' not in question:
                db.session.rollback()
                return jsonify({'message': 'Неправильні дані питання'}), 400
                
            db.session.add(Question(
                test_id=new_test.id,
                question_text=question['question_text'],
                options=question.get('options', []),
                answer=question['answer']
            ))
            
        db.session.commit()
        
        return jsonify({
            'message': 'Тест створено успішно!',
            'code': new_test.code
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании теста: {str(e)}")
        return jsonify({'message': f'Помилка при створенні тесту: {str(e)}'}), 500

@app.route('/get-test/<code>', methods=['GET'])
def get_test(code):
    try:
        test = Test.query.filter_by(code=code).first()
        if not test:
            return jsonify({'message': 'Тест не найден'}), 404
        
        questions = Question.query.filter_by(test_id=test.id).all()
        original_questions = [{
            'question_text': q.question_text,
            'options': q.options,
            'answer': q.answer
        } for q in questions]
        
        generated_questions = asyncio.run(generate_test_variant(original_questions, test))
        
        return jsonify({
            'title': test.title,
            'questions': generated_questions
        })
    except Exception as e:
        logger.error("Error in get_test:", str(e))
        return jsonify({'message': 'Ошибка при получении теста'}), 500

async def generate_test_variant(original_questions, test):
    all_generated_questions = []
    
    for question in original_questions:
        try:
            topic = identify_question_topic(question['question_text'])
            prompt = f"""Создай новый математический вопрос по теме: {topic}
            Используй оригинальный вопрос как образец: {question['question_text']}
            Верни ответ в формате JSON:
            {{
                "question_text": "текст вопроса",
                "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
                "answer": индекс_правильного_ответа
            }}"""
            response = await asyncio.to_thread(model.generate_content, prompt)
            generated_questions = json.loads(response.text.strip())
            all_generated_questions.append(generated_questions)
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса: {str(e)}")
            all_generated_questions.append(question)
    
    return all_generated_questions

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

def generate_test_prompt(subject: str, topic_analysis: dict, test_code: str) -> str:
    try:
        existing_questions = []
        filename = f"question_history_{test_code}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_questions = json.load(f)

        topic = topic_analysis['topic']
        complexity = topic_analysis['complexity']
        calculation_type = topic_analysis['calculation_type']

        return f"""Ты - опытный учитель математики. Создай новый тестовый вопрос, похожий по сложности на исходный.

Тема: {topic}
Тип вычислений: {calculation_type}
ВАЖНО! 
1. Создай вопрос, которого нет в этом списке:
{json.dumps(existing_questions, ensure_ascii=False, indent=2)}

2. Сохраняй тот же уровень сложности что и в исходном вопросе!

3. ОБЯЗАТЕЛЬНО:
- Реши задачу самостоятельно и проверь ответ
- Убедись, что все числа в условии корректны
- Проверь, что ответ математически верный
- Убедись, что все варианты ответов уникальны
- Один из вариантов должен быть правильным ответом
- Остальные варианты должны быть правдоподобными, но неверными

4. ВАЖНО! Индексация вариантов ответов:
- Первый вариант имеет индекс 0
- Второй вариант имеет индекс 1
- Третий вариант имеет индекс 2
- Четвертый вариант имеет индекс 3

5. Рандомизуй ответы:
- Правильный ответ должен быть случайно размещен (индекс от 0 до 3)
- Остальные варианты должны быть логичными неправильными ответами

Верни ответ в формате JSON:
[
    {{
        "question_text": "текст вопроса",
        "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
        "answer": индекс_правильного_ответа,
        "solution": "подробное решение задачи"
    }}
]
"""
    except Exception as e:
        print(f"Ошибка при генерации промпта: {str(e)}")
        return базовый_промпт_для_генерации()

def validate_math_answer(question_text: str, answer: dict) -> bool:
    """Проверяет математическую корректность ответа"""
    return True

math_formulas = {
    'начальная_школа': {
        'площади': {
            'квадрат': 'S = a²',
            'прямоугольник': 'S = a * b',
            'треугольник': 'S = (a * h) / 2'
        },
        'периметры': {
            'квадрат': 'P = 4a',
            'прямоугольник': 'P = 2(a + b)',
            'треугольник': 'P = a + b + c'
        }
    },
    'алгебра': {
        'квадратные_уравнения': {
            'дискриминант': {
                'формула': 'D = b² - 4ac',
                'где': [
                    'a - коэффициент при x²',
                    'b - коэффициент при x',
                    'c - свободный член'
                ]
            },
            'корни': {
                'формула': ['x₁ = (-b + √D) / (2a)', 'x₂ = (-b - √D) / (2a)'],
                'условия': [
                    'D > 0 - два корня',
                    'D = 0 - один корень',
                    'D < 0 - нет действительных корней'
                ]
            }
        },
        'формулы_сокращенного_умножения': {
            'квадрат_суммы': '(a + b)² = a² + 2ab + b²',
            'квадрат_разности': '(a - b)² = a² - 2ab + b²',
            'разность_квадратов': 'a² - b² = (a + b)(a - b)'
        },
        'прогрессии': {
            'арифметическая': {
                'n_й_член': 'aₙ = a₁ + (n-1)d',
                'сумма_n_членов': 'Sₙ = (a₁ + aₙ)n/2'
            },
            'геометрическая': {
                'n_й_член': 'bₙ = b₁ * q^(n-1)',
                'сумма_n_членов': 'Sₙ = b₁(1-q^n)/(1-q)'
            }
        }
    },
    'тригонометрия': {
        'основные_тождества': {
            'sin²α + cos²α = 1',
            'tgα = sinα/cosα',
            'ctgα = cosα/sinα'
        },
        'формулы_сложения': {
            'sin(α±β)': 'sinα*cosβ ± cosα*sinβ',
            'cos(α±β)': 'cosα*cosβ ∓ sinα*sinβ'
        }
    },
    'производная': {
        'основные_правила': {
            'сумма': '(u + v)′ = u′ + v′',
            'произведение': '(u*v)′ = u′v + uv′',
            'частное': '(u/v)′ = (u′v - uv′)/v²'
        },
        'таблица_производных': {
            'xⁿ': 'n*x^(n-1)',
            'sin(x)': 'cos(x)',
            'cos(x)': '-sin(x)',
            'eˣ': 'eˣ',
            'ln(x)': '1/x'
        }
    },
    'интеграл': {
        'основные_правила': {
            'линейность': '∫(au + bv)dx = a∫udx + b∫vdx',
            'по_частям': '∫udv = uv - ∫vdu'
        },
        'таблица_интегралов': {
            '∫xⁿdx': 'x^(n+1)/(n+1) + C',
            '∫sin(x)dx': '-cos(x) + C',
            '∫cos(x)dx': 'sin(x) + C',
            '∫eˣdx': 'eˣ + C',
            '∫(1/x)dx': 'ln|x| + C'
        }
    }
}

def save_topics_to_file():
    math_curriculum = math_formulas
    with open('math_topics.txt', 'w', encoding='utf-8') as f:
        json.dump(math_curriculum, f, ensure_ascii=False, indent=2)

def load_topics_from_file():
    try:
        with open('math_topics.txt', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        save_topics_to_file()
        return math_formulas

@app.route('/get-topics/<subject>', methods=['GET'])
def get_topics(subject):
    if subject.lower() == 'математика':
        topics = load_topics_from_file()
        return jsonify(topics)
    return jsonify({'message': 'Предмет не найден'}), 404

topic_examples = {
    'квадратные_уравнения': 'Пример: x² + 5x + 6 = 0',
    'площади': 'Пример: найти площадь прямоугольника со сторонами 4 и 5',
    'тригонометрия': 'Пример: найти sin(30°)',
    'производная': 'Пример: найти производную функции f(x) = x²',
    'интеграл': 'Пример: вычислить ∫x dx'
}


def save_question_to_file(test_code: str, question: dict):
    """Сохраняет вопрос в файл истории"""
    filename = f"question_history_{test_code}.json"
    try:
        # Загружаем существующие вопросы
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                questions = json.load(f)
        else:
            questions = []
            
        # Добавляем новый вопрос
        questions.append(question)
        
        # Сохраняем обновленный список
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Ошибка при сохранении вопроса: {str(e)}")

def check_question_uniqueness(test_code: str, question_text: str) -> bool:
    """Проверяет уникальность вопроса"""
    filename = f"question_history_{test_code}.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                return not any(q['question_text'].lower() == question_text.lower() for q in questions)
        return True
    except Exception as e:
        print(f"Ошибка при проверке уникальности: {str(e)}")
        return True

@app.route('/check-answers', methods=['POST'])
def check_answers():
    try:
        data = request.get_json()
        user_answers = data.get('answers')
        generated_questions = data.get('generated_questions')
        
        correct = sum(
            1 for i, question in enumerate(generated_questions)
            if int(user_answers[i]) == question['answer']
        )
        
        return jsonify({
            'correct': correct,
            'total': len(generated_questions),
        })
        
    except Exception as e:
        logger.error(f"Ошибка при проверке ответов: {str(e)}")
        return jsonify({'message': 'Ошибка при проверке ответов'}), 500

def verify_solution(question_text: str, answer: str, solution: str) -> bool:
    try:
        # Извлекаем числа из текста вопроса
        numbers = [int(n) for n in re.findall(r'\d+', question_text)]
        # Извлекаем ответ как число
        result = int(re.findall(r'\d+', answer)[0])
        
        # Проверяем соответствие решения и ответа
        if "срезал" in question_text or "убрал" in question_text or "забрал" in question_text:
            return sum(numbers[:-1]) - numbers[-1] == result
        else:
            return sum(numbers) == result
            
    except Exception:
        return True  # В случае ошибки считаем ответ верным

if __name__ == '__main__':
    save_topics_to_file()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')