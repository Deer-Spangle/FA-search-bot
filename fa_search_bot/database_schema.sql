


create table if not exists cache_entries
(
    site_code             TEXT    not null,
    submission_id         TEXT    not null,
    is_photo              BOOLEAN not null,
    media_id              INTEGER not null,
    access_hash           INTEGER not null,
    file_url              TEXT,
    caption               TEXT    not null,
    cache_date            DATE    not null,
    full_image            BOOLEAN not null  -- If false, this cache is only for inline results
);

create unique index if not exists cache_entries_site_code_submission_id_uindex
    on cache_entries (site_code, submission_id);
