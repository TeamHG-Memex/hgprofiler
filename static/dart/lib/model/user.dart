/// A model for a logged in user.
class User {
    int id;

    String agency;
    DateTime created;
    String email;
    bool isAdmin;
    String location;
    DateTime modified;
    String name;
    String phone, phoneE164;
    String thumb;

    User(this.id, this.email, this.isAdmin);

    User.fromJson(Map json) {
        this.id = json['id'];

        this.agency = json['agency'];
        this.created = DateTime.parse(json['created']);
        this.email = json['email'];
        this.isAdmin = json['is_admin'];
        this.location = json['location'];
        this.modified = DateTime.parse(json['modified']);
        this.name = json['name'];
        this.phone = json['phone'];
        this.phoneE164 = json['phone_e164'];
        this.thumb = json['thumb'];
    }
}
