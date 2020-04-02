-- for get the number of shows of every venue
SELECT venue.id, venue.name , venue.city, venue.state, numberShows
    FROM venue left join (
      SELECT venue_id, count(venue_id) AS numberShows
      FROM shows
      GROUP BY venue_id ) AS st
      ON venue.id = st.venue_id ;

 -- for get the number of shows of every venue AND it Artist
SELECT venue.id, venue.name , venue.city, venue.state, numberShows, astist_name
FROM venue left join (
    SELECT venue_id, count(venue_id) AS numberShows,ar_table.astist_name
    FROM (shows left join (
        SELECT id, artist.name AS astist_name
        FROM artist 
        ) AS ar_table
        ON shows.artist_id = ar_table.id )
    GROUP BY venue_id ) AS st
ON venue.id = st.venue_id ;     
--
SELECT venue.id, venue.name , venue.city, venue.state, artist_name
FROM venue left join (
      SELECT venue_id, artist_name
      FROM shows left join (
            SELECT id , name AS artist_name
            FROM artist 
      ) AS art_table
        ON shows.artist_id = art_table.id
     ) AS st
      ON venue.id = st.venue_id ;
      --
select venue.city, venue.state ,count(shows.venue_id) 
from venue left join shows 
on venue.id = shows.venue_id 
group by venue.id;
-- for select count o venue upcoming
a = db.session.execute('select count(venue_id) from shows where venue_id=? and starttime>timeOfNow;').fetchone()[0]
a = db.session.execute('SELECT venue.id, venue.name , venue.city, venue.state, numberShows FROM venue left join (SELECT venue_id, count(venue_id) AS numberShows FROM shows GROUP BY venue_id ) AS st ON venue.id = st.venue_id ;')

             {# {% set place='' %}
              {% if artist.city %} 
              {% set place='ThereCity' %}
              {% else %} 
              {% set place='City' %}
              {% endif %}#}