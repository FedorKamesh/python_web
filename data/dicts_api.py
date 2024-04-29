import flask
from flask import jsonify, make_response, request
from flask_restful import abort

from data import db_session
from data.diction import Dict

blueprint = flask.Blueprint(
    'dicts_api',
    __name__,
    template_folder='templates'
)

@blueprint.route('/api/writings')
def get_writings():
    db_sess = db_session.create_session()
    dicts = db_sess.query(Dict).all()
    return jsonify(
        {
            'writings':
                [item.to_dict(only = ('title', 'content', 'user.name'))
                 for item in dicts]
        }
    )

@blueprint.route('/api/writing/<int:dicts_id>', methods=['GET'])
def get_one_writing(dicts_id):
    db_sess = db_session.create_session()
    dict = db_sess.query(Dict).get(dicts_id)
    if not dict:
        return make_response(jsonify({'error': 'Not found'}), 404)
    return jsonify(
        {
            'writing': dict.to_dict(only=(
                'title', 'content', 'user_id', 'is_private'))
        }
    )

@blueprint.route('/api/writings', methods=['POST'])
def create_writing():
    if not request.json:
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 ['title', 'content', 'user_id', 'is_private']):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    db_sess = db_session.create_session()
    dicts = Dict(
        title=request.json['title'],
        content=request.json['content'],
        user_id=request.json['user_id'],
        is_private=request.json['is_private']
    )
    db_sess.add(dicts)
    db_sess.commit()
    return jsonify({'id': dicts.id})

@blueprint.route('/api/writing/<int:dicts_id>', methods=['DELETE'])
def delete_writing(dicts_id):
    db_sess = db_session.create_session()
    dicts = db_sess.query(Dict).get(dicts_id)
    if not dicts:
        return make_response(jsonify({'error': 'Not found'}), 404)
    db_sess.delete(dicts)
    db_sess.commit()
    return jsonify({'success': 'OK'})

def abort_if_writing_not_found(dicts_id):
    session = db_session.create_session()
    dicts = session.query(Dict).get(dicts_id)
    if not dicts:
        abort(404, message=f"Writing {dicts_id} not found")