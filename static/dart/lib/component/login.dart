import 'package:angular/angular.dart';

import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/rest_api.dart';

/// A controller that presents a UI for logging in.
@Component(
    selector: 'login',
    templateUrl: 'packages/hgprofiler/component/login.html',
    useShadowDom: false
)
class LoginComponent {
    AuthenticationController auth;
    RestApiController server;
    RouteProvider rp;
    TitleService ts;

    String email='', password='', error='';
    bool buttonBusy = false;

    /// Constructor.
    LoginComponent(this.auth, this.rp, this.server, this.ts) {
        this.ts.title = 'Login';

        if (this.rp.route.queryParameters['expired'] == 'true') {
            this.error = 'Your session has expired. Please log in again'
                         ' to continue.';
        }
    }

    /// Ask the server to validate the user's credentials and give us an
    /// authentication token for future API requests.
    void login() {
        this.buttonBusy = true;
        this.error = '';
        var payload = {'email': this.email, 'password': this.password};

        server
            .post('/api/authentication/', payload, needsAuth: false)
            .then((response) {
                auth.checkToken(response.data['token']);
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.buttonBusy = false;
            });
    }
}
