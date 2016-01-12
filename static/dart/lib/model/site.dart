/// A model for a social or form site.
class Site {

    String category;
    int id;
    int statusCode;
    String searchText;
    String name;
    String url;

    // Errors related to creating or loading this profile.
    String error;

    Site(String name, String url, String category, int statusCode, String searchText) {
        this.name = name; 
        this.url = url;
        this.category = category;
        this.statusCode = statusCode;
        this.searchText = searchText;
    }

    Site.fromJson(Map json) {
        this.category = json['category'];
        this.statusCode = json['status_code'];
        this.searchText = json['search_text'];
        this.id = json['id'];
        this.name = json['name'];
        this.url = json['url'];
    }
}
