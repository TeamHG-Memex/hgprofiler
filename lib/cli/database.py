import logging
import os
import shutil
import subprocess
import sys

from sqlalchemy.engine import reflection
from sqlalchemy.schema import (DropConstraint,
                               DropTable,
                               ForeignKeyConstraint,
                               MetaData,
                               Table)
from app.config import get_path
import app.database
import cli
from model import Base, Configuration, User, Site, File
import model.user


class DatabaseCli(cli.BaseCli):
    ''' A tool for initializing the database. '''

    def _agnostic_bootstrap(self, config):
        ''' Bootstrap the Agnostic migrations system. '''

        env = {
            'AGNOSTIC_TYPE': 'postgres',
            'AGNOSTIC_HOST': config.get('database', 'host'),
            'AGNOSTIC_USER': config.get('database', 'super_username'),
            'AGNOSTIC_PASSWORD': config.get('database', 'super_password'),
            'AGNOSTIC_DATABASE': config.get('database', 'database'),
            'AGNOSTIC_MIGRATIONS_DIR': get_path('migrations'),
            'LANG': os.environ['LANG'],  # http://click.pocoo.org/4/python3/
            'PATH': os.environ['PATH'],
        }

        process = subprocess.Popen(
            ['agnostic', 'bootstrap'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env
        )
        process.wait()

        if process.returncode != 0:
            args = (process.returncode, process.stderr.read().decode('ascii'))
            self._logger.error('External process `agnostic bootstrap` failed '
                               'with error code (%d):\n%s' % args)
            sys.exit(1)

    def _create_fixtures(self, config):
        ''' Create fixture data. '''

        self._create_fixture_configurations(config)
        self._create_fixture_images(config)
        self._create_fixture_users(config)
        self._create_fixture_sites(config)

    def _create_fixture_configurations(self, config):
        ''' Create configurations. '''

        session = app.database.get_session(self._db)

        for key, value in config.items('config_table'):
            session.add(Configuration(key, value))

        session.commit()

    def _create_fixture_images(self, config):
        '''
        Create the generic error image.

        Since this script will often run as root, it modifies the owner of the
        new file to match the owner of the data directory.
        '''

        session = app.database.get_session(self._db)

        image_name = 'hgprofiler_error.png'
        data_stat = os.stat(get_path('data'))
        img_path = os.path.join(get_path('static'), 'img', image_name)
        with open(img_path, 'rb') as img:
            img_data = img.read()
            image_file = File(name=image_name, mime='image/png',
                              content=img_data)
            image_file.chown(data_stat.st_uid, data_stat.st_gid)
            session.add(image_file)

        session.commit()

    def _create_fixture_users(self, config):
        ''' Create user fixtures. '''

        session = app.database.get_session(self._db)
        hash_algorithm = config.get('password_hash', 'algorithm')

        try:
            hash_rounds = int(config.get('password_hash', 'rounds'))
        except:
            raise ValueError('Configuration value password_hash.rounds must'
                             ' be an integer: %s' % hash_rounds)

        admin = User('admin')
        admin.agency = 'Profiler'
        admin.name = 'Administrator'
        admin.is_admin = True
        admin.password_hash = model.user.hash_password(
            'MemexPass1',
            hash_algorithm,
            hash_rounds
        )
        session.add(admin)
        session.commit()

    def _create_fixture_sites(self, config):
        ''' Create site fixtures. '''

        session = app.database.get_session(self._db)

        # about.me
        about_me = Site(
            name='About.me',
            url='http://about.me/%s',
            category='social',
            status_code=200,
            search_text='g.PAGE_USER_NAME =',
            test_username_pos='bob'
        )
        session.add(about_me)

        # anobii
        anobii = Site(
            name='Anobii',
            url='http://www.anobii.com/%s/books',
            category='books',
            status_code=200,
            search_text='- aNobii</title>"',
            test_username_pos='bob'
        )
        session.add(anobii)

        # ask.fm
        ask_fm = Site(
            name='Ask FM',
            url='http://ask.fm/%s',
            category='social',
            status_code=200,
            search_text='| ask.fm/',
            test_username_pos='tipsofschool'
        )
        session.add(ask_fm)

        # audioboom
        audioboom = Site(
            name='Audioboom',
            url='http://audioboom.com/%s',
            category='music',
            status_code=200,
            search_text='<title>audioBoom / ',
            test_username_pos='bob'
        )
        session.add(audioboom)

        # audioboom
        authorstream = Site(
            name='Authorstream',
            url='http://www.authorstream.com/%s/',
            category='social',
            status_code=200,
            search_text='Presentations on authorSTREAM',
            test_username_pos='tiikmconferences'
        )
        session.add(authorstream)

        # badoo
        badoo = Site(
            name='Badoo',
            url='http://badoo.com/%s/',
            category='dating',
            status_code=200,
            search_text='| Badoo</title>',
            test_username_pos='dave'
        )
        session.add(badoo)

        # behance
        behance = Site(
            name='Behance',
            url='https://www.behance.net/%s',
            category='social',
            status_code=200,
            search_text=' on Behance\" />',
            test_username_pos='juste'
        )
        session.add(behance)

        # bitbucket
        bitbucket = Site(
            name='Bitbucket',
            url='https://bitbucket.org/%s',
            category='coding',
            status_code=200,
            search_text='\"username\": ',
            test_username_pos='jespern'
        )
        session.add(bitbucket)

        # blinklist
        blip_fm = Site(
            name='Blip FM',
            url='http://blip.fm/%s',
            category='music',
            status_code=200,
            search_text='<title>Free Music | Listen to Music Online |',
            test_username_pos='mark_till'
        )
        session.add(blip_fm)

        session.commit()

    # def _create_fixture_sites(self, config):
    #     ''' Create site fixtures. '''

    #     session = app.database.get_session(self._db)
    #     sample_dir = os.path.join(os.path.dirname(__file__), 'sample-data')
    #     json_file_path = os.path.join(sample_dir, 'profiler_sites.json')

    #     with open(json_file_path) as json_file:
    #         json_data = json.load(json_file)
    #         json_sites = json_data['sites']

    #         for json_site in json_sites:
    #             site = Site(
    #                 name=json_site['r'],
    #                 url=json_site['u'],
    #                 category=json_site['c'],
    #                 status_code=json_site['gRC'],
    #                 search_text=json_site['gRT']
    #             )

    #             session.add(site)

    #     session.commit()
    # def _create_fixture_sites(self, config):
    #     ''' Create site fixtures. '''

    #     session = app.database.get_session(self._db)
    #     sample_dir = os.path.join(os.path.dirname(__file__), 'sample-data')
    #     json_file_path = os.path.join(sample_dir, 'profiler_sites.json')

    #     with open(json_file_path) as json_file:
    #         json_data = json.load(json_file)
    #         json_sites = json_data['sites']

    #         for json_site in json_sites:
    #             site = Site(
    #                 name=json_site['r'],
    #                 url=json_site['u'],
    #                 category=json_site['c'],
    #                 status_code=json_site['gRC'],
    #                 search_text=json_site['gRT']
    #             )

    #             session.add(site)

    #     session.commit()

    def _delete_data(self):
        ''' Delete files stored in the data directory. '''
        data_dir = get_path("data")
        for file_object in os.listdir(data_dir):
            file_object_path = os.path.join(data_dir, file_object)
            if os.path.isfile(file_object_path):
                os.unlink(file_object_path)
            else:
                shutil.rmtree(file_object_path)

    def _drop_all(self):
        '''
        Drop database tables, foreign keys, etc.

        Unlike SQL Alchemy's built-in drop_all() method, this one shouldn't
        punk out if the Python schema doesn't match the actual database schema
        (a common scenario while developing).

        See:
        https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DropEverything
        '''

        tables = list()
        all_fks = list()
        metadata = MetaData()
        inspector = reflection.Inspector.from_engine(self._db)
        session = app.database.get_session(self._db)

        for table_name in inspector.get_table_names():
            fks = list()

            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(ForeignKeyConstraint((), (), name=fk['name']))

            tables.append(Table(table_name, metadata, *fks))
            all_fks.extend(fks)

        for fk in all_fks:
            try:
                self._db.execute(DropConstraint(fk))
            except Exception as e:
                self._logger.warn('Not able to drop FK "%s".' % fk.name)
                self._logger.debug(str(e))

        for table in tables:
            try:
                self._db.execute(DropTable(table))
            except Exception as e:
                self._logger.warn('Not able to drop table "%s".' % table.name)
                self._logger.debug(str(e))

        session.commit()

    def _get_args(self, arg_parser):
        ''' Customize arguments. '''

        arg_parser.add_argument(
            'action',
            choices=('build', 'drop'),
            help='Specify what action to take.'
        )

        arg_parser.add_argument(
            '--debug-db',
            action='store_true',
            help='Print database queries.'
        )

        arg_parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample data.'
        )

        arg_parser.add_argument(
            '--delete-data',
            action='store_true',
            help='Delete archive and screenshot files from data directory.'
        )

    def _run(self, args, config):
        ''' Main entry point. '''

        if args.debug_db:
            # Configure database logging.
            log_level = getattr(logging, args.verbosity.upper())

            db_logger = logging.getLogger('sqlalchemy.engine')
            db_logger.setLevel(log_level)
            db_logger.addHandler(self._log_handler)

        # Connect to database.
        database_config = dict(config.items('database'))
        self._db = app.database.get_engine(database_config, super_user=True)

        # Run build commands.
        if args.action in ('build', 'drop'):
            self._logger.info('Dropping database tables.')
            self._drop_all()

            if args.delete_data:
                self._logger.info('Deleting data.')
                self._delete_data()

        if args.action == 'build':
            self._logger.info('Running Agnostic\'s bootstrap.')
            self._agnostic_bootstrap(config)

            self._logger.info('Creating database tables.')
            Base.metadata.create_all(self._db)

            self._logger.info('Creating fixture data.')
            self._create_fixtures(config)

        if args.action == 'build' and args.sample_data:
            self._logger.info('Creating sample data.')
            self._create_samples(config)
