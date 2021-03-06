from tests.fixture_base import app, db, session
from flask import url_for
from user_server.api.models import User, RecipeList, Recipes
import json
from tests.testshortcuts import  add_user_via_endpoint, login_user_via_endpoint
from tests.testshortcuts import add_user, add_recipe_list

def test_add_recipe_to_recipe_list(client,session):
    # construct user
    u = add_user(session)
    token = u.generate_auth_token().decode('utf-8')
    recipe_list = add_recipe_list(session, u.id, 'test list')

    # add recipes via endpoint
    recipe_data = [{
        'name': 'potatos',
        'url': 'http://recipes.com/potatoesforeverone',
        'pic_url': 'http://somanypictures.of.potatoes.com',
        'id': 123
    }]

    response = client.post(
        url_for('users.add_recipes_to_list'),
        data=json.dumps({
            'targetListId': recipe_list.id,
            'recipes': recipe_data
        }),
        content_type="application/json",
        headers={"Authorization": token}
    )

    assert response.status_code == 200
    assert len(recipe_list.recipes) == 1

    data = response.get_json()
    assert data['status'] == 'success'
    assert data['message'] == f'{recipe_list.list_name} updated'
    assert len(data['updatedRecipes']) == 1
    assert data['updatedRecipes'][0]['name'] == Recipes.query.first().recipe_name


def test_add_multiple_recipes_to_recipe_list(client,session):
    # construct user
    u = add_user(session)
    token = u.generate_auth_token().decode('utf-8')
    recipe_list = add_recipe_list(session, u.id, 'test list')

    # add recipes via endpoint
    recipe_data = [
        {
            'name': 'potatos',
            'url': 'http://recipes.com/potatoesforeverone',
            'pic_url': 'http://somanypictures.of.potatoes.com',
            'id': 123
        },
        {
            'name': 'potatos with other stfuf',
            'url': 'http://recipes.com/potatoesforeverone',
            'pic_url': 'http://somanypictures.of.potatoes.com',
            'id': 124
        },
        {
            'name': 'stuffed potatos',
            'url': 'http://recipes.com/potatoesforeverone',
            'pic_url': 'http://somanypictures.of.potatoes.com',
            'id': 125
        },
    ]

    response = client.post(
        url_for('users.add_recipes_to_list'),
        data=json.dumps({
            'targetListId': recipe_list.id,
            'recipes': recipe_data
        }),
        content_type="application/json",
        headers={"Authorization": token}
    )

    assert response.status_code == 200
    assert len(recipe_list.recipes) == 3

    data = response.get_json()
    assert data['status'] == 'success'
    assert data['message'] == f'{recipe_list.list_name} updated'
    assert len(data['updatedRecipes']) == 3
    assert 'potato' in data['updatedRecipes'][0]['name']


def add_user_recipe_list_and_recipes(session):
    u = add_user(session)
    token = u.generate_auth_token().decode('utf-8')
    recipe_list = add_recipe_list(session, u.id, 'test list')
    r1 = Recipes(
        recipe_name='potato',
        recipe_url='http://blah.com',
        pic_url='http://picturesofpotatoes.com',
        recipe_list_id=recipe_list.id,
        recipe_id=12,
        added_by=u.id
    )
    r2 = Recipes(
        recipe_name='potato',
        recipe_url='http://blah.com',
        pic_url='http://picturesofpotatoes.com',
        recipe_list_id=recipe_list.id,
        recipe_id=123,
        added_by=u.id
    )
    session.add(r1)
    session.add(r2)
    session.commit()

    assert Recipes.query.count() == 2
    assert len(RecipeList.query.first().recipes) == 2

    return (u, token, recipe_list)


def test_get_recipe_list_back_when_given_empty_list(client, session):
    u, token, recipe_list = add_user_recipe_list_and_recipes(session)

    response = client.post(
        url_for('users.add_recipes_to_list'),
        data=json.dumps({
            'targetListId': recipe_list.id,
            'recipes': {}
        }),
        content_type="application/json",
        headers={"Authorization": token}
    )

    assert response.status_code == 200
    data = response.get_json()

    recipes = data['updatedRecipes']
    assert 'name' in recipes[0]
    assert 'name' in recipes[1]
    assert 'url' in recipes[0]
    assert 'url' in recipes[1]
    assert 'potato' in recipes[0]['name']
    assert recipes[0]['id'] == 123 or recipes[1]['id'] == 123



def test_delete_recipe_from_list_via_endpoint(session, client):
    u, token, recipe_list = add_user_recipe_list_and_recipes(session)
    recipe_id = 123  # this is recipe id that previous line added
    request_data = {
        'targetList': recipe_list.id,
        'targetRecipe': recipe_id
    }
    response = client.post(
        url_for('users.remove_recipe_from_list'),
        data=json.dumps(request_data),
        content_type='application/json',
        headers={'Authorization': token}
    )

    assert response.status_code == 200
    data = response.get_json()

    # check response is accurate
    assert 'success' in data['status']
    assert 'deleted potato from target list' in data['message']
    assert 1 == len(data['updatedRecipes'])
    assert data['updatedRecipes'][0]['id'] == 12 # 12 is id that should be there

    # check database

    assert Recipes.query.filter_by(recipe_list_id=recipe_list.id).count() == 1

def test_invalid_input_with_remove():
    pass
