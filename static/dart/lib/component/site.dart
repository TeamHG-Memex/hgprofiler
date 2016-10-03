import 'dart:async';
import 'dart:html';
import 'dart:convert';
import 'dart:math' as math;

import 'package:angular/angular.dart';
import 'package:bootjack/bootjack.dart';
import 'package:dquery/dquery.dart';

import 'package:hgprofiler/query_watcher.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/pager.dart';
import 'package:hgprofiler/model/result.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/model/site.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/sse.dart';

/// A component for viewing and modifying sites.
@Component(
    selector: 'site',
    templateUrl: 'packages/hgprofiler/component/site.html',
    useShadowDom: false
)
class SiteComponent extends Object
                    implements ShadowRootAware {

    String siteError;
    List<Breadcrumb> crumbs = [
        new Breadcrumb('Profiler', '/'),
        new Breadcrumb('Sites', '/site'),
    ];
    int deleteSiteId;
    String dialogTitle;
    String dialogClass;
    int editSiteId;
    final Element _element;
    List<String> keys;
    int loading = 0;
    List<Map> messages = new List<Map>();
    String newSiteName;
    String newSiteCategory;
    String newSiteCategoryDescription = 'Select a category';
    String newSiteUrl;
    String newSiteMatchType;
    String newSiteMatchExpr;
    Map<String,String> matchTypes;
    List<List<String>> matchTypesList;
    String newSiteTestUsernamePos;
    String newSiteTestUsernameNeg;
    String newSiteStatusCode;
    Pager pager;
    Result result;
    String query;
    Result screenshotResult;
    String screenshotClass;
    String screenshotUsername;
    Map<String,Site> sites;
    List<String> siteCategories;
    List<String> siteIds;
    bool showAdd = false;
    bool submittingSite = false;
    String testError;
    int testSiteId;
    String siteValidColor = '#dff0d8';
    String siteInvalidColor = '#f2dede';
    bool testing = true;
    int totalValid;
    int totalInvalid;
    int totalSites;
    int totalTested;
    int totalTestedPercent;
    String trackerId;
    List<String> trackerIds = new List<String>();
    Map<String, int> siteTestTrackers = new Map<String, int>();

    InputElement _inputEl;
    QueryWatcher _queryWatcher;

    final RestApiController api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    SiteComponent(this.api, this._element, this._rp, this._sse, this._ts) {
        this._ts.title = 'Sites';

        RouteHandle rh = this._rp.route.newHandle();
        this._queryWatcher = new QueryWatcher(
            rh,
            ['page', 'rpp'],
            this.fetchCurrentPage
        );

        // Add event listeners...
        UnsubOnRouteLeave(rh, [
            this._sse.onSite.listen(this._siteListener),
            this._sse.onResult.listen(this._resultListener),
        ]);

        this._fetchCategories();
        this._fetchMatchTypes();
        this.fetchCurrentPage();
    }

    /// Generate random string
    String randAlphaNumeric(int length) {
        math.Random rnd = new math.Random();
    List<int> values = new List<int>.generate(32, (i) => rnd.nextInt(256));
    //return(CryptoUtils.bytesToBase64(values).replaceAll(new RegExp('[=/+]'), ''));
    String str = BASE64.encode(values).replaceAll(new RegExp('[=/+]'), '').substring(0, length);
    return str;
    }

    /// Show the "add site" dialog.
    void showAddDialog(String mode) {
        if(mode == 'edit') {
            this.dialogTitle = 'Edit Site';
            this.dialogClass = 'panel-info';
        } else {
            this.dialogTitle = 'Add Site';
            this.dialogClass = 'panel-success';
            this.newSiteName = null;
            this.newSiteCategory = null;
            this.newSiteStatusCode = null;
            this.newSiteMatchType = 'text';
            this.newSiteMatchExpr = '';
            this.newSiteTestUsernamePos = null;
            this.newSiteTestUsernameNeg = this.randAlphaNumeric(16);
            this.newSiteCategoryDescription = 'Select a category';
            this.newSiteUrl = null;
            this.editSiteId = null;
        }
        this.showAdd = true;
        this.siteError = null;

        this._inputEl = this._element.querySelector('#site-name');
        if (this._inputEl != null) {
            // Allow Angular to digest showAdd before trying to focus. (Can't
            // focus a hidden element.)
            new Timer(new Duration(milliseconds: 100), () => this._inputEl.focus());
        }
    }

    /// Get a reference to this element.
    void onShadowRoot(ShadowRoot shadowRoot) {
        this._inputEl = this._element.querySelector('#site-name');
    }

    /// Hide the add/edit sites dialog.
    void hideAddDialog() {
        this.showAdd = false;
    }

    /// Select a category in the "Add Site" form.
    void setSiteCategory(String category) {
        this.newSiteCategory = category;
        String categoryHuman = category.replaceRange(0, 1, category[0].toUpperCase());
        this.newSiteCategoryDescription = categoryHuman;
    }

    /// Select a match type in the "Add Site" form.
    void setSiteMatchType(String matchType) {
        this.newSiteMatchType = matchType;
    }

    /// Set site for deletion and show confirmation modal
    void setDeleteId(String id_) {
        this.deleteSiteId = id_;
        String selector = '#confirm-delete-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        Modal.wire(modalDiv).show();
    }

    /// Show test sites dialog.
    void showTestSitesDialog() {
        String selector = '#test-sites-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        this.fetchCurrentPage();
        Modal.wire(modalDiv).show();
    }

    /// Set site for deletion and show confirmation modal
    void showTestSiteDialog(String id_) {
        this.testSiteId = id_;
        this.testing = false;
        this.result = null;
        this.testError = null;
        String selector = '#test-site-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        Modal.wire(modalDiv).show();

        this._inputEl = this._element.querySelector('#username-query');
        if (this._inputEl != null) {
            // Allow Angular to digest showTestDialog before trying to focus. (Can't
            // focus a hidden element.)
            // Modals take around a second to render.
            new Timer(new Duration(seconds:1.2), () => this._inputEl.focus());
        }
    }

    /// Set site to be edited and show add/edit dialog.
    void editSite(int id_) {
        this.newSiteName = this.sites[id_].name;
        this.setSiteCategory(this.sites[id_].category);
        this.newSiteMatchType = this.sites[id_].matchType;
        this.newSiteMatchExpr = this.sites[id_].matchExpr;
        this.newSiteStatusCode = this.sites[id_].statusCode?.toString() ?? '';
        this.newSiteTestUsernamePos = this.sites[id_].testUsernamePos;
        this.newSiteTestUsernameNeg = this.sites[id_].testUsernameNeg;
        this.newSiteUrl = this.sites[id_].url;
        this.editSiteId = id_;
        this.showAddDialog('edit');
    }

    void setScreenshotResult(int id, String type) {
        if (type == 'pos') {
            this.screenshotResult = this.sites[id].testResultPos;
            this.screenshotUsername = this.sites[id].testUsernamePos;
        } else if (type == 'neg') {
            this.screenshotResult = this.sites[id].testResultNeg;
            this.screenshotUsername = this.sites[id].testUsernameNeg;
        }

        // Formatting
        if (this.screenshotResult.status == 'f') {
            this.screenshotClass = 'found';
        }
        else if (this.screenshotResult.status == 'n') {
            this.screenshotClass = 'not-found';
        }
        else if (this.screenshotResult.status == 'e') {
            this.screenshotClass = 'error';
        }
    }

    /// Fetch a page of profiler sites.
    void fetchCurrentPage() {
        this.loading++;
        String pageUrl = '/api/site/';
        Map urlArgs = {
            'page': this._queryWatcher['page'] ?? '1',
            'rpp': this._queryWatcher['rpp'] ?? '10',
        };

        this.api
            .get(pageUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                this.sites = new Map<String,Site>();

                response.data['sites'].forEach((site) {
                    this.sites[site['id']] = new Site.fromJson(site);
                });
                this.siteIds = new List<String>.from(this.sites.keys);

                this.pager = new Pager(response.data['total_count'],
                                       int.parse(this._queryWatcher['page'] ?? '1'),
                                       resultsPerPage:int.parse(this._queryWatcher['rpp'] ?? '10'));
                this.totalSites = response.data['total_count'];
                this.totalValid = response.data['total_valid_count'];
                this.totalInvalid = response.data['total_invalid_count'];
                this.totalTested = response.data['total_tested_count'];
                this.totalTestedPercent = ((this.totalTested / this.totalSites) * 100).round();

            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {this.loading--;});
    }

    // Fetch list of site categories.
    void _fetchCategories() {
        this.loading++;
        String categoriesUrl = '/api/site/categories';
        this.siteCategories = new List();
        Map urlArgs = new Map();

        this.api
            .get(categoriesUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                response.data['categories'].forEach((category) {
                    this.siteCategories.add(category);

                });
                this.siteCategories.sort();
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    // Fetch list of map of match types.
    void _fetchMatchTypes() {
        this.loading++;
        String url = '/api/site/match-types';
        this.matchTypes = new Map<String,String>();
        this.matchTypesList = new List<List<String>>();

        this.api
            .get(url, needsAuth: true)
            .then((response) {
                this.matchTypes = new Map.from(response.data['match_types']);
                List<String> keys = new List.from(this.matchTypes.keys);
                keys.sort();
                this.matchTypesList = new List<List<String>>();
                for (String key in keys) {
                    matchTypesList.add([key, this.matchTypes[key]]);
                }
                return matchTypes;
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    /// Validate site input form
    bool _validateSiteInput() {
        bool result = true;

        if (this.newSiteCategory == '' || this.newSiteCategory == null) {
            this.siteError = 'You must select a site category.';
            result = false;
        }

        try {
            int code = int.parse(this.newSiteStatusCode);
        } on FormatException {
            this.siteError = 'Status code must be a number.';
            result = false;
        } on ArgumentError {
            this.siteError = 'Status code must be a number.';
            result = false;
        }

        if (this.newSiteUrl == '' || this.newSiteUrl == null) {
            this.siteError = 'You must enter a URL for the site.';
            result = false;
        }

        if (this.newSiteName == '' || this.newSiteName == null) {
            this.siteError = 'You must enter a name for the site.';
            result = false;
        }

        if (this.newSiteTestUsernamePos == '' || this.newSiteTestUsernamePos == null) {
            this.siteError = 'You must enter a test username (pos).';
            result = false;
        }

        if (this.newSiteTestUsernameNeg == '' || this.newSiteTestUsernameNeg == null) {
            this.siteError = 'You must enter a test username (neg).';
            result = false;
        }

        return result;
    }

    void _colorSiteRow(String siteId, String color) {
        Element siteRow = this._element.querySelector('#tr-${siteId}');
        siteRow.style.background = color;
    }

    String _getSiteRowColor(String siteId) {
        Element siteRow = this._element.querySelector('#tr-${siteId}');
        return siteRow.style.background;
    }

    /// Submit a new site.
    void addSite(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/site/';
        this.siteError = null;
        this.submittingSite = true;
        this.loading++;

        // Validate input
        bool valid = this._validateSiteInput();
        if(!valid) {
            this.submittingSite = false;
            resetButton();
            this.loading--;
            return;
        }

        Map site = {
            'name': this.newSiteName,
            'url': this.newSiteUrl,
            'category': this.newSiteCategory,
            'status_code': int.parse(this.newSiteStatusCode, onError: (_) => null),
            'match_expr': this._nullString(this.newSiteMatchExpr),
            'match_type': this._nullString(this.newSiteMatchType),
            'test_username_pos': this.newSiteTestUsernamePos,
            'test_username_neg': this.newSiteTestUsernameNeg,
        };

        Map body = {
            'sites': [site]
        };

        this.api
            .post(pageUrl, {'sites': [site]}, needsAuth: true)
            .then((response) {
                String msg = 'Added site ${this.newSiteName}';
                this._showMessage(msg, 'success', 3, true);
                this.fetchCurrentPage();
                this.showAdd = false;
            })
            .catchError((response) {
                this.siteError = response.data['message'];
            })
            .whenComplete(() {
                this.submittingSite = false;
                this.loading--;
                resetButton();
            });
    }

    /// Trigger add site when the user presses enter in the site input.
    void handleAddSiteKeypress(Event e) {
        if (e.charCode == 13) {
            addSite();
        }
    }


    /// Trigger test site when the user presses enter in the test site input.
    void handleTestSiteKeypress(Event e) {
        if (e.charCode == 13) {
            testSite();
        }
    }



   /// Convert string to camel case.
   String toCamelCase(String input, String separator) {
        List components = input.split(separator);
        if(components.length > 1) {
            String camelCase = components[0];
            for(var i=1; i < components.length; i++) {
                String initial = components[i].substring(0, 1).toUpperCase();
                String word = initial + components[i].substring(1);
                camelCase += word;
            }
            return camelCase;
        }
        return input;
    }

    /// Show a notification to the user
    void _showMessage(String text,
                      String type,
                      [int seconds = 3, bool icon]) {

        Map message = {
            'text': text,
            'type': type,
            'icon': icon
        };
        this.messages.add(message);
        if (seconds > 0) {
            new Timer(new Duration(seconds:seconds), () => this.messages.remove(message));
        }
    }

    /// Save an edited site.
    void saveSite(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/site/${this.editSiteId}';
        this.loading++;

        Map site = {
            'name': this.newSiteName,
            'url': this.newSiteUrl,
            'status_code': int.parse(this.newSiteStatusCode, onError: (_) => null),
            'match_expr': this._nullString(this.newSiteMatchExpr),
            'match_type': this._nullString(this.newSiteMatchType),
            'category': this.newSiteCategory,
            'test_username_pos': this.newSiteTestUsernamePos,
            'test_username_neg': this.newSiteTestUsernameNeg,
        };

        this.api
            .put(pageUrl, site, needsAuth: true)
            .then((response) {
                String name = this.sites[this.editSiteId].name;
                this.sites[this.editSiteId] = new Site.fromJson(response.data);
                this.showAdd = false;
                this._showMessage('Updated site ${name}', 'success', 3, true);
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
            });
    }

    /// Save an edited site.
    void saveAndTestSite(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/site/${this.editSiteId}';
        this.loading++;

        Map body = {
            'name': this.newSiteName,
            'url': this.newSiteUrl,
            'status_code': this.newSiteStatusCode,
            'match_type': this.newSiteMatchType,
            'match_expr': this.newSiteMatchExpr,
            'category': this.newSiteCategory,
            'test_username_pos': this.newSiteTestUsernamePos,
            'test_username_neg': this.newSiteTestUsernameNeg,
        };

        this.api
            .put(pageUrl, body, needsAuth: true)
            .then((response) {
                String name = this.sites[editSiteId].name;
                this.sites[this.editSiteId] = new Site.fromJson(response.data);
                this._showMessage('Updated site ${name}', 'success', 3, true);
                this.testSite(editSiteId);
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
            });
    }

    /// Check if site is awaiting result.
    bool awaitingTestResult(int siteId) {
        bool isWaiting = false;
        this.siteTestTrackers.forEach((trackerId, testSiteId) {
            if (siteId == testSiteId) {
                isWaiting = true;
            }
        });
        return isWaiting;
    }

    /// Request test of siteId.
    void testSite(int siteId) {
        this.result = null;
        String pageUrl = '/api/site/${siteId}/job';
        Map job = {'name': 'test'};

        Map urlArgs = {
            'jobs': [job],
        };

        this.api
            .post(pageUrl, urlArgs, needsAuth: true)
            .then((response) {
                String trackerId = response.data['tracker_ids']['${siteId}'];
                this.siteTestTrackers[trackerId] = siteId;
                new Timer(new Duration(seconds:0.1), () => this._inputEl.focus());
            })
            .catchError((response) {
                this.testError = response.data['message'];
            })
            .whenComplete(() {});
    }

    /// Request test of all sites.
    void testAllSites() {
        this.result = null;
        String pageUrl = '/api/site/job/';
        Map job = {'name': 'test'};

        Map urlArgs = {
            'jobs': [job],
        };

        this.api
            .post(pageUrl, urlArgs, needsAuth: true)
            .then((response) {
                response.data['tracker_ids'].forEach((siteId, trackerId) {
                    this.siteTestTrackers[trackerId] = int.parse(siteId);
                });
            })
            .catchError((response) {
                this._showMessage(response.data['message'], 'danger', 3, true);
            })
            .whenComplete(() {});
    }


    /// Delete site specified by deleteSiteId.
    void deleteSite(Event e, dynamic data, Function resetButton) {
        if(this.deleteSiteId == null) {
            return;
        }
        String pageUrl = '/api/site/${this.deleteSiteId}';
        String name = this.sites[deleteSiteId].name;
        this.loading++;

        this.api
            .delete(pageUrl, needsAuth: true)
            .then((response) {
                this._showMessage('Deleted site ${name}', 'success', 3, true);
                this._fetchCurrentPage();
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
                Modal.wire($("#confirm-delete-modal")).hide();
            });
    }

    /// Get the index of a site category element.
    int siteCategoryIndex(String category) {
        int index;
        for (int i = 0; i < this.siteCategories.length; i++) {
            if(category == this.siteCategories[i]) {
                index = i;
                break;
            }
        }
        return index;
    }

    /// Listen for job results.
    void _resultListener(Event e) {
        Map json = JSON.decode(e.data);
        Result result = new Result.fromJson(json);
        this.siteTestTrackers.remove(result.trackerId);
    }

    /// Listen for site updates.
    // Only fetch page when sites are newly created or deleted.
    // ToDo: Create and add sites locally, rather than use fetchCurrentPage()
    // - this requires some conditional logic to determine whether the site should be part
    // of the current paginated view.
    void _siteListener(Event e) {
        Map json = JSON.decode(e.data);

        if (json['error'] == null) {
            if (json['status'] == 'created') {
                this._showMessage('Site "${json["name"]}" created.', 'success', 3);
                this._fetchCurrentPage();
            }
            else if (json['status'] == 'tested') {
                // Remove tracker_id if it is in siteTestTrackers.
                // This will deactivate loading spinner for that site.
                if(json.containsKey('tracker_id')) {
                    this.siteTestTrackers.remove(json['tracker_id']);
                }
                // Don't show notifications for tested sites (this would overload the UI).
                // Temporarily color rows to show they have been updated.
                Site site = new Site.fromJson(json['site']);
                if (this.sites.containsKey(site.id)) {
                    this.sites[site.id] = site;
                    String normColor = this._getSiteRowColor(site.id);

                    if (site.valid == true) {
                        this._colorSiteRow(site.id, this.siteValidColor);
                    } else {
                        this._colorSiteRow(site.id, this.siteInvalidColor);
                    }

                    new Timer(new Duration(seconds:1), () => this._colorSiteRow(site.id, normColor));
                }
            }
            else if (json['status'] == 'updated') {
                Site site = new Site.fromJson(json['site']);
                if (this.sites.containsKey(site.id)) {
                  this.sites[site.id] = site;
                }
                this._showMessage('Site "${json["name"]}" updated.', 'info', 3);
            }
            else if (json['status'] == 'deleted') {
                this._showMessage('Site "${json["name"]}" deleted.', 'danger', 3);
                this._fetchCurrentPage();
            }
        }
    }

    /// Coerce an empty string to null.
    String _nullString(String s) {
        if (s == null) {
            return null;
        } else {
            String sTrim = s.trim();
            return sTrim.isEmpty ? null : sTrim;
        }
    }
}
