import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import Input from '../components/ui/input';
import Label from '../components/ui/label';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Info } from 'lucide-react';

interface Question {
  question_text: string;
  options: string[];
  answer: number;
}

const EnterTest: React.FC = () => {
  const navigate = useNavigate();
  const [testCode, setTestCode] = useState('');
  const [test, setTest] = useState<{title: string; questions: Question[]} | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswers, setCurrentAnswers] = useState<string[]>([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isEntering, setIsEntering] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<{
    correct: number;
    total: number;
    answers: { isCorrect: boolean; userAnswer: string; correctAnswer: string; questionText: string }[];
  }>({ correct: 0, total: 0, answers: [] });
  const [usedAnswers, setUsedAnswers] = useState<string[]>([]);

  const handleSubmitCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAnimating(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/get-test/${testCode}`);
      setTest(response.data);
      setCurrentAnswers(new Array(response.data.questions.length).fill(''));
      setIsEntering(false);
    } catch (error) {
      alert('Тест не найден');
    }
    setTimeout(() => setIsAnimating(false), 500);
  };

  const getRandomAnswer = (correctAnswer: string, options: string[]): string => {
    // Получаем все индексы, кроме правильного ответа и уже использованных
    const availableIndexes = options
      .map((_, index) => index.toString())
      .filter(index => 
        index !== correctAnswer && 
        !usedAnswers.includes(index)
      );

    // Если нет доступных вариантов, сбрасываем использованные ответы
    if (availableIndexes.length === 0) {
      setUsedAnswers([]);
      return getRandomAnswer(correctAnswer, options);
    }

    // Выбираем случайный индекс из доступных
    const randomIndex = Math.floor(Math.random() * availableIndexes.length);
    const selectedAnswer = availableIndexes[randomIndex];
    
    // Добавляем выбранный ответ в использованные
    setUsedAnswers(prev => [...prev, selectedAnswer]);
    
    return selectedAnswer;
  };

  const handleAnswerSelect = (value: string) => {
    const newAnswers = [...currentAnswers];
    newAnswers[currentQuestionIndex] = value;
    setCurrentAnswers(newAnswers);
    
    if (currentQuestionIndex === test!.questions.length - 1) {
        calculateResults(newAnswers);
    } else {
        setTimeout(() => {
            setCurrentQuestionIndex(prev => prev + 1);
        }, 500);
    }
  };

  const calculateResults = (answers: string[]) => {
    let correct = 0;
    const detailedAnswers = test!.questions.map((q, idx) => {
        const userAnswerIndex = parseInt(answers[idx]);
        const isCorrect = userAnswerIndex === q.answer;
        if (isCorrect) correct++;
        
        return {
            isCorrect,
            userAnswer: q.options[userAnswerIndex] || 'Не отвечено',
            correctAnswer: q.options[q.answer],
            questionText: q.question_text
        };
    });

    setResults({
        correct,
        total: test!.questions.length,
        answers: detailedAnswers
    });
    setShowResults(true);
  };

  if (!test || isEntering) {
    return (
      <div className="test-container enter-test-container">
        <div className="test-header">
          <div className="progress-indicator">
            <button className="close-button" onClick={() => navigate('/home')}>✕</button>
          </div>
        </div>

        <div className="enter-test-content">
          <div className="auth-form-header">
            <h2 className="auth-title animate-fade-in">Вход в тест</h2>
            <p className="auth-subtitle animate-fade-in-delayed">
              Введите код теста для начала
            </p>
          </div>

          <form onSubmit={handleSubmitCode} className="enter-test-form">
            <div className="form-group animate-slide-up">
              <Input
                type="text"
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                placeholder="Введите код теста"
                required
              />
            </div>
            <div className="enter-test-buttons">
              <Button 
                type="button" 
                onClick={() => navigate('/home')}
                className="back-button"
                variant="secondary"
              >
                Назад в меню
              </Button>
              <Button type="submit" className="submit-button">
                Начать тест
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  if (showResults) {
    return (
      <div className="test-container results-view">
        <div className="test-header">
          <div className="progress-indicator">
            <button className="close-button" onClick={() => navigate('/home')}>✕</button>
          </div>
        </div>

        <div className="results-content">
          <div className="results-header">
            <h2>Результаты теста</h2>
            <div className="score-circle">
              <div className="score-value">
                {Math.round((results.correct / results.total) * 100)}%
              </div>
              <div className="score-label">
                {results.correct} из {results.total}
              </div>
            </div>
          </div>

          <div className="answers-review">
            {results.answers.map((result, index) => (
              <div key={index} className={`answer-review-item ${result.isCorrect ? 'correct' : 'incorrect'}`}>
                <div className="question-review">
                  <span className="question-number">#{index + 1}</span>
                  <p>{result.questionText}</p>
                </div>
                <div className="answer-details">
                  <div className="user-answer">
                    <span>Ваш ответ:</span>
                    <strong className={result.isCorrect ? 'correct-text' : 'incorrect-text'}>
                      {result.userAnswer}
                    </strong>
                  </div>
                  {!result.isCorrect && (
                    <div className="correct-answer">
                      <span>Правильный ответ:</span>
                      <strong>{result.correctAnswer}</strong>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="results-actions">
            <button className="retry-button" onClick={() => navigate('/home')}>
              Завершить тест
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = test.questions[currentQuestionIndex];

  return (
    <div className="test-container">
      <div className="test-header">
        <div className="progress-indicator">
          <span>{currentQuestionIndex + 1} / {test.questions.length}</span>
          <button className="close-button" onClick={() => navigate('/home')}>✕</button>
        </div>
      </div>

      <div className="test-content">
        <div className="question-box">
          <p className="question-text">{currentQuestion.question_text}</p>
          
          <div className="options-table">
            <div className="options-row">
              {currentQuestion.options.map((option, index) => (
                <div key={index} className="option-cell">
                  <span className="option-letter">{String.fromCharCode(65 + index)}</span>
                  <span className="option-value">{option}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="answer-section">
          <h3 className="answer-prompt">Выберите верное решение</h3>
          <div className="answer-grid">
            {currentQuestion.options.map((_, index) => (
              <button
                key={index}
                onClick={() => handleAnswerSelect(index.toString())}
                className={`answer-button ${getOptionColor(index)}`}
                disabled={currentAnswers[currentQuestionIndex] !== ''}
              >
                {String.fromCharCode(65 + index)}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const getOptionColor = (index: number): string => {
  const colors = [
    'bg-red-100 hover:bg-red-200',
    'bg-orange-100 hover:bg-orange-200',
    'bg-blue-100 hover:bg-blue-200',
    'bg-green-100 hover:bg-green-200',
    'bg-purple-100 hover:bg-purple-200'
  ];
  return colors[index] || colors[0];
};

export default EnterTest;