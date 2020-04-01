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
  def get_quetions_by_categories(id):
    if( Category.query.filter(Category.id == id).one_or_none() == None):
      return jsonify({
      'result':'No category id '+id
      })
    qs = Question.query.filter(Question.category == id)
    questions = paginate_questions( request , qs)


    return jsonify({
      'totalQuestions':qs.count(),
      'currentCategory': Category.query.get(id).type,
      'questions': questions,
    })

  @app.route('/questions')
  def get_all_questions():
    # questions = get_questions_from_DB()
    questions = Question.query.all()
    categories = get_categories_from_DB()

    current_questions = paginate_questions(request, questions) 

    if(not request.args.get('page')) :
      current_page = "1"
    else:
      current_page = str(request.args.get('page'))

    all_pages = str(int(len(Question.query.all())/QUESTIONS_PER_PAGE) + 1)

    return jsonify(
        {
          'success': True,
          'questions': current_questions,
          'totalQuestions': len(questions),
          'categories': categories,
          'currentCategory': None,
          'page': current_page +'/'+ all_pages
        })



  @app.route('/questions/<question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question == None:
        abort(404)
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })  
    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    if body is None:
      abort(404)

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)
  
    search_term = body.get('searchTerm', None)
    try: 
      if search_term:
        selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_term)))
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'currentCategory': None,
          'questions': current_questions,
          'totalQuestions': len(current_questions)
        })
      else:
        # if new_question is None or new_answer is None:
        #   abort(422)
        # else:  
          quest = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
          quest.insert()

          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)

          return jsonify({
            'success': True,
            'created': quest.id,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
          })
    except:
      abort(422)

  '''
    Route for create a new Category.
  '''
  @app.route('/categories', methods=['POST'])
  def create_new_category():
    body = request.get_json()

    type_cat = body.get('type', None)
    try:
      if(type_cat is None):
        abort(422)
      else:
        new_category = Category(type=type_cat)
        new_category.insert()
        return jsonify({
            'success': True,
            'created': new_category.id,
            'categories': get_categories_from_DB(),
            'total_categories': len(Category.query.all())
          })
    except:
      abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def quizzes_fanction():
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
      "seccess": False,
      "error": 404,
      "message": "Resource Not Found"
    }),404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "seccess": False,
      "error": 422,
      "message": "Unprocessable"
    }),422



  return app

    