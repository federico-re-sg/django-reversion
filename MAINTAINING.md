# SpeedGauge fork maintenance

This fork is consumed by Insurance. Its upstream base is `v6.3.0` and its
package version is `6.3.0+sg.1`. Tiering/Mars does not consume this fork.

## Retained custom behavior

`Revision.user` is a nullable integer, without a foreign key. Insurance started
deleting users rather than deactivating them in RMP-181; storing the ID preserves
historical attribution independently of the user's continued existence.
The change is recorded in commits `1b2da2c` and `f2c8761`, followed by fixes
`f3e129c` and `931a86d`.

`set_user()` still receives a user object and `get_user()` returns that object
inside an active revision. Only persistence converts it to `user.id` or `None`.
Direct assignment to `Revision.user` uses an integer. There is no ORM user
relation or automatic user lookup.

The deployed `0003_alter_revision_user` migration is retained unchanged. The
field label is explicitly `insurance.User`, matching its migration state even
when the test project uses Django's default auth model. Admin history loads the
revision without joining its integer user field. Its presentation is unchanged;
this upgrade does not add user-name resolution.

The `remote_field.hidden` compatibility fix is already present in upstream.
Upstream tests that expect a persisted user object instead assert its ID through
the shared helper. The API tests still assert that `get_user()` returns the object.

## Future updates

1. Fetch upstream tags and create a branch from the current fork release.
2. Merge a stable upstream tag, keeping the integer field, conversion, migration
   identity, and admin query adaptation. Do not rebase published fork history.
3. Advance the upstream base and local package version in this document and
   `reversion/__init__.py`. Keep the local version suffix to distinguish the fork.
4. Review upstream migrations and all code that accesses revision users. Never
   rename or rewrite an already deployed customization migration.
5. Run the checks below and exercise an upgrade from Insurance's previous pinned
   commit on a temporary database containing historical revisions.
6. Publish the reviewed fork commit before updating Insurance. Pin the full SHA
   using `rev` in its Git dependency and regenerate its lock without unrelated
   dependency upgrades. Git dependencies do not require a PyPI release.

## Validation

Use disposable local SQLite, PostgreSQL, and MySQL/MariaDB test databases and the
CI environment variables in `.github/workflows/python-package.yml`. Database
names must be dedicated to the test run; the suite creates and destroys test DBs.

```sh
flake8
python tests/manage.py makemigrations --check --dry-run
coverage run tests/manage.py test tests --noinput
coverage report
cd docs
sphinx-build -n -W . _build
```

The suite covers integer attribution after user deletion, anonymous revisions,
nested contexts, transaction rollback, metadata, admin history/revert/recovery,
GET signal suppression and POST signal behavior. Migration tests preserve
historical data across the foreign-key-to-integer conversion on SQLite and
PostgreSQL. CI retains the upstream supported Python/Django matrix.

For upgrade validation, create revisions with a user and without one under the
previous fork commit, delete the author, and capture the rows from Revision and
Version. Install the new fork, migrate, compare those rows byte-for-byte (including
serialized data), and verify historical access, revert/recovery, and new writes.
Repeat historical access and writes with the old code to validate rollback.

## Rollback

This release retains the integer schema and the existing customization migration;
upstream changes to the initial migration only add model display metadata.
No new database operation is required by the reversion app for an already
migrated Insurance database. Revert Insurance's dependency declaration and lock
together to the previous pinned commit, then rebuild the application. Do not
unapply `0003_alter_revision_user`: that would restore a foreign key incompatible
with historical IDs of deleted users. Future releases with database changes need
their own verified rollback procedure.
