import os
import io
import csv
import json
import time
import zipfile

import worker
from app.config import get_path
from model import Archive


class ArchiveException(Exception):
    ''' Represents a user-facing exception. '''

    def __init__(self, message):
        self.message = message


def results_csv_string(results):
    ''' Generate in-memory csv of the results and return it as a string. '''

    data = []
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for result in results:
        row = [result['site_name'], result['site_url'], result['found'], result['image']]
        data.append(row)

    writer.writerows(data)

    return output.getvalue()


def create_zip(name, results):
    """ Generate a zipped archive containing results.csv and all images for a username search."""

    data_dir = get_path("data")
    screenshot_dir = os.path.join(data_dir, 'screenshot')
    archive_dir = os.path.join(data_dir, 'archive')
    zip_path = os.path.join(archive_dir, name)
    zip_file = zipfile.ZipFile(zip_path, 'w')

    # Add images
    for result in results:
        image_path = os.path.join(screenshot_dir, result['image'])
        zip_file.write(image_path, arcname=result['image'], compress_type=zipfile.ZIP_DEFLATED)

    # Add results csv
    csv_string = results_csv_string(results)
    info = zipfile.ZipInfo('results.csv')
    info.date_time = time.localtime(time.time())[:6]
    info.compress_type = zipfile.ZIP_DEFLATED
    zip_file.writestr(info, csv_string)
    zip_file.close()


def create_archive(job_id, username, results):
    """ Save result summary to db and store static files in zip archive."""

    redis = worker.get_redis()
    db_session = worker.get_session()
    zip_name = '{}.zip'.format(job_id)
    site_count = len(results)
    found_count = 0
    not_found_count = 0
    error_count = 0
    create_zip(zip_name, results)

    for result in results:
        if result['error'] is not None:
            error_count += 1
        elif result['found']:
            found_count += 1
        else:
            not_found_count += 1

    archive = Archive(job_id=job_id,
                      username=username,
                      site_count=site_count,
                      found_count=found_count,
                      not_found_count=not_found_count,
                      error_count=error_count,
                      zip_file=zip_name)


    db_session.add(archive)
    db_session.commit()
    # Publish
    redis.publish('archive', json.dumps(archive.as_dict()))
