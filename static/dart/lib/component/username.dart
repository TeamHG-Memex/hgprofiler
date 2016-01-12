import 'dart:async';
import 'dart:convert';
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/pager.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/model/result.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/sse.dart';

/// A controller for searching websites for usernames.
@Component(
    selector: 'username',
    templateUrl: 'packages/hgprofiler/component/username.html',
    useShadowDom: false
)
class UsernameComponent implements ShadowRootAware {
    Map backgroundTask;
    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('Usernames', '/username'),
    ];
    int currentPage;
    String error;
    bool loading = false;
    String jobId;
    List<Result> results;
    bool submittingUsername = false;
    bool awaitingResults = false;
    Pager pager;
    String query;
    String username;
    int resultsPerPage = 10;
    int totalResults;
    int found;
    String sort, sortDescription;
    List<String> urls;

    InputElement _inputEl;

    final AuthenticationController _auth; 
    final Element _element;
    final RestApiController _api;
    final RouteProvider _rp;
    final Router _router;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor
    UsernameComponent(this._api, this._auth, this._element, this._rp, this._router, this._sse, this._ts) {
        // Get the current query parameters from URL...
        var route = this._rp.route;
        this._parseQueryParameters(route.queryParameters);
        this._ts.title = 'Usernames';

        // Add event listeners...
        RouteHandle rh = route.newHandle();

        List<StreamSubscription> listeners = [
            this._sse.onResult.listen(this._resultListener),
            rh.onEnter.listen((e) {
                this._parseQueryParameters(e.queryParameters);
                this._fetchCurrentPage();
            }),
        ];

        // ...and remove event listeners when we leave this route.
        rh.onLeave.take(1).listen((e) {
            listeners.forEach((listener) => listener.cancel());
        });
    }

    // Request username search from background workers.
    void searchUsername() {
        if (this.query == null || this.query == '') {
            this.error = 'You must enter a username query';
            return;
        } else {
            this.error = null;
        }
        this.submittingUsername = true;
        this.awaitingResults = true;
        this.results = new List<Result>();
        this.totalResults = 0;
        this.found = 0;
        this.username = this.query;

        String pageUrl = '/api/username/';

        Map body = {
            'usernames': [this.query]
        };

        this._api
            .post(pageUrl, body, needsAuth: true)
            .then((response) {
                this.query = '';
                this.jobId = response.data['jobs'][0]['id'];
                new Timer(new Duration(seconds:0.1), () => this._inputEl.focus());
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {this.submittingUsername = false;});
    }

    /// Listen for job results.
    void _resultListener(Event e) {
        Map json = JSON.decode(e.data);
        Result result = new Result.fromJson(json);
        if (result.jobId == this.jobId) {
            this.results.add(result);
            this.totalResults = result.total;
            if(result.found == true) {
                this.found++;
            }
            if(this.totalResults == this.results.length) {
                this.awaitingResults = false;
            }
        }
    }


    /// Handle a keypress in the search input field.
    void handleSearchKeypress(event) {
        if (event.keyCode == KeyCode.ENTER) {
            this.searchUsername();
        }
    }

    /// Sort by a specified field.
    void sortBy(String sort) {
        Map args = this._makeUrlArgs();
        args.remove('page');

        if (sort == null) {
            args.remove('sort');
        } else {
            args['sort'] = sort;
        }

        this._router.go('search',
                        this._rp.route.parameters,
                        queryParameters: args);
    }

    /// Get a query parameter as an int.
    void _getQPInt(value, [defaultValue]) {
        if (value != null) {
            return int.parse(value);
        } else {
            return defaultValue;
        }
    }

    /// Get a query parameter as a string.
    void _getQPString(value, [defaultValue]) {
        if (value != null) {
            return Uri.decodeComponent(value);
        } else {
            return defaultValue;
        }
    }

    /// Make a map of arguments for a URL query string.
    void _makeUrlArgs() {
        var args = new Map<String>();

        // Create query, page, and sort URL args.
        if (this.currentPage != 1) {
            args['page'] = this.currentPage.toString();
        }

        if (this.query != null && !this.query.trim().isEmpty) {
            args['query'] = this.query;
        }

        if (this.resultsPerPage != 10) {
            args['rpp'] = this.resultsPerPage.toString();
        }

        if (this.sort != null) {
            args['sort'] = this.sort;
        }

        return args;
    }

    /// Take a map of query parameters and parse/load into member variables.
    void _parseQueryParameters(qp) {
        this.error = null;

        // Set up query and paging URL args.
        this.currentPage = this._getQPInt(qp['page'], 1);
        this.query = this._getQPString(qp['query']);
        this.resultsPerPage = this._getQPInt(qp['rpp'], 10);


        // Set up breadcrumbs.
        if (this.query == null) {
            this.crumbs = [
                new Breadcrumb('HGProfiler', '/'),
                new Breadcrumb('Usernames'),
            ];
            this._ts.title = 'Username';
        } else {
            this.crumbs = [
                new Breadcrumb('HGProfiler', '/'),
                new Breadcrumb('Usernames', '/username'),
                new Breadcrumb('"' + this.query + '"'),
            ];
            this._ts.title = 'Username "${this.query}"';
        }

        // Set up sort orders.
        this.sort = this._getQPString(qp['sort']);

        Map sortDescriptions = {
            'post_date_tdt': 'Post Date (Old→New)',
            '-post_date_tdt': 'Post Date (New→Old)',
            'username_s': 'Username (A→Z)',
            '-username_s': 'Username (Z→A)',
        };

        if (sortDescriptions.containsKey(this.sort)) {
            this.sortDescription = sortDescriptions[this.sort];
        } else {
            this.sortDescription = 'Most Relevant';
        }
    }

    /// Listen for changes in route parameters.
    void _routeListener(Event e) {
        this._parseQueryParameters(e.queryParameters);

        if (this.query == null || this.query.trim().isEmpty) {
            this.results = new List();
        } else {
            this._fetchSearchResults();
        }
    }

    /// Listen for updates from background workers.
    void _workerListener(Event e) {
        Map job = JSON.decode(e.data);

        if (this.backgroundTask == null && job['queue'] == 'index' &&
            (job['status'] == 'started' || job['status'] == 'progress')) {

            job['Description'] = '(Loading Description...)';
            this.backgroundTask = job;

            this._api
                .get('/api/tasks/job/${job["id"]}', needsAuth: true)
                .then((response) {
                    String description = response.data['description'];
                    this.backgroundTask['description'] = description;
                });
        } else if (this.backgroundTask['id'] == job['id']) {
            if (job['status'] == 'progress') {
                this.backgroundTask['progress'] = job['progress'];
            } else if (job['status'] == 'finished') {
                this.backgroundTask = null;
            }
        }
    }

    /// Get a reference to this element.
    void onShadowRoot(ShadowRoot shadowRoot) {
        this._inputEl = this._element.querySelector('.search-username-form input');
        this._inputEl.focus();
    }
}
