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

        # blip fm
        blip_fm = Site(
            name='Blip FM',
            url='http://blip.fm/%s',
            category='music',
            status_code=200,
            search_text='<title>Free Music | Listen to Music Online |',
            test_username_pos='mark_till'
        )
        session.add(blip_fm)

        # blogmarks
        blogmarks = Site(
            name='Blogmarks',
            url='http://blogmarks.net/user/%s',
            category='social',
            status_code=200,
            search_text='<title>Blogmarks : Public marks from',
            test_username_pos='Krome'
        )
        session.add(blogmarks)

        # blogspot
        blogspot = Site(
            name='Blogspot',
            url='http://%s.blogspot.co.uk',
            category='social',
            status_code=200,
            search_text='Blogger Template Style',
            test_username_pos='takingroot-jr'
        )
        session.add(blogspot)

        # bodybuilding
        bodybuilding = Site(
            name='Bodybuilding',
            url='http://bodyspace.bodybuilding.com/%s/',
            category='health',
            status_code=200,
            search_text='s BodySpace - Bodybuilding.com</title>',
            test_username_pos='Scarfdaddy'
        )
        session.add(bodybuilding)

        # break
        break_com = Site(
            name='Break',
            url='http://www.break.com/user/%s',
            category='video',
            status_code=200,
            search_text=' | Break.com</title>',
            test_username_pos='jenny'
        )
        session.add(break_com)

        # cafemom
        cafemom = Site(
            name='Cafemom',
            url='http://www.cafemom.com/home/%s',
            category='social',
            status_code=200,
            search_text='h3 id="profile-user',
            test_username_pos='jane'
        )
        session.add(cafemom)

        # cardomain
        car_domain = Site(
            name='Car Domain',
            url='http://www.cardomain.com/member/%s/',
            category='automotive',
            status_code=200,
            search_text='s Profile in',
            test_username_pos='dan'
        )
        session.add(car_domain)

        # codeplex
        codeplex = Site(
            name='Codeplex',
            url='http://www.codeplex.com/site/users/view/%s',
            category='coding',
            status_code=200,
            search_text='property="profile:username" />',
            test_username_pos='dan'
        )
        session.add(codeplex)

        # colour lovers
        colour_lovers = Site(
            name='Colour Lovers',
            url='http://www.colourlovers.com/lover/%s',
            category='art and design',
            status_code=200,
            search_text='var repos = [{"',
            test_username_pos='bob'
        )
        session.add(colour_lovers)

        # conferize
        conferize = Site(
            name='Conferize',
            url='https://www.conferize.com/u/%s/',
            category='business',
            status_code=200,
            search_text='| Conferize - Never miss a Conference</title>',
            test_username_pos='dan'
        )
        session.add(conferize)

        # copytaste
        copy_taste = Site(
            name='Copytaste',
            url='http://copytaste.com/profile/%s',
            category='social',
            status_code=200,
            search_text=' property="og:title" content="',
            test_username_pos='metegulec'
        )
        session.add(copy_taste)

        # cruisemates
        cruisemates = Site(
            name='Cruisemates',
            url='http://www.cruisemates.com/forum/members/%s.html',
            category='travel',
            status_code=200,
            search_text='- View Profile: ',
            test_username_pos='trip'
        )
        session.add(cruisemates)

        # Dailymotion
        daily_motion = Site(
            name='Dailymotion',
            url='http://www.dailymotion.com/%s',
            category='Video',
            status_code=200,
            search_text=' - Dailymotion</title>',
            test_username_pos='fanreviews'
        )
        session.add(daily_motion)

        # Delicous
        delicious = Site(
            name='Delicious',
            url='https://del.icio.us/%s',
            category='Social',
            status_code=200,
            search_text='<h2>Username:',
            test_username_pos='john'
        )
        session.add(delicious)

        # DeviantArt
        deviant_art = Site(
            name='DeviantArt',
            url='http://%s.deviantart.com/',
            category='image',
            status_code=200,
            search_text='s Journal"',
            test_username_pos='marydoodles'
        )
        session.add(deviant_art)

        # Diigo
        diigo = Site(
            name='Diigo',
            url='https://www.diigo.com/profile/%s',
            category='bookmarking',
            status_code=200,
            search_text=' Public Profile in the Diigo Community</title>',
            test_username_pos='hunter53'
        )
        session.add(diigo)

        # Disqus
        disqus = Site(
            name='Disqus',
            url='https://disqus.com/by/%s/',
            category='social',
            status_code=200,
            search_text='Disqus Profile - ',
            test_username_pos='willwillibe'
        )
        session.add(disqus)

        # DIY
        diy = Site(
            name='DIY',
            url='https://diy.org/%s',
            category='home improvement',
            status_code=200,
            search_text='iphone\" content=\"diy://diy.org/',
            test_username_pos='bob'
        )
        session.add(diy)

        # Dribble
        dribble = Site(
            name='Dribble',
            url='https://www.dribbble.com/%s',
            category='art and design',
            status_code=200,
            search_text='<div class="profile-info ">',
            test_username_pos='kirp'
        )
        session.add(dribble)

        # Ebay
        ebay = Site(
            name='Ebay',
            url='http://www.ebay.com/usr/%s',
            category='shopping',
            status_code=200,
            search_text='on eBay</title>',
            test_username_pos='max'
        )
        session.add(ebay)

        # Etsy
        etsy = Site(
            name='Etsy',
            url='https://www.etsy.com/people/%s',
            category='shopping',
            status_code=200,
            search_text=' on Etsy</title>',
            test_username_pos='betsy'
        )
        session.add(etsy)

        # Families
        families = Site(
            name='Families',
            url='http://www.families.com/author/%s',
            category='lifestyle',
            status_code=200,
            search_text='  </title>',
            test_username_pos='alan'
        )
        session.add(families)

        # Fanpop
        fanpop = Site(
            name='Fanpop',
            url='http://www.fanpop.com/fans/%s',
            category='entertainment',
            status_code=200,
            search_text=' Profile Page</title>',
            test_username_pos='dan'
        )
        session.add(fanpop)

        # FFFFound
        ffffound = Site(
            name='FFFFound',
            url='http://ffffound.com/home/%s/found/',
            category='image',
            status_code=200,
            search_text='<title>FFFFOUND!</title>',
            test_username_pos='tobbz'
        )
        session.add(ffffound)

        # Flavours
        flavours = Site(
            name='Flavours',
            url='http://%s.flavors.me',
            category='social',
            status_code=200,
            search_text=': Flavors.me',
            test_username_pos='john'
        )
        session.add(flavours)

        # Flickr
        flickr = Site(
            name='Flickr',
            url='https://www.flickr.com/photos/%s/',
            category='image',
            status_code=200,
            search_text='s Photostream</title>',
            test_username_pos='adam'
        )
        session.add(flickr)

        # Foodspotting
        foodspotting = Site(
            name='Foodspotting',
            url='http://www.foodspotting.com/%s',
            category='lifestyle',
            status_code=200,
            search_text=' - Foodspotting</title>',
            test_username_pos='dylan'
        )
        session.add(foodspotting)

        # Fotolog
        fotolog = Site(
            name='Fotolog',
            url='http://www.fotolog.com/%s/',
            category='image',
            status_code=200,
            search_text=' - Fotolog</title>',
            test_username_pos='anna'
        )
        session.add(fotolog)

        # Foursquare
        foursquare = Site(
            name='Foursquare',
            url='https://foursquare.com/%s',
            category='social',
            status_code=200,
            search_text='on Foursquare</title>',
            test_username_pos='john'
        )
        session.add(foursquare)

        # Freesound
        freesound = Site(
            name='Freesound',
            url='http://www.freesound.org/people/%s/',
            category='music',
            status_code=200,
            search_text='START of Content area',
            test_username_pos='john'
        )
        session.add(freesound)

        # Friendfinder-x
        friend_finder_x = Site(
            name='FriendFinder-X',
            url='http://www.friendfinder-x.com/profile/%s',
            category='dating',
            status_code=200,
            search_text='Member Profile - FriendFinder-x</title>',
            test_username_pos='daniel'
        )
        session.add(friend_finder_x)

        # Funny or die
        funny_or_die = Site(
            name='Funny or Die',
            url='http://www.funnyordie.com/%s',
            category='video',
            status_code=200,
            search_text=' - Home on Funny or Die</title>',
            test_username_pos='bob'
        )
        session.add(funny_or_die)

        # Garmin Connect
        garmin_connect = Site(
            name='Garmin Connect',
            url='http://connect.garmin.com/modern/profile/%s',
            category='health',
            status_code=200,
            search_text='VIEWER_USERPREFERENCES =',
            test_username_pos='sally'
        )
        session.add(garmin_connect)

        # Geekgrade
        geekgrade = Site(
            name='Geek Grade',
            url='http://www.geekgrade.com/geeksheet/%s/blogs',
            category='coding',
            status_code=200,
            search_text='- Geek Grade</title>',
            test_username_pos='d0k'
        )
        session.add(geekgrade)

        # Geocaching
        geocaching = Site(
            name='Geocaching',
            url='https://www.geocaching.com/seek/nearest.aspx?u=%s',
            category='hobby',
            status_code=200,
            search_text='By Username (Hidden) - User:',
            test_username_pos='john'
        )
        session.add(geocaching)

        # Get it On
        get_it_on = Site(
            name='GETitOn',
            url='http://getiton.com/profile/%s',
            category='dating',
            status_code=200,
            search_text='s Profile</title>',
            test_username_pos='chris'
        )
        session.add(get_it_on)

        # Github
        github = Site(
            name='Github',
            url='https://github.com/%s',
            category='coding',
            status_code=200,
            search_text='<meta content="profile"',
            test_username_pos='google'
        )
        session.add(github)

        # GodTube
        godtube = Site(
            name='GodTube',
            url='http://www.godtube.com/%s/',
            category='video',
            status_code=200,
            search_text='Last Visit Date:</span>',
            test_username_pos='bball1989'
        )
        session.add(godtube)

        # Gogobot
        gogobot = Site(
            name='Gogobot',
            url='http://www.gogobot.com/user/%s',
            category='travel',
            status_code=200,
            search_text='Travel Tips &amp; Activities',
            test_username_pos='dan'
        )
        session.add(gogobot)

        # Goodreads
        goodreads = Site(
            name='Goodreads',
            url='http://www.goodreads.com/%s',
            category='entertainment',
            status_code=302,
            search_text='www.goodreads.com/user/show/',
            test_username_pos='seal'
        )
        session.add(goodreads)

        # Gravatar
        gravatar = Site(
            name='Gravatar',
            url='http://en.gravatar.com/profiles/%s',
            category='social',
            status_code=200,
            search_text='"displayName":',
            test_username_pos='simon'
        )
        session.add(gravatar)

        # Hubpages
        hubpages = Site(
            name='Hubpages',
            url='http://%s.hubpages.com/',
            category='blog',
            status_code=200,
            search_text='on HubPages</title>:',
            test_username_pos='bob'
        )
        session.add(hubpages)

        i_am_pregnant = Site(
            name='i-am-pregnant',
            url='http://www.i-am-pregnant.com/members/%s/',
            category='health',
            status_code=200,
            search_text='This is the stylesheet for your pages. '
                        'Add your own rules below this line',
            test_username_pos='shiv77'
        )
        session.add(i_am_pregnant)

        if_this_then_that = Site(
            name='IFTTT',
            url='https://ifttt.com/p/%s/shared',
            category='technology',
            status_code=200,
            search_text='s Published Recipes - IFTTT',
            test_username_pos='bsaren'
        )
        session.add(if_this_then_that)

        image_shack = Site(
            name='ImageShack',
            url='https://imageshack.com/user/%s',
            category='image',
            status_code=200,
            search_text='s Images</title>',
            test_username_pos='Nicholas230'
        )
        session.add(image_shack)

        imgur = Site(
            name='imgur',
            url='http://imgur.com/user/%s',
            category='image',
            status_code=200,
            search_text='on Imgur</title>',
            test_username_pos='ThatPervert'
        )
        session.add(imgur)

        instagram = Site(
            name='Instagram',
            url='https://www.instagram.com/%s/',
            category='social',
            status_code=200,
            search_text='on Instagram" />',
            test_username_pos='kensingtonroyal'
        )
        session.add(instagram)

        instructables = Site(
            name='instructables',
            url='http://www.instructables.com/member/%s/',
            category='learning',
            status_code=200,
            search_text='<title>Instructables Member:',
            test_username_pos='shags_j'
        )
        session.add(instructables)

        interpals = Site(
            name='InterPals',
            url='https://www.interpals.net/%s',
            category='social',
            status_code=200,
            search_text='s Profile</title>',
            test_username_pos='Seven89'
        )
        session.add(interpals)

        keybase = Site(
            name='Keybase',
            url='https://keybase.io/%s',
            category='crypto',
            status_code=200,
            search_text='| Keybase</title>',
            test_username_pos='mehaase'
        )
        session.add(keybase)

        kongregate = Site(
            name='Kongregrate',
            url='http://www.kongregate.com/accounts/%s',
            category='gaming',
            status_code=200,
            search_text='s profile on Kongregate</title>',
            test_username_pos='Truestrike'
        )
        session.add(kongregate)

        lanyrd = Site(
            name='Lanyrd',
            url='http://lanyrd.com/profile/%s/',
            category='social',
            status_code=200,
            search_text='s conference talks and presentations '
                        '| Lanyrd</title>',
            test_username_pos='shanselman'
        )
        session.add(lanyrd)

        last_fm = Site(
            name='Last.fm',
            url='http://www.last.fm/user/%s',
            category='music',
            status_code=200,
            search_text='s Music Profile - Users',
            test_username_pos='FrancaesG'
        )
        session.add(last_fm)

        law_of_attraction = Site(
            name='Law of Attraction',
            url='http://www.lawofattractionsingles.com/%s',
            category='dating',
            status_code=200,
            search_text='s profile on Law Of Attraction Singles</title>',
            test_username_pos='Jenniferlynnmaui'
        )
        session.add(law_of_attraction)

        library_thing = Site(
            name='LibraryThing',
            url='https://www.librarything.com/profile/%s',
            category='learning',
            status_code=200,
            search_text='| LibraryThing</title>',
            test_username_pos='Medievalgirl'
        )
        session.add(library_thing)

        linked_in = Site(
            name='LinkedIn',
            url='https://www.linkedin.com/in/%s',
            category='social',
            status_code=200,
            search_text='summary="Overview for ',
            test_username_pos='markhaase'
        )
        session.add(linked_in)

        marketing_land = Site(
            name='Marketing Land',
            url='http://marketingland.com/author/%s',
            category='business',
            status_code=200,
            search_text='property="og:url" content=,',
            test_username_pos='barb-palser'
        )
        session.add(marketing_land)

        mate1 = Site(
            name='Mate1.com',
            url='http://www.mate1.com/profiles/%s',
            category='dating',
            status_code=200,
            search_text='basicInfoTitle">Basic Info',
            test_username_pos='janedoe'
        )
        session.add(mate1)

        medium = Site(
            name='Medium',
            url='https://medium.com/@%s',
            category='social',
            status_code=200,
            search_text='name="description" content="',
            test_username_pos='erinshawstreet'
        )
        session.add(medium)

        meetzur = Site(
            name='Meetzur',
            url='http://www.meetzur.com/%s',
            category='social',
            status_code=200,
            search_text='MEETZUR_PROFILE_300x250',
            test_username_pos='sachin99'
        )
        session.add(meetzur)

        mixcloud = Site(
            name='Mixcloud',
            url='https://www.mixcloud.com/%s/',
            category='music',
            status_code=200,
            search_text='s Favorites | Mixcloud</title>',
            test_username_pos='dublab'
        )
        session.add(mixcloud)

        mixcrate = Site(
            name='mixcrate',
            url='http://www.mixcrate.com/%s',
            category='music',
            status_code=200,
            search_text='- Mixcrate</title>',
            test_username_pos='kennyrock'
        )
        session.add(mixcrate)

        mixlr = Site(
            name='Mixlr',
            url='http://mixlr.com/%s/',
            category='music',
            status_code=200,
            search_text='is on Mixlr. Mixlr is a simple way to share live',
            test_username_pos='therwandan'
        )
        session.add(mixlr)

        mod_db = Site(
            name='Mod DB',
            url='http://www.moddb.com/members/%s',
            category='gaming',
            status_code=200,
            search_text='View the Mod DB  member ',
            test_username_pos='hugebot'
        )
        session.add(mod_db)

        muck_rack = Site(
            name='Muck Rack',
            url='https://muckrack.com/%s',
            category='gaming',
            status_code=200,
            search_text='on Muck Rack</title>',
            test_username_pos='scottkleinberg'
        )
        session.add(muck_rack)

        mybuilder_com = Site(
            name='MyBuilder.com',
            url='https://www.mybuilder.com/profile/view/%s',
            category='business',
            status_code=200,
            search_text='s profile</title>',
            test_username_pos='kdbuildingservices'
        )
        session.add(mybuilder_com)

        mylot = Site(
            name='myLot',
            url='http://www.mylot.com/%s',
            category='social',
            status_code=200,
            search_text='on myLot</title>',
            test_username_pos='LovingMyBabies'
        )
        session.add(mylot)

        myspace = Site(
            name='Myspace',
            url='https://myspace.com/%s',
            category='social',
            status_code=200,
            search_text=') on Myspace</title>',
            test_username_pos='kesha'
        )
        session.add(myspace)

        netvibes = Site(
            name='Netvibes',
            url='http://www.netvibes.com/%s',
            category='business',
            status_code=200,
            search_text='s Public Page</title>',
            test_username_pos='grade3kis'
        )
        session.add(netvibes)

        okcupid = Site(
            name='okcupid',
            url='https://www.okcupid.com/profile/%s',
            category='dating',
            status_code=200,
            search_text='<title>OkCupid |',
            test_username_pos='the_ferett'
        )
        session.add(okcupid)

        lifeboat = Site(
            name='lifeboat',
            url='https://oc.tc/%s',
            category='gaming',
            status_code=200,
            search_text='https://avatar.oc.tc/',
            test_username_pos='Matilaina'
        )
        session.add(lifeboat)

        pandora = Site(
            name='Pandora',
            url='https://www.pandora.com/profile/%s',
            category='music',
            status_code=200,
            search_text='div class="profile_container_static"',
            test_username_pos='mehaase'
        )
        session.add(pandora)

        photoblog = Site(
            name='PhotoBlog',
            url='https://www.photoblog.com/%s',
            category='social',
            status_code=200,
            search_text='photoblog_username = "',
            test_username_pos='canon6d'
        )
        session.add(photoblog)

        photobucket = Site(
            name='Photobucker',
            url='http://photobucket.com/user/%s/library/',
            category='image',
            status_code=200,
            search_text=' Pictures, Photos & Images | Photobucket</title>',
            test_username_pos='darkgladir'
        )
        session.add(photobucket)

        picture_trail = Site(
            name='PictureTrail',
            url='http://www.picturetrail.com/%s',
            category='image',
            status_code=200,
            search_text='<title>PictureTrail</title>',
            test_username_pos='victoria15'
        )
        session.add(picture_trail)

        pink_bike = Site(
            name='Pinkbike',
            url='http://www.pinkbike.com/u/%s/',
            category='entertainment',
            status_code=200,
            search_text='on Pinkbike</title>',
            test_username_pos='mattwragg'
        )
        session.add(pink_bike)

        pinterest = Site(
            name='Pinterest',
            url='https://www.pinterest.com/%s/',
            category='social',
            status_code=200,
            search_text='on Pinterest</title>',
            test_username_pos='mehaase'
        )
        session.add(pinterest)

        playlists_net = Site(
            name='Playlists.Net',
            url='http://playlists.net/members/%s',
            category='music',
            status_code=200,
            search_text='<title>Profile for ',
            test_username_pos='WhatisSoul'
        )
        session.add(playlists_net)

        plurk = Site(
            name='Plurk',
            url='http://www.plurk.com/%s',
            category='social',
            status_code=200,
            search_text='] on Plurk - Plurk</title>',
            test_username_pos='xxSaltandPepperxx'
        )
        session.add(plurk)

        rate_your_music = Site(
            name='Rate Your Music',
            url='http://rateyourmusic.com/~%s',
            category='music',
            status_code=200,
            search_text='Rate Your Music</title>',
            test_username_pos='silvioporto'
        )
        session.add(rate_your_music)

        readability = Site(
            name='Readability',
            url='https://readability.com/%s/',
            category='entertainment',
            status_code=200,
            search_text='on Readability',
            test_username_pos='adam'
        )
        session.add(readability)

        reddit = Site(
            name='Reddit',
            url='https://www.reddit.com/user/%s',
            category='social',
            status_code=200,
            search_text='<title>overview for ',
            test_username_pos='mehaase'
        )
        session.add(reddit)

        scratch = Site(
            name='MeTwo',
            url='https://scratch.mit.edu/users/%s/',
            category='social',
            status_code=200,
            search_text='on Scratch</title>',
            test_username_pos='MeTwo'
        )
        session.add(scratch)

        rapid7_community = Site(
            name='Rapid7 Community',
            url='https://community.rapid7.com/people/%s',
            category='technology',
            status_code=200,
            search_text='s Profile     | SecurityStreet',
            test_username_pos='dabdine'
        )
        session.add(rapid7_community)

        setlist_fm = Site(
            name='setlist.fm',
            url='http://www.setlist.fm/user/%s',
            category='music',
            status_code=200,
            search_text='s setlist.fm | setlist.fm</title>',
            test_username_pos='tw21'
        )
        session.add(setlist_fm)

        shopcade = Site(
            name='Shopcade',
            url='https://www.shopcade.com/%s',
            category='social',
            status_code=200,
            search_text=') on Shopcade</title',
            test_username_pos='salonidahake'
        )
        session.add(shopcade)

        single_muslim = Site(
            name='SingleMuslim',
            url='https://www.singlemuslim.com/searchuser/%s/abc',
            category='dating',
            status_code=200,
            search_text='- Single Muslim Rest of the World</title>',
            test_username_pos='YoghurtTub'
        )
        session.add(single_muslim)

        slashdot = Site(
            name='Slashdot',
            url='https://slashdot.org/~%s',
            category='technology',
            status_code=200,
            search_text='- Slashdot User</title>',
            test_username_pos='Locke2005'
        )
        session.add(slashdot)

        slideshare = Site(
            name='SlideShare',
            url='http://www.slideshare.net/%s',
            category='technology',
            status_code=200,
            search_text='s presentations</title>',
            test_username_pos='dmc500hats'
        )
        session.add(slideshare)

        smite_guru = Site(
            name='SmiteGuru',
            url='http://smite.guru/stats/xb/%s/summary',
            category='gaming',
            status_code=200,
            search_text='<title>SmiteGuru - ',
            test_username_pos='WatsonV3'
        )
        session.add(smite_guru)

        smug_mug = Site(
            name='SmugMug',
            url='https://%s.smugmug.com/',
            category='image',
            status_code=200,
            search_text='pageon: homepage',
            test_username_pos='therescueddog'
        )
        session.add(smug_mug)

        smule = Site(
            name='Smule',
            url='http://www.smule.com/%s',
            category='music',
            status_code=200,
            search_text='s Profile on Smule</title>',
            test_username_pos='_PFR_Anashi716'
        )
        session.add(smule)

        snooth = Site(
            name='Snooth',
            url='http://www.snooth.com/profiles/%s/',
            category='music',
            status_code=200,
            search_text='Location: http://www.snooth.com/profiles/John/',
            test_username_pos='dvogler'
        )
        session.add(snooth)

        soldier_x = Site(
            name='SoldierX',
            url='https://www.soldierx.com/hdb/%s',
            category='technology',
            status_code=200,
            search_text='div id="node-',
            test_username_pos='achillean'
        )
        session.add(soldier_x)

        sound_cloud = Site(
            name='SoundCloud',
            url='https://soundcloud.com/%s',
            category='music',
            status_code=200,
            search_text='profile - Hear the world',
            test_username_pos='youngma'
        )
        session.add(sound_cloud)

        soup = Site(
            name='Soup',
            url='http://%s.soup.io/',
            category='social',
            status_code=200,
            search_text='"s soup</title>',
            test_username_pos='nattaly'
        )
        session.add(soup)

        source_forge = Site(
            name='SourceForge',
            url='https://sourceforge.net/u/%s/profile/',
            category='technology',
            status_code=200,
            search_text=' / Profile</title>',
            test_username_pos='ronys'
        )
        session.add(source_forge)

        speaker_deck = Site(
            name='Speaker Deck',
            url='https://speakerdeck.com/%s',
            category='technology',
            status_code=200,
            search_text='<title>Presentations by',
            test_username_pos='rocio'
        )
        session.add(speaker_deck)

        sporcle = Site(
            name='Sporcle',
            url='http://www.sporcle.com/user/%s',
            category='entertainment',
            status_code=200,
            search_text="id='UserBox'>",
            test_username_pos='lolshortee'
        )
        session.add(sporcle)

        steam = Site(
            name='Steam',
            url='http://steamcommunity.com/id/%s',
            category='gaming',
            status_code=200,
            search_text='g_rgProfileData =',
            test_username_pos='tryh4rdz'
        )
        session.add(steam)

        stumble_upon = Site(
            name='StumbleUpon',
            url='http://www.stumbleupon.com/stumbler/%s',
            category='social',
            status_code=200,
            search_text='s Likes | StumbleUpon.com</title>',
            test_username_pos='starspirit'
        )
        session.add(stumble_upon)

        stupid_cancer = Site(
            name='Stupidcancer',
            url='http://stupidcancer.org/community/profile/%s',
            category='social',
            status_code=200,
            search_text='- Stupid Cancer Community</title>',
            test_username_pos='CatchMeYes'
        )
        session.add(stupid_cancer)

        tf2_backpack_examiner = Site(
            name='TF2 Backpack Examiner',
            url='http://www.tf2items.com/id/%s',
            category='gaming',
            status_code=200,
            search_text='<title>TF2 Backpack -',
            test_username_pos='robinwalker'
        )
        session.add(tf2_backpack_examiner)

        tribe = Site(
            name='Tribe',
            url='http://people.tribe.net/%s',
            category='social',
            status_code=200,
            search_text='Profile - tribe.net</title>',
            test_username_pos='violetta'
        )
        session.add(tribe)

        trip_advisor = Site(
            name='TripAdvisor',
            url='https://www.tripadvisor.com/members/%s',
            category='social',
            status_code=200,
            search_text='<title>Member Profile - ',
            test_username_pos='scrltd16'
        )
        session.add(trip_advisor)

        tumblr = Site(
            name='Tumblr',
            url='http://%s.tumblr.com/',
            category='social',
            status_code=200,
            search_text='X-Tumblr-User:',
            test_username_pos='seanjacobcullen'
        )
        session.add(tumblr)

        twitter = Site(
            name='Twitter',
            url='https://twitter.com/%s',
            category='social',
            status_code=200,
            search_text='| Twitter</title>',
            test_username_pos='mehaase'
        )
        session.add(twitter)

        untappd = Site(
            name='Untappd',
            url='https://untappd.com/user/%s',
            category='entertainment',
            status_code=200,
            search_text='on Untappd</title>',
            test_username_pos='samelawrence'
        )
        session.add(untappd)

        vimeo = Site(
            name='Vimeo',
            url='https://vimeo.com/%s',
            category='image',
            status_code=200,
            search_text='on Vimeo</title>',
            test_username_pos='mikeolbinski'
        )
        session.add(vimeo)

        visualize_us = Site(
            name='VisualizeUs',
            url='http://vi.sualize.us/%s/',
            category='social',
            status_code=200,
            search_text='favorite pictures on VisualizeUs</title>',
            test_username_pos='emilybusiness'
        )
        session.add(visualize_us)

        voices_com = Site(
            name='Voices.com',
            url='https://www.voices.com/people/%s',
            category='business',
            status_code=200,
            search_text='/assets/images/branding/default_profile_avatar',
            test_username_pos='johncavanagh'
        )
        session.add(voices_com)

        wanelo = Site(
            name='Wanelo',
            url='https://wanelo.com/%s',
            category='social',
            status_code=200,
            search_text='on Wanelo</title>',
            test_username_pos='tsingeli'
        )
        session.add(wanelo)

        wattpad = Site(
            name='Wattpad',
            url='https://www.wattpad.com/user/%s',
            category='social',
            status_code=200,
            search_text='- Wattpad </title>',
            test_username_pos='Weirdly_Sarcastic'
        )
        session.add(wattpad)

        wishlistr = Site(
            name='Wishlistr',
            url='http://www.wishlistr.com/profile/%s/',
            category='social',
            status_code=200,
            search_text='s profile</title>',
            test_username_pos='seventy7'
        )
        session.add(wishlistr)

        wordpress = Site(
            name='WordPress',
            url='https://profiles.wordpress.org/%s/',
            category='business',
            status_code=200,
            search_text='alt="Profile picture of',
            test_username_pos='sivel'
        )
        session.add(wordpress)

        xbox_gamertag = Site(
            name='Xbox Gamertag',
            url='https://www.xboxgamertag.com/search/%s/',
            category='gaming',
            status_code=200,
            search_text=' - Xbox Live Gamertag </title>',
            test_username_pos='masterrshake'
        )
        session.add(xbox_gamertag)

        youtube = Site(
            name='YouTube',
            url='https://www.youtube.com/user/%s',
            category='image',
            status_code=200,
            search_text='- YouTube</title>',
            test_username_pos='vlogdozack'
        )
        session.add(youtube)

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
