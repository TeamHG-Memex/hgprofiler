import 'dart:async';
import 'dart:html';
import 'dart:convert';

import 'package:angular/angular.dart';
import 'package:hgprofiler/authentication.dart';
import 'package:hgprofiler/query_watcher.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/pager.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/mixin/current_page.dart';
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

    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('Sites', '/site'),
    ];

    List<String> keys;
    Map<String,Function> sites;
    List<String> siteIds;
    final Element _element;
    String error;
    String addSiteError;
    String newSite;
    String newSiteCategory;
    String newSiteUrl;
    String newSiteSearchText;
    int newSiteStatusCode;
    List<String> siteCategories;
    Pager pager;
    int loading = 0;
    bool showAdd = false;
    bool submittingSite = false;
    String newSiteCategoryDescription = 'Select a category';

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
    void showAddDialog() {
        this.showAdd = true;
        this.addSiteError = null;

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
        this.newSite = '';
        this.error = null;
    }

    /// Select a category in the "Add Site" form.
    void selectAddSiteCategory(String category) {
        this.newSiteCategory = category;
        String categoryHuman = category.replaceRange(0, 1, category[0].toUpperCase());
        this.newSiteCategoryDescription = categoryHuman;
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
                    this.sites[site['id']] = {
                        'name': site['name'],
                        'url': site['url'],
                        'category': site['category'],
                        'statusCode': site['status_code'],
                        'searchText': site['search_text'],
                        'saveUrl': (v) => this.saveSite(site['id'], 'url', v),
                        'saveName': (v) => this.saveSite(site['id'], 'name', v),
                        'saveCategory': (v) => this.saveSite(site['id'], 'category', this.siteCategories[v]),
                        'saveSearchText': (v) => this.saveSite(site['id'], 'search_text', v),
                        'saveStatusCode': (v) => this.saveSite(site['id'], 'status_code', v),
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
    void addSite() {
        String pageUrl = '/api/site/';
        this.addSiteError = null;
        this.submittingSite = true;
        this.loading++;

        Map site = {
            'name': this.newSite,
            'url': this.newSiteUrl,
            'category': this.newSiteCategory,
        }; 

        if (this.newSiteSearchText != null) {
            site['search_text'] = this.newSiteSearchText;
        }

        if (this.newSiteStatusCode != null) {
            site['satus_code'] = this.newSiteStatusCode;
        }

        Map body = {
            'sites': [site]
        };

        this._api
            .post(pageUrl, body, needsAuth: true)
            .then((response) {
                new Timer(new Duration(seconds:0.1), () {
                    this._inputEl.focus();
                    this.newSite = '';
                    this.newSiteUrl = '';
                    this.newSiteStatusCode = '';
                    this.newSiteSearchText = '';
                });
            })
            .catchError((response) {
                this.addSiteError = response.data['message'];
            })
            .whenComplete(() {
                this.submittingSite = false;
                this.loading--;
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
    void saveSite(String id_, String key, String value) {
        String pageUrl = '/api/site/${id_}';
        this.error = null;
        this.loading++;

        Map body = {
            key: value,
        };

        this._api
            .put(pageUrl, body, needsAuth: true)
            .then((response) {
                key = this.toCamelCase(key, '_');
                this.sites[id_][key] = value;
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    /// Delete site specified by id.
    void deleteSite(String id_) {
        String pageUrl = '/api/site/${id_}';
        this.error = null;
        this.loading++;

        this._api
            .delete(pageUrl, needsAuth: true)
            .then((response) {
                //this.sites.remove(id_);
                //this.siteIds.remove(id_);
                new Future(() {
                    this._fetchCurrentPage();
                });
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
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
