import re
import io
import csv
import json

import worker
from app.rest import url_for
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
    row = ['Site Name', 'Search Url', 'Status', 'Screenshot']
    data.append(row)

    # In-memory csv
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    # Add results
    for result in results:
        # Clean fields for user-friendly output
        if result['status'] == 'e':
            status = 'Error'
        elif result['status'] == 'f':
            status = 'Found'
        elif result['status'] == 'n':
            status = 'Not Found'
        else:
            status = 'Unknown'

        row = [
            result['site_name'],
            result['site_url'],
            status,
            result['image_name']
        ]
        data.append(row)

    writer.writerows(data)

    return output.getvalue()


def create_zip(filename, results):
    '''
    Generate zip archive of results and return the file id.

    Adds all images for results that have screenshots.
    Adds csv result summary created on the fly (as IOString).
    '''

    db_session = worker.get_session()
    files = []
    str_files = []
    # Get images records for the results
    #file_ids = [r['image_file_id'] for r in results]
    #image_files = db_session.query(File).filter(File.id.in_(file_ids)).all()
    #file_dict = {}
    #for image_file in image_files:
    #    file_dict[image_file.id] = image_file

    # Create list of images
    for result in results:
        #image_file = file_dict[result['image_file_id']]
        # Add the name to results for the csv output
        image_tuple = (result['image_name'], result['image_file_path'])
        files.append(image_tuple)

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
        raise ArchiveException(e)

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

    # Generate zip file
    filename = re.sub('[\W_]+', '', username)  # Strip non-alphanumeric char
    zip_file_id = create_zip(filename, results)

    for result in results:
        if result['status'] == 'e':
            error_count += 1
        elif result['status'] == 'f':
            found_count += 1
        elif result['status'] == 'n':
            not_found_count += 1

    archive = Archive(job_id=job_id,
                      username=username,
                      group_id=group_id,
                      site_count=site_count,
                      found_count=found_count,
                      not_found_count=not_found_count,
                      error_count=error_count,
                      zip_file_id=zip_file_id)

    # Write to db
    db_session.add(archive)
    db_session.commit()

    # Publish
    message = {
        'id': archive.id,
        'name': archive.username,
        'status': 'created',
        'archive': archive.as_dict(),
        # 'resource': url_for('ArchiveView:get', id_=archive.id)
    }
    redis.publish('archive', json.dumps(message))
