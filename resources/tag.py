from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import TagSchema, TagItemSchema

from sqlalchemy.exc import SQLAlchemyError
from db import db
from models import TagModel, StoreModel, ItemModel

blp = Blueprint("tags", __name__, description="operation on tags")


@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        tag = TagModel(store_id=store_id, **tag_data)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, messege=str(e))

        return tag


@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @blp.response(202, description="Deletes a tag if no items are linked")
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(400, description="Tag is linked to one or more items. Tag not deleted")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted."}

        abort(400, message="Could not delete tag. Tag linked to one or more items")



@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(400, message="Tag and Item can't be with different store id.")

        if tag in item.tags:
            abort(400, message="tag is already linked to the item")

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return tag

    @blp.response(200, TagItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if item.store.id != tag.store.id:
            abort(400, messege="Tag and Item can't be with different store id.")

        try:
            item.tags.remove(tag)
        except ValueError as e:
            abort(400, message=str(e))

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return {"message": "Item and tag have been Unlinked", "tag": tag, "item": item}
