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
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<{
    correct: number;
    total: number;
    answers: { isCorrect: boolean; userAnswer: string; correctAnswer: string; questionText: string }[];
  }>({ correct: 0, total: 0, answers: [] });

  const handleSubmitCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.get(`http://127.0.0.1:5000/get-test/${testCode}`);
      setTest(response.data);
      setCurrentAnswers(new Array(response.data.questions.length).fill(''));
      setCurrentQuestionIndex(0);
      setShowResults(false);
    } catch (error) {
      alert('Тест не найден');
    }
  };

  const handleAnswerSelect = async (value: string) => {
    const newAnswers = [...currentAnswers];
    newAnswers[currentQuestionIndex] = value;
    setCurrentAnswers(newAnswers);
    
    if (currentQuestionIndex === test!.questions.length - 1) {
      try {
        const response = await axios.post('http://127.0.0.1:5000/check-answers', {
          test_code: testCode,
          answers: newAnswers.map(answer => parseInt(answer)),
          generated_questions: test!.questions
        });
        setResults(response.data);
        setShowResults(true);
      } catch (error) {
        alert('Ошибка при проверке ответов');
      }
    } else {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  if (!test) {
    return (
      <div className="test-container enter-test-container">
        <div className="test-header">
          <div className="progress-indicator">
            <button className="close-button" onClick={() => navigate('/home')}>✕</button>
          </div>
        </div>
        
        <div className="enter-test-content">
          <h2>Введите код теста</h2>
          <form onSubmit={handleSubmitCode} className="enter-test-form">
            <input
              type="text"
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              placeholder="Введите код теста"
              required
            />
            <div className="enter-test-buttons">
              <button type="button" onClick={() => navigate('/home')} className="back-button">
                Назад
              </button>
              <button type="submit" className="submit-button">
                Начать тест
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  if (showResults) {
    return (
      <div className="test-container results-view">
        <div className="results-content">
          <div className="score-circle">
            <span className="score-value">{results.correct}/{results.total}</span>
            <span className="score-label">Правильно</span>
          </div>
          
          <div className="answers-review">
            {results.answers.map((answer, index) => (
              <div key={index} className={`answer-review-item ${answer.isCorrect ? 'correct' : 'incorrect'}`}>
                <div className="question-text">
                  <span className="question-number">Вопрос {index + 1}:</span>
                  {answer.questionText}
                </div>
                <div className="answer-comparison">
                  <div className="user-answer">
                    <span>Ваш ответ: </span>
                    <strong>{answer.userAnswer}</strong>
                  </div>
                  <div className="correct-answer">
                    <span>Правильный ответ: </span>
                    <strong>{answer.correctAnswer}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="buttons-container">
            <button onClick={() => navigate('/home')} className="back-button">
              Вернуться на главную
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Отображение вопросов теста
  return (
    <div className="test-container">
      <div className="test-header">
        <div className="progress-indicator">
          Вопрос {currentQuestionIndex + 1} из {test.questions.length}
        </div>
      </div>

      <div className="test-content">
        <div className="question-box">
          <div className="question-text">
            {test.questions[currentQuestionIndex].question_text}
          </div>
          <div className="options-grid">
            {test.questions[currentQuestionIndex].options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswerSelect(index.toString())}
                className={`option-button ${
                  parseInt(currentAnswers[currentQuestionIndex]) === index ? 'selected' : ''
                }`}
              >
                <span className="option-letter">{String.fromCharCode(65 + index)}</span>
                <span className="option-text">{option}</span>
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