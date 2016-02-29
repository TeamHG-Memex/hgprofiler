/// A model for a username search result.
class Result {

    int id;
    String jobId;
    String siteName;
    String siteUrl;
    int imageFileId;
    String imageFileUrl;
    int number;
    String status;
    int total;
    String error;

    Result(String jobId, String siteName, siteUrl, String status, int number, int total) {
        this.status = status; 
        this.jobId = jobId; 
        this.siteName = siteName; 
        this.siteUrl = siteUrl; 
        this.number = number; 
        this.total = total; 
    }

    Result.fromJson(Map json) {
        this.status = json['status'];
        this.id = json['id'];
        this.jobId = json['job_id'];
        this.siteName = json['site_name'];
        this.siteUrl = json['site_url'];
        this.imageFileId = json['image_file_id'];
        this.imageFileUrl = json['image_file_url'];
        this.number = json['number'];
        this.total = json['total'];
        this.error = json['error'];
    }
}
