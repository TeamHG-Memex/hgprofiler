/// A model for a username search result.
class Result {

    int id;
    String jobId;
    String siteName;
    String siteUrl;
    bool found;
    int number;
    int total;

    String error;

    Result(String jobId, String siteName, siteUrl, bool found, int number, int total) {
        this.found = found;
        this.jobId = jobId; 
        this.siteName = siteName; 
        this.siteUrl = siteUrl; 
        this.number = number; 
        this.total = total; 
    }

    Result.fromJson(Map json) {
        this.found = json['found'];
        this.id = json['id'];
        this.jobId = json['job_id'];
        this.siteName = json['site_name'];
        this.siteUrl = json['site_url'];
        this.number = json['number'];
        this.total = json['total'];
        this.error = json['error'];
    }
}
