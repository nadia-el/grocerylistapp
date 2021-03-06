import secrets
from functools import wraps

from flask import abort, request

from flask_mail import Message
from flask_login import current_user

from grocerylistapp import db, mail
from grocerylistapp.models import RecipeList, CompiledList


line_colors = {
    "INGREDIENT": "btn-ingredient",
    "CARDINAL": "btn-amount",
    "QUANTITY": "btn-measurement",
    "O": "btn-base"
}


def create_list(user_id, list_name="Untitled List"):
    # create new list
    random_hex = secrets.token_urlsafe(8)
    new_list = CompiledList(hex_name=random_hex, user_id=user_id, name=list_name)
    db.session.add(new_list)
    db.session.commit()

    # create recipe for user-added lines
    user_added_list = RecipeList(name="Additional Ingredients",
                                 hex_name=secrets.token_urlsafe(8),
                                 hex_color="#D3D3D3")
    user_added_list.complist = new_list
    db.session.add(user_added_list)
    db.session.commit()
    return new_list


def sort_list(list_lines):
    # sort by the index_in_list function
    def sort_by_index(e):
        print(e.index_in_list)
        return e.index_in_list
    list_lines.sort(key=sort_by_index)


def email_list(email, comp_list, list_lines, recipe_list):
    msg = Message('Your Grocery List: ' + comp_list.name,
                  sender='grocerylistapp5@gmail.com',
                  recipients=[email])

    list_html = f'''
    <h1>{comp_list.name}</h1>
    <ul>'''

    for line in list_lines:

        line_style = " style='color:darkgrey'" if line.checked else ""
        line_checked = " <span style='font-style: italic'>(checked)</span>" if line.checked else ""

        list_html += f'<li{line_style}>{line.ingredient}{line_checked}</li>'

    list_html += '''
    </ul> 
    <h1> Recipes in List: </h1>
    <ul>'''

    # remove 'Additional Ingredients' recipe:
    recipe_list = [recipe for recipe in recipe_list if recipe.name != "Additional Ingredients"]

    for recipe in recipe_list:
        list_html += f'''<li><a href={recipe.recipe_url}>{recipe.name}</a></li>'''

    list_html += '</ul>'

    msg.html = list_html

    mail.send(msg)


def owner_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_list = CompiledList.query.filter_by(hex_name=kwargs.get('hex_name', '')).first()
        if not current_list:
            # try to get from form
            current_list = CompiledList.query.filter_by(hex_name=request.form.get('id', '', type=str)).first_or_404()
        if not current_list:
            # this shouldn't happen
            return abort(500)
        if current_list.user_id != current_user.id:
            return abort(403)

        return func(*args, **kwargs)
    return wrapper