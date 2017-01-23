CREATE TABLE scrobbles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token_id integer NULL,
    created_at timestamp with time zone NOT NULL,
    played_at timestamp with time zone NOT NULL,
    artist character varying(255) NOT NULL,
    artist_id integer,
    track character varying(255) NOT NULL,
    track_id integer,
    album character varying(255),
    album_id integer,
    tracknumber character varying(255),
    length interval NOT NULL,
    musicbrainz character varying(255),
    source character varying(255),
    rating character varying(255)
);

CREATE SEQUENCE scrobbles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
;

ALTER SEQUENCE scrobbles_id_seq OWNED BY scrobbles.id;
ALTER TABLE ONLY scrobbles ALTER COLUMN id SET DEFAULT nextval('scrobbles_id_seq'::regclass);
ALTER TABLE ONLY scrobbles ADD CONSTRAINT scrobbles_pkey PRIMARY KEY (id);
ALTER TABLE ONLY scrobbles ADD CONSTRAINT scrobbles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE ONLY scrobbles ADD CONSTRAINT scrobbles_token_id_fkey FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE SET NULL;
ALTER TABLE ONLY scrobbles ADD CONSTRAINT scrobbles_artist_id_fkey FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE SET NULL;

CREATE INDEX scrobbles_user_id_idx ON scrobbles USING btree (user_id);
CREATE INDEX scrobbles_artist_id_idx ON scrobbles USING btree (artist_id);
CREATE INDEX scrobbles_artist_idx ON scrobbles USING btree (lower((artist)::text));
CREATE INDEX scrobbles_played_at_idx ON scrobbles USING btree (played_at);
CREATE INDEX scrobbles_track_idx ON scrobbles USING btree (lower((track)::text));
CREATE UNIQUE INDEX scrobbles_unique_idx ON scrobbles (played_at, artist, track);

CREATE INDEX np_played_at_idx ON np USING btree (played_at);
CREATE INDEX np_user_id_idx ON np USING btree (user_id);
