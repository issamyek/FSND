#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate # added for the migration
import datetime
from sqlalchemy import func # Ensure it is case-insensitive the search term.

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Shows(db.Model):
    __tablename__ = 'shows'
    artist_id = db.Column(db.Integer(), db.ForeignKey('artist.id'),primary_key=True)
    venue_id = db.Column(db.Integer(), db.ForeignKey('venue.id'),primary_key=True)
    start_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))


    def __repr__(self):
        return f"\n<Venue\n 'id :'{self.id}\n 'name :' {self.name}\n 'city :' {self.city}\n 'state :'{self.state}>"


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))

    venues = db.relationship('Venue', secondary='shows', backref=db.backref('artists', lazy=True))

    def __repr__(self):
        return f"\n<Artist\n 'id :'{self.id}\n 'name :' {self.name}\n 'city :' {self.city}\n 'state :'{self.state}>"


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  allVenue = db.session.execute('select DISTINCT city, state from venue;').fetchall()
  
  for v in allVenue:    
      mydata = {}
      mydata['city'] = v.city
      mydata['state'] = v.state
      mydata['venues'] = []
      venues = Venue.query.filter_by(state=v.state,city=v.city).all()
      for venue in venues:
        myVenue = {}
        myVenue["id"] = venue.id
        myVenue["name"] = venue.name
        myVenue["num_upcoming_shows"] = db.session.execute('select count(venue_id) from shows where venue_id='+ str(venue.id) 
                +' and start_date > CURRENT_TIMESTAMP;').fetchone()[0]
        mydata['venues'].append(myVenue)
      data.append(mydata)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_word = request.form.get('search_term', '')
  resp = Venue.query.filter(func.lower(Venue.name).contains( search_word.lower() )).all()
  response = {}
  response['count'] = len(resp)
  response['data'] = [] 
  for d in resp: 
    myVenue = {}
    myVenue["id"] = d.id
    myVenue["name"] = d.name
    myVenue["num_upcoming_shows"] = db.session.execute('select count(venue_id) from shows where venue_id='+ str(d.id) 
                  +' and start_date > CURRENT_TIMESTAMP;').fetchone()[0]
    response['data'].append(myVenue)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue :
    form = VenueForm()
    flash('Venue of id ' + str(venue_id) + ' does not exist create NEW Venue here !')
    return render_template('forms/new_venue.html', form=form)


  mydata = {}
  mydata['id'] = venue.id
  mydata['name'] = venue.name
  mydata['genres'] = venue.genres
  mydata['address'] = venue.address
  mydata['city'] = venue.city
  mydata['state'] = venue.state
  mydata['phone'] = venue.phone
  mydata['website'] = venue.website
  mydata['facebook_link'] = venue.facebook_link
  mydata['seeking_description'] = venue.seeking_description
  mydata['image_link'] = venue.image_link
  mydata['upcoming_shows'] = []
  mydata['past_shows'] = []
  pastShows = db.session.execute('select artist_id,start_date from shows where venue_id='+ str(venue_id) +' and start_date < CURRENT_TIMESTAMP;').fetchall()
  upShows = db.session.execute('select artist_id,start_date  from shows where venue_id='+ str(venue_id) +' and start_date > CURRENT_TIMESTAMP;').fetchall()
  
  for past_show in pastShows:
      ps = {}
      ps['artist_id'] = past_show['artist_id']
      ps['artist_name'] = Artist.query.get(past_show['artist_id']).name
      ps['artist_image_link'] = Artist.query.get(past_show['artist_id']).image_link
      ps['start_time'] = past_show['start_date']
      mydata['past_shows'].append(ps)

  for up_artist_id in upShows: 
      ups = {}
      ups['artist_id'] = up_artist_id['artist_id']
      ups['artist_name'] = Artist.query.get(up_artist_id['artist_id']).name
      ups['artist_image_link'] = Artist.query.get(up_artist_id['artist_id']).image_link
      ups['start_time'] = up_artist_id['start_date']
      mydata['upcoming_shows'].append(ups)    

  mydata['past_shows_count'] = len(pastShows)
  mydata['upcoming_shows_count'] =len(upShows)

  return render_template('pages/show_venue.html', venue=mydata)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  newVenue = Venue(name=request.form['name'],city=request.form['city'],state=request.form['state'],
              address=request.form['address'],phone=request.form['phone'],genres=request.form['genres'],
              facebook_link=request.form['facebook_link'])

  try:
    db.session.add(newVenue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was Unsuccessfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.!')
      
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  if not Venue.query.get(venue_id) :
    flash('Venue of id ' + str(venue_id) + ' does not exist To delete it')
    return render_template('pages/home.html')

  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_word = request.form.get('search_term', '')
  
  resp = Artist.query.filter(func.lower(Artist.name).contains(search_word.lower())).all()
  response = {}
  response['count'] = len(resp)
  response['data'] = [] 
  for d in resp: 
    myArtist = {}
    myArtist["id"] = d.id
    myArtist["name"] = d.name
    myArtist["num_upcoming_shows"] = db.session.execute('select count(artist_id) from shows where artist_id='+ str(d.id) +' and start_date > CURRENT_TIMESTAMP;').fetchone()[0]
    
    response['data'].append(myArtist)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  artist = Artist.query.get(artist_id)
  if not artist :
    form = ArtistForm()
    flash('Artist of id ' + str(artist_id) + ' does not exist create NEW Artist here !')
    return render_template('forms/new_artist.html', form=form)

  mydata = {}
  mydata['id'] = artist.id
  mydata['name'] = artist.name
  if artist.genres : mydata['genres'] = artist.genres
  mydata['city'] = artist.city
  mydata['state'] = artist.state
  mydata['phone'] = artist.phone
  # mydata['website'] = artist.website
  mydata['facebook_link'] = artist.facebook_link
  if artist.seeking_description:
    mydata['seeking_talent'] = True
    mydata['seeking_description'] = artist.seeking_description

  mydata['image_link'] = artist.image_link
  mydata['upcoming_shows'] = []
  mydata['past_shows'] = []
  pastShows = db.session.execute('select venue_id, start_date from shows where artist_id='+ str(artist_id) +' and start_date < CURRENT_TIMESTAMP;').fetchall()
  upShows = db.session.execute('select venue_id, start_date from shows where artist_id='+ str(artist_id) +' and start_date > CURRENT_TIMESTAMP;').fetchall()

  for past_show in pastShows:
      ps = {}
      ps['venue_id'] = past_show['venue_id']
      ps['venue_name'] = Venue.query.get(past_show['venue_id']).name
      ps['venue_image_link'] = Venue.query.get(past_show['venue_id']).image_link
      ps['start_time'] = past_show['start_date']
      mydata['past_shows'].append(ps)

  for up_venue_id in upShows: 
      ups = {}
      ups['venue_id'] = up_venue_id['venue_id']
      ups['venue_name'] = Venue.query.get(up_venue_id['venue_id']).name
      ups['venue_image_link'] = Venue.query.get(up_venue_id['venue_id']).image_link
      ups['start_time'] = up_venue_id['start_date']
      mydata['upcoming_shows'].append(ups)    

  mydata['past_shows_count'] = len(pastShows)
  mydata['upcoming_shows_count'] = len(upShows)
  
  return render_template('pages/show_artist.html', artist=mydata)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)
  if not artist :
     flash('Artist of id ' + str(artist_id) + ' does not exist create NEW Artist here !')
     return render_template('forms/new_artist.html', form=form)

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes

  artist = Artist.query.get(artist_id)
  artist.name = request.form['name']
  artist.genres = request.form['genres']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  # artist.website = request.form['website']
  artist.facebook_link = request.form['facebook_link']
  # artist.image_link = request.form['image_link']
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully Updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be Updated.')

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)
  if not venue :
     flash('Venue of id ' + str(venue_id) + ' does not exist create NEW Venue here !')
     return render_template('forms/new_venue.html', form=form)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.genres = request.form['genres']
  venue.city = request.form['city']
  venue.address = request.form['address']
  venue.state = request.form['state']
  venue.phone = request.form['phone']
  # venue.website = request.form['website']
  venue.facebook_link = request.form['facebook_link']
  # venue.image_link = request.form['image_link']

  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully Updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be Updated.')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  newArtist = Artist(name=request.form['name'],city=request.form['city'],state=request.form['state'],
              phone=request.form['phone'],genres=request.form['genres'],
              facebook_link=request.form['facebook_link'])
  try:
    db.session.add(newArtist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + newArtist.name + ' could not be listed.')
    
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows_ = db.session.execute('select venue_id, artist_id, start_date from shows;').fetchall()
  for show in shows_:
    myShow ={}
    myShow['venue_id'] = show.venue_id
    myShow['venue_name'] = Venue.query.get(show.venue_id).name
    myShow['artist_id'] = show.artist_id
    myShow['artist_name'] = Artist.query.get(show.artist_id).name
    myShow['artist_image_link'] = Artist.query.get(show.artist_id).image_link
    myShow['start_time'] = show.start_date
    data.append(myShow)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    # on successful db insert, flash success
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_date = request.form['start_time']
    db.session.execute("INSERT INTO shows (artist_id, venue_id, start_date) VALUES("+ artist_id +","+ venue_id +",'"+ start_date +"');")
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
