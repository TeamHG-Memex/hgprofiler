/// A model for a social or form site.
import 'package:hgprofiler/model/result.dart';

class Site {

    String category;
    int id;
    int statusCode;
    String searchText;
    String name;
    String url;
    String testUsernamePos;
    String testUsernameNeg;
    Result testResultPos;
    Result testResultNeg;
    DateTime testedAt;
    bool valid;

    // Errors related to creating or loading this site.
    String error;

    Site(String name, String url, String category,
         int statusCode, String searchText,
         String testUsernamePos) {

        this.name = name; 
        this.url = url;
        this.category = category;
        this.statusCode = statusCode;
        this.searchText = searchText;
	    this.testUsernamePos = testUsernamePos;
    }

    Site.fromJson(Map json) {
        this.category = json['category'];
        this.statusCode = json['status_code'];
        this.searchText = json['search_text'];
        this.id = json['id'];
        this.name = json['name'];
        this.url = json['url'];
        this.testUsernamePos = json['test_username_pos'];
        this.testUsernameNeg = json['test_username_neg'];

        if (json['test_result_pos'] != null) {
           this.testResultPos = new Result.fromJson(json['test_result_pos']);
        } else {
            this.testResultPos = null;
        }

        if (json['test_result_neg'] != null) {
           this.testResultNeg = new Result.fromJson(json['test_result_neg']);
        } else {
            this.testResultNeg = null;
        }

	    this.valid = json['valid'];
	    this.testedAt = json['tested_at'];
    }
}
