import 'dart:async';
import 'dart:html';
import 'dart:convert';

import 'package:angular/angular.dart';
import 'package:bootjack/bootjack.dart';
import 'package:dquery/dquery.dart';

import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/query_watcher.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/pager.dart';
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

    String addSiteError;
    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('Sites', '/site'),
    ];
    int deleteSiteId;
    String dialogTitle;
    String dialogClass;
    int editingSiteId;
    final Element _element;
    String error;
    List<String> keys;
    int loading = 0;
    String newSiteName;
    String newSiteCategory;
    String newSiteCategoryDescription = 'Select a category';
    String newSiteUrl;
    String newSiteSearchText;
    int newSiteStatusCode;
    Pager pager;
    Map<String,Function> sites;
    List<String> siteCategories;
    List<String> siteIds;
    bool showAdd = false;
    bool submittingSite = false;
    List<String> successMsgs = []; 

    InputElement _inputEl;
    Router _router;
    QueryWatcher _queryWatcher;

    final AuthenticationController _auth;
    final RestApiController _api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    SiteComponent(this._auth, this._api, this._element, this._router, this._rp, this._sse, this._ts) {
        this._ts.title = 'Sites';

        // Add event listeners...
        RouteHandle rh = this._rp.route.newHandle();
        this._queryWatcher = new QueryWatcher(
            rh,
            ['page', 'rpp'],
            this._fetchCurrentPage
        );

        List<StreamSubscription> listeners = [
            this._sse.onSite.listen(this._siteListener),
        ];
        // ...and remove event listeners when we leave this route.
        UnsubOnRouteLeave(rh, [
            this._sse.onSite.listen(this._siteListener),
        ]);
        this._fetchCategories();
        this._fetchCurrentPage();
    }

    /// Show the "add profile" dialog.
    void showAddDialog(string mode) {
        if(mode == 'edit') {
            this.dialogTitle = 'Edit Group';
            this.dialogClass = 'panel-info';
        } else {
            this.dialogTitle = 'Add Group';
            this.dialogClass = 'panel-success';
        }
        this.showAdd = true;
        this.addSiteError = null;
        this.error = null;

        this._inputEl = this._element.querySelector('#siteName');
        if (this._inputEl != null) {
            // Allow Angular to digest showAdd before trying to focus. (Can't
            // focus a hidden element.)
            new Timer(new Duration(seconds:0.1), () => this._inputEl.focus());
        }
    }

    /// Get a reference to this element.
    void onShadowRoot(ShadowRoot shadowRoot) {
        this._inputEl = this._element.querySelector('.add-site-form input');
    }

    /// Show the "add sites" dialog.
    void hideAddDialog() {
        this.showAdd = false;
        this.newSiteName = null;
        this.newSiteCategory = null;
        this.newSiteStatusCode = null;
        this.newSiteSearchText = null;
        this.newSiteCategoryDescription = 'Select a category';
        this.newSiteUrl = null;
        this.editingSiteId = null;
        this.error = null;
    }

    /// Select a category in the "Add Site" form.
    void setSiteCategory(String category) {
        this.newSiteCategory = category;
        String categoryHuman = category.replaceRange(0, 1, category[0].toUpperCase());
        this.newSiteCategoryDescription = categoryHuman;
    }

    /// Set site for deletion and show confirmation modal
    void setDeleteId(String id_) {
        this.deleteSiteId = id_;
        String selector = '#confirm-delete-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        Modal.wire(modalDiv).show();
    }

    /// Set site to be edited and show add/edit dialog.    
    void editingSite(int id_) {
        this.error = null;
        this.newSiteName = this.sites[id_]['name'];
        this.setSiteCategory(this.sites[id_]['category']);
        this.newSiteSearchText = this.sites[id_]['searchText'];
        this.newSiteStatusCode = this.sites[id_]['statusCode'];
        this.newSiteUrl = this.sites[id_]['url'];
        this.editingSiteId = id_;
        this.showAddDialog('edit');
    }

    /// Fetch a page of profiler sites. 
    void _fetchCurrentPage() {
        this.error = null;
        this.loading++;
        String pageUrl = '/api/site/';
        Map urlArgs = {
            'page': this._queryWatcher['page'] ?? '1',
            'rpp': this._queryWatcher['rpp'] ?? '10',
        };

        this.sites = new Map<String>();

        this._api
            .get(pageUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                this.sites = new Map<String>();

                response.data['sites'].forEach((site) {
                    window.console.debug(site);
                    this.sites[site['id']] = {
                        'name': site['name'],
                        'url': site['url'],
                        'category': site['category'],
                        'statusCode': site['status_code'],
                        'searchText': site['search_text'],
                    };

                });
                // Deleting sites affects paging of results, redirect to the final page
                // if the page no longer exists.
                int lastPage = (response.data['total_count']/int.parse(this._queryWatcher['rpp'] ?? '10')).ceil();

                if (int.parse(this._queryWatcher['page'] ?? '1') > lastPage) {
                    Uri uri = Uri.parse(window.location.toString());
                    Map queryParameters = new Map.from(uri.queryParameters);

                    if (lastPage == 0) {
                        queryParameters.remove('page');
                    } else {
                        queryParameters['page'] = lastPage.toString();
                    }

                    this._router.go('site', {}, queryParameters: queryParameters);

                }

                this.pager = new Pager(response.data['total_count'],
                                       int.parse(this._queryWatcher['page'] ?? '1'),
                                       resultsPerPage:int.parse(this._queryWatcher['rpp'] ?? '10'));

                new Future(() {
                    this.siteIds = new List<String>.from(this.sites.keys);
                });
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {this.loading--;});
    }

    // Fetch list of site categories.
    void _fetchCategories() {
        this.loading++;
        String categoriesUrl = '/api/site/categories';
        this.siteCategories = new List();
        Map urlArgs = new Map();

        this._api
            .get(categoriesUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                response.data['categories'].forEach((category) {
                    this.siteCategories.add(category);

                });
                this.siteCategories.sort();
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    /// Submit a new site.
    void addSite(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/site/';
        this.addSiteError = null;
        this.submittingSite = true;
        this.loading++;

        // Validate input
        bool valid = true;

        if (this.newSiteCategory == '' || this.newSiteCategory == null) {
            this.addSiteError = 'You must select a site category.';
            valid = false;
        }

        if (this.newSiteSearchText == '' || this.newSiteSearchText == null) {
            this.addSiteError = 'You must enter search text for the site.';
            valid = false;
        }

        try {
            int code = int.parse(this.newSiteStatusCode);
        } on FormatException {
            this.addSiteError = 'Status code must be a number.';
            valid = false;
        } on ArgumentError {
            this.addSiteError = 'Status code must be a number.';
            valid = false;
        }

        if (this.newSiteUrl == '' || this.newSiteUrl == null) {
            this.addSiteError = 'You must enter a URL for the site.';
            valid = false;
        }

        if (this.newSiteName == '' || this.newSiteName == null) {
            this.addSiteError = 'You must enter a name for the site.';
            valid = false;
        }


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
        }; 

        if (this.newSiteSearchText != null) {
            site['search_text'] = this.newSiteSearchText;
        }

        if (this.newSiteStatusCode != null) {
            site['status_code'] = this.newSiteStatusCode;
        }

        Map body = {
            'sites': [site]
        };

        this._api
            .post(pageUrl, body, needsAuth: true)
            .then((response) {
            })
            .catchError((response) {
                this.addSiteError = response.data['message'];
                this.loading--;
                resetButton();
            })
            .whenComplete(() {
                this._inputEl.focus();
                this.submittingSite = false;
                this.loading--;
                resetButton();
                if (this.addSiteError == null) {
                    this.newSiteName = '';
                    this.newSiteUrl = '';
                    this.newSiteStatusCode = '';
                    this.newSiteSearchText = '';
                    this.showAdd = false;
                    String msg = 'New site added site';
                    this.successMsgs.add(msg);
                    new Timer(new Duration(seconds:3), () => this.successMsgs.remove(msg));
                }
            });
    }

    /// Trigger add site when the user presses enter in the site input.
    void handleAddSiteKeypress(Event e) {
        if (e.charCode == 13) {
            addSite();
        }
    }

    /// Listen for site updates.
    void _siteListener(Event e) {
        Map json = JSON.decode(e.data);

        if (json['error'] == null) {
            this._fetchCurrentPage();
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

    /// Save an edited site.
    void saveSite(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/site/${this.editingSiteId}';
        this.error = null;
        this.loading++;

        
        Map body = {
            'name': this.newSiteName,
            'url': this.newSiteUrl,
            'status_code': this.newSiteStatusCode,
            'search_text': this.newSiteSearchText,
            'category': this.newSiteCategory,
        };

        this._api
            .put(pageUrl, body, needsAuth: true)
            .then((response) {
                this._fetchCurrentPage();
            })
            .catchError((response) {
                this.error = response.data['message'];
                resetButton();
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
                this.showAdd = false;
                String msg = 'Updated group';
                this.successMsgs.add(msg);
                new Timer(new Duration(seconds:3), () => this.successMsgs.remove(msg));
            });
    }

    /// Delete group specified by deleteGroupId.
    void deleteSite(Event e, dynamic data, Function resetButton) {
        if(this.deleteSiteId == null) {
            return;
        }
        this.error = null;
        String pageUrl = '/api/site/${this.deleteSiteId}';
        this.loading++;

        this._api
            .delete(pageUrl, needsAuth: true)
            .then((response) {
                this.sites.remove(this.deleteSiteId);
                this.siteIds.remove(this.deleteSiteId);
                new Future(() {
                    this._fetchCurrentPage();
                });
                String msg = 'Deleted site ID "${this.deleteSiteId}"';
                this.successMsgs.add(msg);
                new Timer(new Duration(seconds:3), () => this.successMsgs.remove(msg));
            })
            .catchError((response) {
                this.error = response.data['message'];
                resetButton();
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
}
