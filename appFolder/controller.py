from datetime import datetime
from flask import render_template, request, flash, redirect, url_for
from sqlalchemy import func
from appFolder import app, db
from appFolder.forms import *
from appFolder.model import *
import dateutil.parser
import babel


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venues = Venue.query.order_by(Venue.city, Venue.state).all()
    c_vs = set()
    for venue in venues:
        c_vs.add((venue.city, venue.state))
    c_vs = list(c_vs)
    data = []
    for c_v in c_vs:
        city, state = c_v
        venuess = []
        for venue in venues:
            if venue.city == city and venue.state == state:
                v = Show.query.filter(Show.venue_id == venue.id).all()
                num_upcoming_shows = 0
                n_t = datetime.now()
                for show in v:
                    if show.start_time > n_t:
                        num_upcoming_shows += 1

                venuess.append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows
                })
        data.append({
            "city": city,
            "state": state,
            "venues": venuess
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    count = len(venues)
    data = []
    for venue in venues:
        number_upcoming_shows = 0
        shows = Show.query.filter(Show.venue_id == venue.id).all()
        n_t = datetime.now()
        for show in shows:
            if show.start_time > n_t:
                number_upcoming_shows += 1
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": number_upcoming_shows
        })
    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    v_s = db.session.query(Venue).join(
        Show, Venue.id == Show.venue_id).filter(Venue.id == venue_id).all()
    # venue = Venue.query.get(venue_id)
    # shows = Show.query.filter(Show.venue_id == venue_id).all()
    past_shows = []
    upcoming_shows = []
    n_t = datetime.now()
    for ele in v_s:
        if ele.start_time > n_t:
            upcoming_shows.append({
                "artist_id": ele.artist_id,
                "artist_name": ele.artist.name,
                "artist_image_link": ele.artist.image_link,
                "start_time": format_datetime(str(ele.start_time))
            })
        else:
            past_shows.append({
                "artist_id": ele.artist_id,
                "artist_name": ele.artist.name,
                "artist_image_link": ele.artist.image_link,
                "start_time": format_datetime(str(ele.start_time))
            })
    ps_count = len(past_shows)
    us_count = len(upcoming_shows)
    data = {
        "id": v_s.id,
        "name": v_s.name,
        "genres": v_s.genres,
        "address": v_s.address,
        "city": v_s.city,
        "state": v_s.state,
        "phone": v_s.phone,
        "website": v_s.website_link,
        "facebook_link": v_s.facebook_link,
        "seeking_talent": v_s.seeking_talent,
        "seeking_description": v_s.seeking_description,
        "image_link": v_s.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_data": ps_count,
        "upcoming_shows_data": us_count
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()

    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    # genres = request.form.getlist('genres')
    genres = form.genres.data
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_talent = request.form['seeking_talent']
    seeking_description = request.form['seeking_description']

    # to validate that input is correct
    if not form.validate_on_submit():
        flash('Please fill out all fields correctly')
        return redirect(url_for('create_venue_form'))
    else:
        try:
            venue = Venue(name=name, city=city, state=state, address=address,
                          phone=phone, genres=genres, image_link=image_link,
                          facebook_link=facebook_link, website=website_link,
                          seeking_talent=seeking_talent,
                          seeking_description=seeking_description)
            db.session.add(venue)
            db.session.commit()
        except:
            db.session.rollback()
            flash(f'An error occurred. {name} could not be listed.')
            print(sys.exc_info())
        finally:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
            db.session.close()
            return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    try:
        db.session.delete(venue)
        db.session.commit()
        flash('Venue deleted successfully')
    except:
        db.session.rollback()
        flash('An error occurred. Venue could not be deleted.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    # data = [{
    #     "id": 4,
    #     "name": "Guns N Petals",
    # }, {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    # }, {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    # }]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    count = len(artists)
    data = []
    for artist in artists:
        num_upcoming_shows = 0
        n_t = datetime.now()
        shows = Show.query.filter(Show.artist_id == artist.id).all()
        for show in shows:
            if show.start_time > n_t:
                num_upcoming_shows += 1
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(artist.shows)
        })
    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    a_s = db.session.query(Artist).join(
        Show, Artist.id == Show.artist_id).filter(Artist.id == artist_id).all()

    # artist = Artist.query.get(artist_id)
    # so_artist = Show.query.filter(Show.artist_id == artist_id).all()
    past_show = []
    upcoming_show = []
    for ele in a_s:
        n_t = datetime.now()
        if ele.start_time > n_t:
            upcoming_show.append({
                "venue_id": ele.venue_id,
                "venue_name": ele.venue.name,
                "venue_image_link": ele.venue.image_link,
                "start_time": format_datetime(str(ele.start_time))
            })
        else:
            past_show.append({
                "venue_id": ele.venue_id,
                "venue_name": ele.venue.name,
                "venue_image_link": ele.venue.image_link,
                "start_time": format_datetime(str(ele.start_time))
            })
        us_count = len(upcoming_show)
        ps_count = len(past_show)
    data = {
        "id": a_s.id,
        "name": a_s.name,
        "genres": a_s.genres,
        "city": a_s.city,
        "state": a_s.state,
        "phone": a_s.phone,
        "website": a_s.website_link,
        "facebook_link": a_s.facebook_link,
        "seeking_venue": a_s.seeking_venue,
        "seeking_description": a_s.seeking_description,
        "image_link": a_s.image_link,
        "past_shows": past_show,
        "upcoming_shows":  upcoming_show,
        "past_shows_count": ps_count,
        "upcoming_shows_count": us_count
    }

    return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()

    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    image_link = request.form['image_link']
    seeking_venue = request.form['seeking_venue']
    seeking_description = request.form['seeking_description']

    # city = form.city.data
    # state = form.state.data
    # phone = form.phone.data
    # genres = form.genres.data
    # facebook_link = form.facebook_link.data
    # image_link = form.image_link.data
    # website_link = form.website_link.data
    # seeking_venue = form.seeking_venue.data
    # seeking_description = form.seeking_description.data

    if not form.validate_on_submit():
        flash('Pease fill out all the fields correctly')
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        try:
            artist = Artist.query.get(artist_id)
            artist.name = name
            artist.city = city
            artist.state = state
            artist.phone = phone
            artist.genres = genres
            artist.facebook_link = facebook_link
            artist.image_link = image_link
            artist.website_link = website_link
            artist.seeking_venue = seeking_venue
            artist.seeking_description = seeking_description
            db.session.commit()
        except:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be updated.')
            db.session.rollback()
            print(sys.exc_info())
            abort(500)
        finally:
            flash('Artist ' + request.form['name'] +
                  ' was successfully updated!')
            db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    form = VenueForm()
    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = request.form['seeking_talent']
        venue.seeking_description = request.form['seeking_description']
        venue.image_link = request.form['image_link']
        db.session.commit()
    except:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
        db.session.rollback()
        print(sys.exc_info())
        abort(500)
    finally:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data

    if not form.validate():
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        return redirect(url_for('create_artist_form'))
    else:
        try:
            Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link,
                   website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
            db.session.commit()
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' +
                  name + ' could not be listed.')
            print(sys.exc_info())
            abort(500)
        finally:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
            db.session.close()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')

#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    form = ShowForm()
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    if not form.validate():
        flash('An error occurred. Show could not be listed.')
        return redirect(url_for('create_shows'))
    else:
        try:
            n_s = Show(artist_id=artist_id, venue_id=venue_id,
                       start_time=start_time)
            db.session.add(n_s)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
            print(sys.exc_info())
        finally:
            db.session.close()
    flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
