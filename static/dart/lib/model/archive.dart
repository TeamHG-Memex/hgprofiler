/// A model for a social or form site.
class Archive {

    int id;
    String trackerId;
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

    Archive(String trackerId, DateTime date, String username, Map group,
            int siteCount, int foundCount, int notFoundCount, int errorCount,
            String zipFileUrl) {
        this.trackerId = trackerId;
        this.date = date;
        this.username = username;
        this.group = group;
        this.siteCount = siteCount;
        this.foundCount = foundCount;
        this.notFoundCount = notFoundCount;
        this.errorCount = errorCount;
        this.zipFileUrl = zipFileUrl;
    }

   Archive.fromJson(Map json) {
        this.trackerId = json['tracker_id'];
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
