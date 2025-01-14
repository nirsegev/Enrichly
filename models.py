from . import db

link_tags = db.Table(
    'link_tags',
    db.Column('link_id', db.Integer, db.ForeignKey('user_links.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class UserLink(db.Model):
    __tablename__ = 'user_links'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String, nullable=False)
    link = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=True)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String, nullable=True)
    price = db.Column(db.String, nullable=True)
    images = db.Column(db.JSON, nullable=True)
    site_name = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    tags = db.relationship('Tag', secondary=link_tags, back_populates='links')


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    links = db.relationship('UserLink', secondary=link_tags, back_populates='tags')
