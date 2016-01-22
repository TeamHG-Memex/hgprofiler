import os
import io
import csv
import time
import zipfile

from app.config import get_path


def results_csv_string(results):
    ''' Generate an in-memory csv of the results and return it as a string. '''
    data = []
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for result in results:
        row = [result.site_name, result.site_url, result.found, result.image]
        data.append(row)

    writer.writerows(data)

    return output.getvalue()


def create_zip(job_id, results):
    """ Generate a zipped archive containing results.csv and all images for a username search."""
    data_dir = get_path("data")
    screenshot_dir = os.path.join(data_dir, 'screenshot')
    archive_dir = os.path.join(data_dir, 'archive')
    name = '{}.zip'.format(job_id)
    zip_path = os.path.join(archive_dir, name)
    zip_file = zipfile.ZipFile(zip_path, 'w')
    # Add images
    for result in results:
        image_path = os.path.join(screenshot_dir, result.image)
        zip_file.write(result.image, image_path, zipfile.ZIP_DEFLATED)

    # Add results csv
    csv_string = results_csv_string(results)
    info = zipfile.ZipInfo('results.csv')
    info.date_time = time.localtime(time.time())[:6]
    info.compress_type = zipfile.ZIP_DEFLATED
    zip_file.writestr(info, csv_string)
    zip_file.close()
    # Publish
