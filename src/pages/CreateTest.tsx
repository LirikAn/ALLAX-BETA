import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import Input from '../components/ui/input';
import Label from '../components/ui/label';
import { Card, CardContent } from '../components/ui/card';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Check, Trash2 } from 'lucide-react';

interface Question {
  question_text: string;
  answer: string;
  type: 'test' | 'text';
  options?: string[];
  correctOption?: number;
}

const CreateTest: React.FC = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [testCode, setTestCode] = useState<string>('');

  const handleAddQuestion = (type: 'test' | 'text') => {
    const newQuestion: Question = {
      question_text: '',
      answer: '',
      type: type,
      options: type === 'test' ? ['', '', '', ''] : undefined,
      correctOption: type === 'test' ? undefined : undefined
    };
    setQuestions([...questions, newQuestion]);
  };

  const handleChangeQuestion = (index: number, field: string, value: string) => {
    setQuestions(prevQuestions => {
      const newQuestions = [...prevQuestions];
      newQuestions[index] = { ...newQuestions[index], [field]: value };
      return newQuestions;
    });
  };

  const handleChangeOption = (questionIndex: number, optionIndex: number, value: string) => {
    setQuestions(prevQuestions => {
      const newQuestions = [...prevQuestions];
      if (newQuestions[questionIndex].options) {
        newQuestions[questionIndex].options![optionIndex] = value;
      }
      return newQuestions;
    });
  };

  const handleSetCorrectOption = (questionIndex: number, optionIndex: number) => {
    setQuestions(prevQuestions => {
      const newQuestions = [...prevQuestions];
      newQuestions[questionIndex].correctOption = optionIndex;
      newQuestions[questionIndex].answer = String(optionIndex + 1);
      return newQuestions;
    });
  };

  const handleDeleteQuestion = (index: number) => {
    setQuestions(questions.filter((_, qIndex) => qIndex !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        'http://192.168.1.249:5000/create-test',
        {
          title,
          subject,
          questions: questions.map(q => ({
            ...q,
            question_text: q.question_text.trim(),
            answer: q.answer.trim()
          }))
        }
      );
      alert('Тест успешно создан!');
      setTestCode(response.data.code);
    } catch (error) {
      alert('Ошибка при создании теста');
    }
  };

  return (
    <div className="page-container">
      <div className="auth-form-header">
        <h2 className="auth-title animate-fade-in">Создание теста</h2>
        <p className="auth-subtitle animate-fade-in-delayed">
          Создайте новый тест
        </p>
      </div>

      <form onSubmit={handleSubmit} className="create-test-form">
        <Card className="mb-6">
          <CardContent>
            <div className="form-group">
              <Label htmlFor="title">Название теста</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <Label htmlFor="subject">Предмет</Label>
              <select
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="form-input"
                required
              >
                <option value="">Выберите предмет</option>
                <option value="math">Математика</option>
                <option value="ukrainian">Українська мова</option>
              </select>
            </div>
          </CardContent>
        </Card>

        <div className="questions-container">
          {questions.map((question, qIndex) => (
            <Card key={qIndex} className="question-card mb-6">
              <CardContent>
                <div className="question-header">
                  <h3 className="question-title">Вопрос {qIndex + 1}</h3>
                  <div className="question-actions">
                    <span className="question-type-badge">
                      {question.type === 'test' ? 'Тестовый' : 'Текстовый'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeleteQuestion(qIndex)}
                      className="delete-question-button"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>

                <Input
                  value={question.question_text}
                  onChange={(e) => handleChangeQuestion(qIndex, 'question_text', e.target.value)}
                  placeholder="Текст вопроса"
                  className="question-input"
                  required
                />

                {question.type === 'test' ? (
                  <div className="options-grid">
                    {question.options?.map((option, oIndex) => (
                      <div key={oIndex} className="option-container">
                        <div className="option-input-wrapper">
                          <Input
                            value={option}
                            onChange={(e) => handleChangeOption(qIndex, oIndex, e.target.value)}
                            placeholder={`Вариант ${oIndex + 1}`}
                            className="option-input"
                            required
                          />
                          <button
                            type="button"
                            onClick={() => handleSetCorrectOption(qIndex, oIndex)}
                            className={`correct-option-button ${
                              question.correctOption === oIndex ? 'active' : ''
                            }`}
                          >
                            {question.correctOption === oIndex ? (
                              <Check className="check-icon" />
                            ) : (
                              <div className="empty-check" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={question.answer}
                    onChange={(e) => handleChangeQuestion(qIndex, 'answer', e.target.value)}
                    placeholder="Правильный ответ"
                    className="text-answer-input"
                    required
                  />
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="button-group">
          <Button 
            type="button"
            onClick={() => navigate('/home')}
            className="submit-button animate-fade-in"
            variant="text"
          >
            Назад в меню
          </Button>
          
          <Button 
            type="button"
            onClick={() => handleAddQuestion('test')}
            className="submit-button animate-fade-in"
          >
            Добавить тестовый вопрос
          </Button>
          <Button 
            type="button"
            onClick={() => handleAddQuestion('text')}
            className="submit-button animate-fade-in"
          >
            Добавить текстовый вопрос
          </Button>
          <Button 
            type="submit"
            className="submit-button animate-fade-in"
          >
            Создать тест
          </Button>
        </div>

        {testCode && (
          <div className="test-code animate-fade-in">
            <p>Код теста: {testCode}</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default CreateTest;