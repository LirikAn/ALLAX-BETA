import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import Input from '../components/ui/input';
import Label from '../components/ui/label';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface Question {
  question_text: string;
  answer: string;
}

const EnterTest: React.FC = () => {
  const navigate = useNavigate();
  const [testCode, setTestCode] = useState('');
  const [test, setTest] = useState<{title: string; questions: Question[]} | null>(null);
  const [currentAnswers, setCurrentAnswers] = useState<string[]>([]);
  const [results, setResults] = useState<boolean[]>([]);
  const [showResults, setShowResults] = useState(false);

  const handleSubmitCode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.get(`http://127.0.0.1:5000/get-test/${testCode}`);
      setTest(response.data);
      setCurrentAnswers(new Array(response.data.questions.length).fill(''));
      setShowResults(false);
    } catch (error) {
      alert('Тест не найден');
    }
  };

  const handleAnswerChange = (index: number, value: string) => {
    const newAnswers = [...currentAnswers];
    newAnswers[index] = value;
    setCurrentAnswers(newAnswers);
  };

  const handleCheckAnswers = () => {
    if (!test) return;
    
    const newResults = test.questions.map((question, index) => 
      question.answer.toLowerCase().trim() === currentAnswers[index].toLowerCase().trim()
    );
    setResults(newResults);
    setShowResults(true);
  };

  if (!test) {
    return (
      <div className="auth-form-container">
        <div className="auth-form-header">
          <h2 className="auth-title animate-fade-in">Вход в тест</h2>
          <p className="auth-subtitle animate-fade-in-delayed">
            Введите код теста для начала
          </p>
        </div>

        <form onSubmit={handleSubmitCode} className="auth-form">
          <div className="form-group animate-slide-up">
            <Label htmlFor="testCode" className="form-label">Код теста</Label>
            <Input
              id="testCode"
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              placeholder="Введите код теста"
              className="form-input"
              required
            />
          </div>
          <Button type="submit" className="submit-button">
            Начать тест
          </Button>
          <Button 
            type="button"
            onClick={() => navigate('/home')}
            className="submit-button"
            variant="text"
          >
            Назад в меню
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2 className="auth-title animate-fade-in">{test.title}</h2>
      </div>

      <div className="auth-form">
        {test.questions.map((question, index) => (
          <div key={index} className="form-group animate-slide-up">
            <Label htmlFor={`answer-${index}`} className="form-label">
              {question.question_text}
            </Label>
            <Input
              id={`answer-${index}`}
              value={currentAnswers[index]}
              onChange={(e) => handleAnswerChange(index, e.target.value)}
              placeholder="Ваш ответ"
              className="form-input"
            />
            {showResults && (
              <div className={`result-indicator ${results[index] ? 'correct' : 'incorrect'}`}>
                {results[index] ? '✓ Правильно' : '✗ Неправильно'}
              </div>
            )}
          </div>
        ))}

        <Button 
          onClick={handleCheckAnswers}
          className="submit-button"
          variant="primary"
        >
          Проверить ответы
        </Button>
        <Button 
          onClick={() => navigate('/home')}
          className="submit-button"
          variant="text"
        >
          Назад в меню
        </Button>
      </div>
    </div>
  );
};

export default EnterTest;