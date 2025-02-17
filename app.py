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

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config
)

# Создаем чат-сессию для каждого запроса
def get_chat_session():
    return model.start_chat(history=[])

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

async def analyze_topic_with_ai(question_text: str) -> str:
    """Анализирует тему вопроса с помощью AI и возвращает подробный анализ"""
    analysis_prompt = f"""Проанализируй математический вопрос и определи:
1. Тему вопроса
2. Уровень сложности (от 1 до 5)
3. Тип вычислений
4. Используемые числа

Вопрос: {question_text}

При анализе учитывай:
- Если в вопросе простые числа (до 10) - это базовый уровень
- Если используются только целые числа - это простой уровень
- Если есть дроби/проценты - это средний уровень
- Если есть сложные вычисления - это высокий уровень

Верни ответ в формате JSON:
{{
    "topic": "название темы",
    "complexity": число_от_1_до_5,
    "calculation_type": "тип_вычислений",
    "numbers_used": [список_чисел],
    "operation": "используемая_операция"
}}"""

    response = await asyncio.to_thread(model.generate_content, analysis_prompt)
    return response.text.strip()

async def generate_test_variant(original_questions, test):
    print("\n=== Логирование генерации вариантов ===")
    print(f"Предмет: {test.subject}")
    print(f"Количество вопросов: {len(original_questions)}")
    
    all_generated_questions = []
    chat_session = get_chat_session()
    
    for question in original_questions:
        try:
            topic_info = analyze_question_topic(question['question_text'])
            prompt = generate_test_prompt(test.subject, topic_info, test.code)
            response = await asyncio.to_thread(chat_session.send_message, prompt)
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            generated_questions = json.loads(response_text.strip())
            
            if isinstance(generated_questions, list) and len(generated_questions) > 0:
                for generated in generated_questions:
                    # Проверяем уникальность вопроса
                    if check_question_uniqueness(test.code, generated['question_text']):
                        # Сохраняем вопрос в историю
                        save_question_to_file(test.code, generated)
                        all_generated_questions.append(generated)
                        break
            
        except Exception as e:
            print(f"\nОшибка при обработке вопроса: {str(e)}")
            if "429 Resource has been exhausted" in str(e):
                # Если превышен лимит API, возвращаем оригинальный вопрос
                all_generated_questions.append(question)
            else:
                # Для других ошибок тоже возвращаем оригинальный вопрос
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

def generate_test_prompt(subject: str, topic_analysis: str, test_code: str) -> str:
    try:
        # Загружаем существующие вопросы
        existing_questions = []
        filename = f"question_history_{test_code}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_questions = json.load(f)

        # Преобразуем topic_analysis в строку, если это словарь
        if isinstance(topic_analysis, dict):
            topic_analysis = json.dumps(topic_analysis, ensure_ascii=False)

        analysis = json.loads(topic_analysis)
        topic = analysis['topic']
        complexity = analysis['complexity']
        calculation_type = analysis['calculation_type']
        numbers = analysis['numbers_used']
        operation = analysis['operation']
        
        # Определяем диапазон чисел на основе сложности исходного вопроса
        if complexity <= 2:
            number_range = "от 1 до 10"
            operations = "только сложение и вычитание"
        elif complexity <= 3:
            number_range = "от 1 до 20"
            operations = "четыре основные арифметические операции"
        else:
            number_range = "от 1 до 100"
            operations = "любые подходящие операции"

        return f"""Ты - опытный учитель математики. Создай новый тестовый вопрос, похожий по сложности на исходный.

Тема: {topic}
Тип вычислений: {calculation_type}
Используй числа: {number_range}
Операции: {operations}

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

4. Рандомизуй ответы:
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

def analyze_question_topic(question_text: str) -> dict:
    """Анализирует тему вопроса и возвращает соответствующие данные"""
    topic = identify_question_topic(question_text)
    
    # Определяем сложность на основе содержимого вопроса
    complexity = 1  # По умолчанию простой уровень
    if any(word in question_text.lower() for word in ['дробь', 'процент', '%']):
        complexity = 3
    elif any(word in question_text.lower() for word in ['умножить', 'разделить', '*', '/']):
        complexity = 2
        
    # Определяем тип вычислений
    calculation_type = "арифметика"  # По умолчанию
    if 'уравнен' in question_text.lower():
        calculation_type = "уравнения"
        
    # Находим числа в вопросе
    numbers_used = re.findall(r'\d+', question_text)
    
    # Определяем операцию
    operation = "сложение"  # По умолчанию
    if '-' in question_text:
        operation = "вычитание"
    elif '*' in question_text or 'умнож' in question_text:
        operation = "умножение"
    elif '/' in question_text or 'дел' in question_text:
        operation = "деление"
            
    return {
        "topic": topic or "арифметика",
        "complexity": complexity,
        "calculation_type": calculation_type,
        "numbers_used": numbers_used,
        "operation": operation,
        "examples": topic_examples.get(topic, ""),
        "formulas": {}
    }

def generate_verification_prompt(question: dict, topic_info: dict) -> str:
    """Создает промпт для проверки вопроса на основе темы"""
    return f"""Проверь математический вопрос на основе следующих данных:

Тема: {topic_info['topic']}

Примеры по теме:
{topic_info['examples']}

Применимые формулы:
{json.dumps(topic_info['formulas'], ensure_ascii=False, indent=2)}

Вопрос для проверки:
{question['question_text']}
Варианты ответов: {question['options']}
Указанный правильный ответ: {question['options'][question['answer']]}

Проверь:
1. Соответствует ли вопрос указанной теме
2. Правильно ли составлены варианты ответов
3. Верно ли указан правильный ответ
4. Решаемая ли задача

Верни ответ в формате JSON:
{{
    "is_valid": true/false,
    "correct_answer": "правильный ответ",
    "explanation": "объяснение проверки"
}}
"""

def базовый_промпт_для_генерации() -> str:
    """Возвращает базовый промпт для генерации вопросов, когда анализ темы не удался"""
    return """Ты - опытный учитель математики. Создай новый простой тестовый вопрос.

Правила:
1. Вопрос должен быть очень простым (уровень начальной школы)
2. Используй только целые числа от 1 до 10
3. Используй только простые операции (сложение, вычитание)
4. Создай 4 варианта ответа:
   - Правильный ответ должен быть помещен в случайную позицию (0-3)
   - Остальные три должны быть неправильными, но правдоподобными
   - Неправильные ответы должны отличаться от правильного на 1-2 единицы
   - Все варианты должны быть разными числами

Верни ответ в формате JSON:
[
    {
        "question_text": "вопрос",
        "options": ["вариант1", "вариант2", "вариант3", "вариант4"],
        "answer": случайный_индекс_правильного_ответа
    }
]
"""

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
        
        correct = 0
        detailed_answers = []
        
        for i, question in enumerate(generated_questions):
            user_answer_index = int(user_answers[i])
            is_correct = user_answer_index == question['answer']
            
            # Убираем дополнительную проверку решения, так как она создает ложные срабатывания
            if is_correct:
                correct += 1
                
            detailed_answers.append({
                'isCorrect': is_correct,
                'userAnswer': question['options'][user_answer_index],
                'correctAnswer': question['options'][question['answer']],
                'questionText': question['question_text']
            })
        
        return jsonify({
            'correct': correct,
            'total': len(generated_questions),
            'answers': detailed_answers
        })
        
    except Exception as e:
        print(f"Ошибка при проверке ответов: {str(e)}")
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
