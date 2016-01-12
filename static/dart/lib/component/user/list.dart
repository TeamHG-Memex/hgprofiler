import 'dart:html';
import 'dart:math';

import 'package:angular/angular.dart';
import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/pager.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/mixin/current_page.dart';
import 'package:hgprofiler/model/user.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:bootjack/bootjack.dart';
import 'package:dquery/dquery.dart';

/// A component for listing application users.
@Component(
    selector: 'user-list',
    templateUrl: 'packages/hgprofiler/component/user/list.html',
    useShadowDom: false
)
class UserListComponent extends Object with CurrentPageMixin {
    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('User Directory'),
    ];

    String error;
    bool loading = false;
    Pager pager;
    List<User> users;

    final AuthenticationController auth;
    final RestApiController _api;
    final int _resultsPerPage = 10;
    final Router _router;
    final RouteProvider _rp;
    final TitleService _ts;

    /// Constructor.
    UserListComponent(this.auth, this._api, this._router, this._rp, this._ts) {
        this.initCurrentPage(this._rp.route, this._fetchCurrentPage);
        this._fetchCurrentPage();
        this._ts.title = 'User Directory';
    }

    /// Create a new user and (if successful) redirect to the new URL.
    void addUser(Event event, dynamic data, Function resetButton) {
        this.error = null;

        Map body = {
            'email': document.getElementById('email').value,
            'password': document.getElementById('password').value,
        };

        this._api
            .post('/api/user/', body, needsAuth: true)
            .then((response) {
                Modal.wire($("#add-user-modal")).hide();
                this._router.go('user_view', {'id': response.data['id']});
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                resetButton();
            });
    }

    /// Simulate a click on the "Add" button.
    void submitAddUser() {
        window.document.getElementById('add-button').click();
    }

    /// Fetch a page of users.
    void _fetchCurrentPage() {
        this.error = null;
        this.loading = true;
        String pageUrl = '/api/user/';
        Map urlArgs = {
            'page': this.currentPage,
            'rpp': this._resultsPerPage,
        };

        this._api
            .get(pageUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                this.users = new List.generate(
                    response.data['users'].length,
                    (index) => new User.fromJson(response.data['users'][index])
                );

                this.pager = new Pager(response.data['total_count'],
                                       this.currentPage,
                                       resultsPerPage:this._resultsPerPage);
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {this.loading = false;});
    }
}
