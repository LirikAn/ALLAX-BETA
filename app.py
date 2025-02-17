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
import re
import math
from fractions import Fraction
from typing import List, Dict

# Настройка Google Gemini API
genai.configure(api_key='AIzaSyBxoiv6GT1CKCZ9cq-iRDKyb8Y55imzTwE')
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql+pymysql://root:123123@192.168.1.245/db_name')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

CORS(
    app,
    origins=["http://localhost:3000", "http://192.168.1.249:3000", "http://127.0.0.1:3000"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

logging.basicConfig(level=logging.INFO)

# Примеры для каждой темы
topic_examples = {
    'квадратные_уравнения': """
    ВАЖНО! Формула дискриминанта всегда: D = b² - 4ac
    
    Пример 1: Найти дискриминант уравнения x² + 6x + 9 = 0
    Решение: 
    a = 1, b = 6, c = 9
    D = b² - 4ac = 6² - 4(1)(9) = 36 - 36 = 0
    
    Пример 2: Найти корни уравнения 2x² - 7x + 3 = 0
    Решение:
    a = 2, b = -7, c = 3
    D = b² - 4ac = (-7)² - 4(2)(3) = 49 - 24 = 25
    """,
    
    'арифметика': """
    Пример 1: Вычислить 25 - 9
    Решение: 25 - 9 = 16
    
    Пример 2: Найти сумму чисел 17 + 8
    Решение: 17 + 8 = 25
    """,
    
    'площади': """
    Пример 1: Найти площадь прямоугольника со сторонами 5 и 4
    Решение: S = a * b = 5 * 4 = 20 кв.ед.
    
    Пример 2: Найти площадь квадрата со стороной 6
    Решение: S = a² = 6² = 36 кв.ед.
    """
}

# Определение math_curriculum
math_curriculum = {
    '1_класс': {
        'числа_и_цифры': [
            'числа от 1 до 20',
            'письмо и чтение чисел',
            'представление чисел'
        ],
        'основные_действия': [
            'сложение до 10',
            'вычитание до 10',
            'числовые последовательности',
            'сравнение чисел'
        ]
    },
    '2_класс': {
        'числа_и_операции': [
            'сложение до 100',
            'вычитание до 100',
            'умножение',
            'деление'
        ],
        'измерения': [
            'длина',
            'масса',
            'время'
        ]
    },
    '3_класс': {
        'числа_и_операции': [
            'многозначные числа',
            'сложные операции',
            'делимость'
        ],
        'измерения': [
            'единицы измерения',
            'время',
            'календарь'
        ]
    },
    '4_класс': {
        'числа_и_операции': [
            'многозначные числа',
            'дроби',
            'десятичные дроби'
        ],
        'измерения': [
            'сложные единицы',
            'время',
            'объемы'
        ]
    },
    '5_класс': {
        'натуральные_числа': [
            'действия с натуральными числами',
            'делимость',
            'обыкновенные дроби'
        ],
        'геометрия': [
            'углы',
            'треугольники',
            'прямоугольники'
        ]
    },
    '6_класс': {
        'рациональные_числа': [
            'положительные и отрицательные числа',
            'координатная прямая',
            'действия с рациональными числами'
        ],
        'отношения_и_пропорции': [
            'отношения',
            'пропорции',
            'проценты'
        ]
    },
    '7_класс': {
        'алгебра': [
            'линейные уравнения',
            'системы уравнений',
            'функции'
        ],
        'геометрия': [
            'треугольники',
            'параллельные прямые',
            'соотношения между сторонами и углами'
        ]
    },
    '8_класс': {
        'алгебра': [
            'квадратные уравнения',
            'неравенства',
            'квадратичная функция'
        ],
        'геометрия': [
            'четырехугольники',
            'площади',
            'подобие треугольников'
        ]
    },
    '9_класс': {
        'алгебра': [
            'степенная функция',
            'прогрессии',
            'элементы комбинаторики'
        ],
        'геометрия': [
            'векторы',
            'метод координат',
            'правильные многоугольники'
        ]
    },
    '10_класс': {
        'алгебра': [
            'тригонометрические функции',
            'тригонометрические уравнения',
            'производная'
        ],
        'геометрия': [
            'параллельность в пространстве',
            'перпендикулярность в пространстве',
            'многогранники'
        ]
    },
    '11_класс': {
        'алгебра': [
            'показательная функция',
            'логарифмическая функция',
            'интеграл'
        ],
        'геометрия': [
            'цилиндр и конус',
            'сфера и шар',
            'объемы тел'
        ]
    }
}

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
    code = db.Column(db.String(6), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    topics = db.Column(db.JSON, nullable=True)  # Новое поле для тем
    created_by = db.Column(db.String(50), nullable=False)

class Question(db.Model):
    __tablename__ = 'Question'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('Test.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.JSON, nullable=True)  # Змінюємо на nullable=True
    answer = db.Column(db.Integer, nullable=False)

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
        # Сначала создаем запись в БД
        db.session.add(Test(
            code=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
            title=data['title'],
            subject=data['subject'],
            topics=[],
            created_by="anonymous"
        ))
        db.session.flush()  # Получаем id теста
        
        new_test = Test.query.filter_by(title=data['title']).order_by(Test.id.desc()).first()
        
        # Добавляем вопросы
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
        print(f"Ошибка при создании теста: {str(e)}")
        return jsonify({'message': f'Помилка при створенні тесту: {str(e)}'}), 500

@app.route('/get-test/<code>', methods=['GET'])
def get_test(code):
    try:
        test = Test.query.filter_by(code=code).first()
        if not test:
            return jsonify({'message': 'Тест не найден'}), 404
        
        # Получаем оригинальные вопросы и сериализуем их
        questions = Question.query.filter_by(test_id=test.id).all()
        original_questions = [{
            'question_text': q.question_text,
            'options': q.options,
            'answer': q.answer
        } for q in questions]
        
        # Генерируем новый вариант теста
        generated_questions = asyncio.run(generate_test_variant(original_questions, test))
        
        return jsonify({
            'title': test.title,
            'questions': generated_questions
        })
    except Exception as e:
        print("Error in get_test:", str(e))
        return jsonify({'message': 'Ошибка при получении теста'}), 500

async def generate_test_variant(original_questions, test):
    print("\n=== Логирование генерации вариантов ===")
    print(f"Предмет: {test.subject}")
    print(f"Количество вопросов: {len(original_questions)}")
    
    def check_discriminant(a, b, c):
        """Вычисляет дискриминант квадратного уравнения"""
        return b**2 - 4*a*c
        
    def check_arithmetic(expression):
        """Проверяет арифметическое выражение"""
        try:
            expression = expression.replace('×', '*')
            return eval(expression)
        except:
            return None
            
    for question in original_questions:
        response = await asyncio.to_thread(model.generate_content, prompt)
        try:
            generated = json.loads(response.text)
            
            # Проверяем тему вопроса
            question_lower = generated['question_text'].lower()
            
            if 'дискриминант' in question_lower:
                # Ищем коэффициенты в тексте
                import re
                coeffs = re.findall(r'(\d+)?x²?\s*([+-]\s*\d+)?x?\s*([+-]\s*\d+)?', question_lower)
                if coeffs:
                    a = int(coeffs[0][0]) if coeffs[0][0] else 1
                    b_str = coeffs[0][1].replace(' ', '') if coeffs[0][1] else '0'
                    b = int(b_str) if b_str else 0
                    c_str = coeffs[0][2].replace(' ', '') if coeffs[0][2] else '0'
                    c = int(c_str) if c_str else 0
                    
                    correct_d = check_discriminant(a, b, c)
                    # Заменяем один из вариантов ответа на правильный
                    generated['options'][0] = str(correct_d)
                    generated['answer'] = 0
                    
            elif any(op in question_lower for op in ['+', '-', '*', '/', '×']):
                nums = re.findall(r'\d+', question_lower)
                ops = re.findall(r'[+\-*/×]', question_lower)
                if nums and ops:
                    expression = f"{nums[0]}{ops[0]}{nums[1]}"
                    correct_result = check_arithmetic(expression)
                    if correct_result is not None:
                        # Заменяем один из вариантов ответа на правильный
                        generated['options'][0] = str(correct_result)
                        generated['answer'] = 0
                        
            all_generated_questions.append(generated)
            
        except Exception as e:
            print(f"\nОшибка при обработке вопроса: {str(e)}")
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

def generate_test_prompt(subject: str, topic: str = None) -> str:
    return f"""Ты - опытный учитель математики. Создай новые тестовые вопросы, похожие по сложности на оригинальные, но с другими числами и условиями.

Правила:
1. Каждый вопрос должен быть уникальным
2. Все вычисления должны быть простыми (результат не больше 100)
3. Варианты ответов должны быть правдоподобными
4. Только один вариант ответа должен быть правильным
5. Используй простые математические операции: +, -, *, /

Пример вопроса:
{{
    "question_text": "Сколько будет 2 + 3?",
    "options": ["3", "4", "5", "6"],
    "answer": 2  // Индекс правильного ответа (0-3), в данном случае "5" это правильный ответ
}}

Верни массив вопросов в формате JSON:
[
    {{"question_text": "вопрос", "options": ["вариант1", "вариант2", "вариант3", "вариант4"], "answer": индекс_правильного_ответа}},
    // другие вопросы...
]
"""

def identify_question_topic(question_text: str) -> tuple:
    """Определяет тему и класс вопроса по его содержанию"""
    question_lower = question_text.lower()
    
    # Ключевые слова для определения тем
    keywords = {
        'квадратные_уравнения': ['дискриминант', 'квадратн', 'уравнен', 'корн'],
        'площади': ['площадь', 'периметр', 'сторон'],
        'тригонометрия': ['sin', 'cos', 'tg', 'ctg'],
        'производная': ['производная', 'касательная'],
        'интеграл': ['интеграл', 'первообразная']
    }
    
    # Определяем тему по ключевым словам
    for topic, words in keywords.items():
        if any(word in question_lower for word in words):
            return topic

    return None

def validate_math_answer(question_text: str, answer: dict) -> bool:
    """Проверяет математическую корректность ответа"""
    # Всегда возвращаем True, полагаясь на ответы нейросети
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
    with open('math_topics.txt', 'w', encoding='utf-8') as f:
        json.dump(math_curriculum, f, ensure_ascii=False, indent=2)

def load_topics_from_file():
    try:
        with open('math_topics.txt', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        save_topics_to_file()
        return math_curriculum

@app.route('/get-topics/<subject>', methods=['GET'])
def get_topics(subject):
    if subject.lower() == 'математика':
        topics = load_topics_from_file()
        return jsonify(topics)
    return jsonify({'message': 'Предмет не найден'}), 404

if __name__ == '__main__':
    save_topics_to_file()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
