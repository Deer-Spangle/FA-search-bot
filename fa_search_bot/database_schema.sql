


create table if not exists cache_entries
(
    site_code             TEXT    not null,
    submission_id         TEXT    not null,
    is_photo              BOOLEAN not null,
    media_id              INTEGER not null,
    access_hash           INTEGER not null,
    file_url              TEXT    not null,
    caption               TEXT    not null,
    cache_date            DATE    not null
);

create unique index if not exists cache_entries_site_code_submission_id_uindex
    on cache_entries (site_code, submission_id);
