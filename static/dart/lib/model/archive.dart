/// A model for a social or form site.
class Archive {

    int id;
    String jobId;
    DateTime date;
    String username;
    Map group;
    int siteCount;
    int foundCount;
    int notFoundCount;
    int errorCount;
    String zipFileUrl;

    // Errors related to creating or loading this profile.
    String error;

    Archive(String jobId, DateTime date, String username, Map group, int siteCount, int foundCount, int notFoundCount, int errorCount, int zipFileUrl) {
        this.jobId = jobId; 
        this.date = date;
        this.username = username;
        this.group = group;
        this.siteCount = siteCount;
        this.foundCount = foundCount;
        this.notFoundCount = notFoundCount;
        this.errorCount = errorCount;
        this.zipFile = zipFileUrl;
    }

   Archive.fromJson(Map json) {
        this.jobId = json['job_id'];
        this.id = json['id'];
        this.date = json['date'];
        this.username = json['username'];
        this.group = json['group'];
        this.siteCount = json['site_count'];
        this.foundCount = json['found_count'];
        this.notFoundCount = json['not_found_count'];
        this.errorCount = json['error_count'];
        this.zipFileUrl = json['zip_file_url'];
    }
}
