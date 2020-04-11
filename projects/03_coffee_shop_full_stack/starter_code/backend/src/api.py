import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    '''
    @TODO uncomment the following line to initialize the datbase
    !! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
    !! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
    '''
    # db_drop_and_create_all()

    ## ROUTES
   
    @app.route('/')
    def home():
        return jsonify(
            {
            'success': True,
            'Home': 'Home page for the drink caffee' 
            }
        )

    @app.route('/drinks')
    def get_drinks():
        data = Drink.query.all()
        drinks = list(map(Drink.short, data))
        if drinks is None or len(drinks) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'drinks': drinks
        })

    @app.route('/drinks-detail')
    # require the 'get:drinks-detail' permission
    @requires_auth('get:drinks-detail')
    def get_drinks_detail(payload):
        drinks_query = Drink.query.all()
        drinks = list(map(Drink.long, drinks_query))
        if drinks is None or len(drinks) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'drinks': drinks
        })

    @app.route('/drinks', methods=['POST'])
    @requires_auth('post:drinks')
    def post_drink(payload):
        body = request.get_json()
        if body is None:
            abort(404)
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        # verify id there is no duplicate
        duplicate = Drink.query.filter(Drink.title == title).one_or_none()
        if duplicate is not None:
            abort(400)
        # if the reciepe has not been inputed as a list
        if type(recipe) is not list:
            recipe = [recipe]
        try:
            new_drink = Drink(title=title, recipe=json.dumps(recipe))
            new_drink.insert() # insert in the database

            return jsonify({
                'success': True,
                'drinks': [new_drink.long()]
            })
        except:
            abort(422)

    
    @app.route('/drinks/<int:drink_id>', methods=['PATCH'])
    @requires_auth('patch:drinks')
    def update_drink(payload, drink_id):
        try:
            # get the element with given id
            drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
            if drink is None:
                abort(404)
            body = request.get_json()  # get the body
            if body is None:
                abort(404)
            updated_title = body.get('title', None)
            updated_recipe = body.get('recipe', None)
            if updated_title is not None:
                drink.title = updated_title
            if updated_recipe is not None:
                # if the recipe is not a list transform it as a list
                if type(updated_recipe) is not list:
                    updated_recipe = [updated_recipe]
                # update drink.recipe with given value
                drink.recipe = json.dumps(updated_recipe)
            drink.update()  # update the record
            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            })
        except:
            abort(422)

    
    @app.route('/drinks/<drink_id>', methods=['DELETE'])
    @requires_auth('delete:drinks')
    def delete_drink(payload, drink_id):
        # get the drink by id to delete
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)
        try:
            drink.delete()  # delete this item
            return jsonify({
                "success": True,
                "delete": drink_id
            })
        except:
            abort(422)


    ## Error Handling
    '''
    Example error handling for unprocessable entity
    '''
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
                        "success": False, 
                        "error": 422,
                        "message": "unprocessable"
                        }), 422


    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
                        "success": False,
                        "error": 404,
                        "message": "resource not found"
                    }), 404

 
 
    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
                        "success": False,
                        "error": 405,
                        "message": "method not allowed"
                    }), 405

 
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
                        "success": False,
                        "error": 400,
                        "message": "bad request"
                    }), 400


    @app.errorhandler(AuthError)
    def auth_error(error):
        return jsonify({
                        "success": False,
                        "error": error.status_code,
                        "code": error.error['code'],
                        "message": error.error['description']
                    }), error.status_code


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)