import os
import re
import io
import csv
import json

import worker
from app.config import get_path
from model.archive import Archive
from model.file import File


class ArchiveException(Exception):
    ''' Represents a user-facing exception. '''

    def __init__(self, message):
        self.message = message


def results_csv_string(results):
    ''' Generate in-memory csv of the results and return it as a string. '''

    data = []
    # Column headers
    row = ['Site Name', 'Search Url', 'Found', 'Screenshot']
    data.append(row)

    # In-memory csv
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    # Add results
    for result in results:
        # Strip job ID to match the name of the zipped file (archives in /data directory include
        # the job id).
        if result['image_file_name'] is not None:
            image_name = result['image_file_name']
        else:
            image_name = None

        row = [result['site_name'], result['site_url'], result['found'], image_name]
        data.append(row)

    writer.writerows(data)

    return output.getvalue()


#def create_zip(username, job_id, results):
#    """ Generate a zipped archive containing results.csv and all images for a username search."""
#
#    zip_name = '{}-{}.zip'.format(username, job_id)
#    data_dir = get_path("data")
#    screenshot_dir = os.path.join(data_dir, 'screenshot')
#    archive_dir = os.path.join(data_dir, 'archive')
#    zip_path = os.path.join(archive_dir, zip_name)
#    zip_file = zipfile.ZipFile(zip_path, 'w')
#
#    # Add images
#    for result in results:
#        if result['image_file_path'] is not None:
#            image_path = os.path.join(data_dir, result['image_file_path'])
#            # Strip job ID to make the file name more readable.
#            #replace_chars = '-{}'.format(job_id)
#            #image_name = result['image'].replace(replace_chars, '')
#            zip_file.write(image_path, arcname=result['image_file_name'], compress_type=zipfile.ZIP_DEFLATED)
#
#    # Add results csv
#    csv_string = results_csv_string(results)
#    csv_name = '{}.csv'.format(username)
#    info = zipfile.ZipInfo(csv_name)
#    info.date_time = time.localtime(time.time())[:6]
#    info.compress_type = zipfile.ZIP_DEFLATED
#    zip_file.writestr(info, csv_string)
#    zip_file.close()

def create_zip(filename, results):
    '''
    Generate zip archive of results and return the file id.

    Adds all images for results that have screenshots.
    Adds csv result summary created on the fly (as IOString).
    '''

    db_session = worker.get_session()
    files = []
    str_files = []

    # Get list of images
    for result in results:
        if result['image_file_path'] is not None:
            image = (result['image_file_name'], result['image_file_path'])
            files.append(image)

    # Generate in-memory results csv
    csv_string = results_csv_string(results)
    str_file = ('{}.csv'.format(filename), csv_string)
    str_files.append(str_file)

    zip_file = File(name='{}.zip'.format(filename),
                    mime='application/zip',
                    zip_archive=True,
                    zip_files=files,
                    zip_str_files=str_files)

    db_session.add(zip_file)

    try:
        db_session.commit()
    except Exception as e:
        raise ScrapeException(e)

    return zip_file.id



def create_archive(job_id, username, group_id, results):
    """
    Archive summary of results in the database and store a zip archive in the data
    directory.
    """

    redis = worker.get_redis()
    db_session = worker.get_session()
    site_count = len(results)
    found_count = 0
    not_found_count = 0
    error_count = 0
    name = '{}-{}'.format(re.sub('[\W_]+', '', username), job_id)  # Strip non-alphanumeric char
    zip_name = '{}.zip'.format(name)

    # Generate zip file
    filename = re.sub('[\W_]+', '', username) # Strip non-alphanumeric char
    zip_file_id = create_zip(filename, results)

    # Generate found/not found counts
    # Results that have errors increment the not_found_count
    for result in results:
        if result['error'] is not None:
            error_count += 1
        elif result['found']:
            found_count += 1
        else:
            not_found_count += 1

    archive = Archive(job_id=job_id,
                      username=username,
                      group_id = group_id,
                      site_count=site_count,
                      found_count=found_count,
                      not_found_count=not_found_count,
                      error_count=error_count,
                      zip_file_id=zip_file_id)

    # Write to db
    db_session.add(archive)
    db_session.commit()

    # Publish
    redis.publish('archive', json.dumps(archive.as_dict()))
