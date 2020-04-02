import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 3

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  @app.route('/')
  def hello_test():
    return jsonify({
      'message':' Hello Every Body in the Trivia App',
    })


  CORS(app, resourses={'/':{'origin': '*'}})

  @app.after_request
  def after_request(response):
    response.headers.add('Access-control-Allow-Headers','Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


  def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page-1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions



  def get_categories_from_DB():
    categories = {}
    for cat in Category.query.all():
      categories [cat.id] = cat.type

    return categories
  
  @app.route('/categories')
  def get_all_categories():
    categories = get_categories_from_DB()

    return jsonify({
      'success': True,
      'categories': categories,
    })

  @app.route('/categories/<id>/questions')
  def get_questions_by_categories(id):
    if( Category.query.filter(Category.id == id).one_or_none() == None):
      abort(404)
    qs = Question.query.filter(Question.category == id).all()
    questions = paginate_questions(request , qs)
    d = is_arg_page_valide(qs, request)
    all_pages_available = d['all_pages_available']
    current_page = d['current_page']


    return jsonify({
      'success': True,
      'totalQuestions':len(qs),
      'currentCategory': Category.query.get(id).type,
      'questions': questions,
          'page': current_page +'/'+ str(all_pages_available)
    })

  def is_arg_page_valide(questions, request):
      arg_pages = request.args.get('page')
      all_questions_number = len(questions)
      all_pages_available = int(all_questions_number/QUESTIONS_PER_PAGE)
      if (all_questions_number % QUESTIONS_PER_PAGE) != 0 : 
        all_pages_available += 1

      if(not arg_pages) :
        current_page = "1"
      else:
        if int(arg_pages) > all_pages_available or not arg_pages:
          abort(404)
        current_page = arg_pages

      d = {}
      d['all_pages_available'] = all_pages_available
      d['current_page'] = current_page

      return d
    
  @app.route('/questions')
  def get_all_questions():
    questions = Question.query.all()
    categories = get_categories_from_DB()

    current_questions = paginate_questions(request, questions) 
 
    d = is_arg_page_valide(questions, request)
    all_pages_available = d['all_pages_available']
    current_page = d['current_page']

    return jsonify(
        {
          'success': True,
          'questions': current_questions,
          'totalQuestions': len(questions),
          'categories': categories,
          'currentCategory': None,
          'page': current_page +'/'+ str(all_pages_available)
        })



  @app.route('/questions/<question_id>', methods=['DELETE'])
  def delete_question(question_id):

    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question == None:
      abort(404)
    question.delete()
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)
    # test if the page in the arg is valide
    is_arg_page_valide(selection, request)
    return jsonify({
      'success': True,
      'deleted': question_id,
      'questions': current_questions,
      'totalQuestions': len(Question.query.all())
    }) 

  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    if body is None:
      abort(422)

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)
  
    search_term = body.get('searchTerm', None)
    
    if search_term:
      selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_term))).all()
      current_questions = paginate_questions(request, selection)
      
      d = is_arg_page_valide(selection, request)
      all_pages_available = d['all_pages_available']
      current_page = d['current_page']

      return jsonify({
        'success': True,
        'currentCategory': None,
        'questions': current_questions,
        'totalQuestions': len(selection),
        'page': current_page +'/'+ str(all_pages_available)
      })
    else:
      if new_question is None or new_answer is None or new_difficulty is None or new_category is None :
        abort(404)
      else:  
        quest = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
        quest.insert()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        is_arg_page_valide(selection, request)

        return jsonify({
          'success': True,
          'created': quest.id,
          'questions': current_questions,
          'totalQuestions': len(Question.query.all())
        })


  '''
    Route for create a new Category.
  '''
  @app.route('/categories', methods=['POST'])
  def create_new_category():
    if request.get_json() is None : abort(422)
    body = request.get_json()

    type_cat = body.get('type', None)
    
    if(type_cat is None):
      abort(404)
    else:
      new_category = Category(type=type_cat)
      new_category.insert()
      return jsonify({
          'success': True,
          'created': new_category.id,
          'categories': get_categories_from_DB(),
          'total_categories': len(Category.query.all())
        })
    # try:except:
    #   abort(422)


  @app.route('/quizzes', methods=['POST'])
  def quizzes_fanction():
    if request.get_json() is None: abort(422)
    body = request.get_json()
  
    previous_questions = body.get('previous_questions', None)
    quiz_category = body.get('quiz_category', None)
    quiz_category_id = quiz_category.get('id', -1)

  
    if quiz_category_id == 0:
        selection = Question.query.order_by(Question.id).filter(
            Question.id.notin_(previous_questions)).all()
    else:
        category = Category.query.get(quiz_category_id)
        if category is None:
          abort(404)
        selection = Question.query.order_by(
          Question.id).filter_by(category=quiz_category_id).filter(
          Question.id.notin_(previous_questions)).all()
    selection_length = len(selection)
    if selection_length > 0:
        selected_question = selection[random.randrange(
            0, selection_length)]
        return jsonify({
            'success': True,
            "question": selected_question.format()
        })
    else:
        return jsonify({
            "success": True,
            "question": None
        })   


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "Resource Not Found"
    }),404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "Unprocessable"
    }),422



  return app

    