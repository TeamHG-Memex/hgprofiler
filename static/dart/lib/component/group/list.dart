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
import 'package:hgprofiler/mixin/current_page.dart';
import 'package:hgprofiler/model/group.dart';
import 'package:hgprofiler/model/site.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/sse.dart';

/// A component for viewing and modifying credentials.
@Component(
    selector: 'group-list',
    templateUrl: 'packages/hgprofiler/component/group/list.html',
    useShadowDom: false
)
class GroupListComponent extends Object
                    implements ShadowRootAware {

    List<Breadcrumb> crumbs = [
        new Breadcrumb('HGProfiler', '/'),
        new Breadcrumb('Groups', '/group'),
    ];
    bool allSites;
    String addGroupError;
    Map<Map> groups;
    int editingGroupId;
    List<int> editingGroupSiteIds;
    List<String> groupIds;
    final Element _element;
    String error;
    String editSitesError;
    List<CheckboxInputElement> editSiteCheckboxes;
    String newGroupName;
    Pager pager;
    int loading = 0;
    List<Site> sites;
    bool showAdd = false;
    String siteSearch = '';
    bool submittingGroup = false;
    int totalSites;

    InputElement _inputEl;
    Router _router;
    QueryWatcher _queryWatcher;

    final AuthenticationController _auth;
    final RestApiController _api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    GroupListComponent(this._auth, this._api, this._element, 
                       this._router, this._rp, this._sse, this._ts) {

        this._ts.title = 'Groups';

        // Add event listeners...
        RouteHandle rh = this._rp.route.newHandle();
        this._queryWatcher = new QueryWatcher(
            rh,
            ['page', 'rpp'],
            this._fetchCurrentPage
        );

        List<StreamSubscription> listeners = [
            this._sse.onGroup.listen(this._groupListener),
        ];

        //editSiteCheckboxes.forEach((checkbox) {
        //    listeners.add(checkbox.onChange.listen(editSite));
        //});

        // ...and remove event listeners when we leave this route.
        UnsubOnRouteLeave(rh, [
            this._sse.onGroup.listen(this._groupListener),
        ]);
    
        this._fetchSites();
        this._fetchCurrentPage();
            //.then((_) {
            //    String selector = 'input[name="edit-site-checkbox"][type="checkbox"]';
            //    List<CheckboxInputElement> editSiteCheckboxes = querySelectorAll(selector);
            //    editSiteCheckboxes.forEach((checkbox) {
            //        listeners.add(checkbox.onChange.listen(editSite));
            //    });
            //    window.console.debug(editSiteCheckboxes);
            //});
    }

    /// Show the "add profile" dialog.
    void showAddDialog() {
        this.showAdd = true;

        if (this._inputEl != null) {
            // Allow Angular to digest showAdd before trying to focus. (Can't
            // focus a hidden element.)
            new Timer(new Duration(seconds:0.1), () => this._inputEl.focus());
        }
    }

    /// Get a reference to this element.
    void onShadowRoot(ShadowRoot shadowRoot) {
        this._inputEl = this._element.querySelector('.add-group-form input');
    }

    /// Show the "add groups" dialog.
    void hideAddDialog() {
        this.showAdd = false;
        this.newGroup = '';
    }

    /// Fetch a page of profiler groups. 
    Future _fetchCurrentPage() {
        Completer completer = new Completer();
        this.error = null;
        this.loading++;
        String pageUrl = '/api/group/';
        Map urlArgs = {
            'page': this._queryWatcher['page'] ?? '1',
            'rpp': this._queryWatcher['rpp'] ?? '100',
        };
        this.groups = new Map<Map>();

        this._api
            .get(pageUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                this.groupIds = new List<String>();

                response.data['groups'].forEach((group) {
                    this.groups[group['id']] = {
                        'name': group['name'],
                        'sites': new List.generate(
                            group['sites'].length,
                            (index) => new Site.fromJson(group['sites'][index])
                        ),
                        'saveName': (v) => this.saveGroup(group['id'], 'name', v)
                    };
                });
                // Deleting groups affects paging of results, redirect to the final page
                // if the page no longer exists.
                int lastPage = (response.data['total_count']/int.parse(this._queryWatcher['rpp'] ?? '100')).ceil();
                if (lastPage == 0) { 
                    lastPage = 1;
                }
                if (int.parse(this._queryWatcher['page'] ?? '1') > lastPage) {
                    Uri uri = Uri.parse(window.location.toString());
                    Map queryParameters = new Map.from(uri.queryParameters);

                    if (lastPage == 0) {
                        queryParameters.remove('page');
                    } else {
                        queryParameters['page'] = lastPage.toString();
                    }

                    this._router.go('group', {}, queryParameters: queryParameters);

                }

                this.pager = new Pager(response.data['total_count'],
                                       int.parse(this._queryWatcher['page'] ?? '1'),
                                       resultsPerPage: int.parse(this._queryWatcher['rpp'] ?? '100'));
                new Future(() {
                    this.groupIds = new List<String>.from(this.groups.keys);
                });

            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
                completer.complete();
            });
        return completer.future;
    }

    void saveGroup(String id_, String key, String value) {
        String pageUrl = '/api/group/${id_}';
        this.error = null;
        this.loading++;

        Map body = {
            key: value,
        };

        this._api
            .put(pageUrl, body, needsAuth: true)
            .then((response) {
                //this.groups[id_][key] = value;
                this._fetchCurrentPage();
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
            });
    }

    void deleteGroup(String id_) {
        String pageUrl = '/api/group/${id_}';
        this.error = null;
        this.loading++;
        Map body = {};

        this._api
            .delete(pageUrl, urlArgs: {}, needsAuth: true)
            .then((response) {
                this.groups.remove(id_);
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
            });
    }
    
    void editingGroup(int id_) {
        this.error = null;
        this.editingGroupId = id_;
        this.editingGroupSiteIds = new List.generate(
                this.groups[id_]['sites'].length,
                (index) =>  this.groups[id_]['sites'][index].id);
        String selector = 'input[name="site-checkboxes"][type="checkbox"]';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        siteCheckboxes.forEach((checkbox) {
            if (this.editingGroupSiteIds.contains(int.parse(checkbox.value))) {
                checkbox.checked = true;
            } else {
                checkbox.checked = false;
            }
        });
    }

    void editSite() {
        String checkedSelector = 'input[name="edit-site-checkbox"][type="checkbox"]:checked'; 
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(checkedSelector);
        String toggleSelector = '#all-sites-toggle';
        CheckboxInputElement toggleAllSitesCheckbox = this._element.querySelector(toggleSelector);
        if (siteCheckboxes.length == this.totalSites) {
            allSites = true;
        } else {
            allSites = false;
        }
    }

    void saveGroupSites(Event e, dynamic data, Function resetButton) {
        String selector = 'input[name="edit-site-checkbox"][type="checkbox"]:checked';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        window.console.debug(siteCheckboxes);
        this.editingGroupSiteIds = new List();
        siteCheckboxes.forEach((checkbox) {
            this.editingGroupSiteIds.add(checkbox.value);
        });
        this.saveGroup(this.editingGroupId, 'sites', this.editingGroupSiteIds);
        resetButton();
        Modal.wire($("#edit-sites-modal")).hide();
    }

    void toggleSites() {
        String selector = 'input[name="edit-site-checkbox"][type="checkbox"]';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        this.editingGroupSiteIds = new List();
        siteCheckboxes.forEach((checkbox) {
            checkbox.checked = this.allSites;
        });
    }


    void addGroup(Event e, dynamic data, Function resetButton) {
        List<int> sites = new List();
        String pageUrl = '/api/group/';
        this.error = null;
        this.loading++;

        if (this.newGroupName == '' || this.newGroupName == null) {
            this.addGroupError = 'You must enter a name for the group';
        }

        var query  = $('input[name="site-checkboxes"]:checked');
        if (query.length == 0) {
            this.addGroupError = 'You must select at least one site';
        } else {
            query.forEach((checkbox) {
                sites.add(checkbox.value);
            }); }

        Map group  = {
            'name': this.newGroupName,
            'sites': sites
        };
      
        Map body = {
            'groups': [group]
        };

        this._api
            .post(pageUrl, body, needsAuth: true)
            .then((response) {
                this.newGroupName = ''; 
                this.addGroupError = null;
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
                Modal.wire($("#add-group-modal")).hide();
            });
    }


    /// Fetch a page of profiler sites.
    Future _fetchPageOfSites(page) {
        Completer completer = new Completer();
        this.loading++;
        String siteUrl = '/api/site/';
        Map urlArgs = {
            'page': page,
            'rpp': 100,
        };
        int totalCount = 0;
        Map result = new Map();

        this._api
            .get(siteUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                if (response.data.containsKey('total_count')) {
                    this.totalSites = response.data['total_count'];
                }
                response.data['sites'].forEach((site) {
                    if (!this.sites.contains(site)) {
                        this.sites.add(site);
                    }
                });
                this.loading--;
                completer.complete();
            })
            .catchError((response) {
                this.error = response.data['message'];
            });
        return completer.future;
    }

    // Fetch all profiler sites.
    Future _fetchSites() {
        Completer completer = new Completer();
        Map result;
        this.error = null;
        bool finished = false;
        int page = 1;
        this.sites = new List();
        String siteUrl = '/api/site/';
        int totalCount = 0;
        this._fetchPageOfSites(page)
            .then((_) {
                int lastPage = (this.totalSites/100).ceil();
                page++;
                while(page <= lastPage) {
                    this._fetchPageOfSites(page);
                    page++;
                }
                completer.complete();

            });
        return completer.future;
    }

    /// Trigger add group when the user presses enter in the group input.
    void handleAddGroupKeypress(Event e) {
        if (e.charCode == 13) {
            addGroup();
        }
    }

    /// Listen for group updates.
    void _groupListener(Event e) {
        Map json = JSON.decode(e.data);

        window.alert('called');
        if (json['error'] == null) {
            this._fetchCurrentPage();
        } 
    }
}
