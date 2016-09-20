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

    bool allSites;
    List<Breadcrumb> crumbs = [
        new Breadcrumb('Profiler', '/'),
        new Breadcrumb('Groups', '/group'),
    ];
    int deleteGroupId;
    String dialogTitle;
    String dialogClass;
    int editGroupId;
    List<int> editGroupSiteIds;
    final Element _element;
    List<CheckboxInputElement> editSiteCheckboxes;
    String groupError;
    List<String> groupIds;
    Map<Map> groups;
    int loading = 0;
    List<Map> messages = new List<Map>();
    String newGroupName;
    Pager pager;
    bool showAdd = false;
    List<Site> sites;
    String siteSearch = '';
    bool submittingGroup = false;
    int totalSites;

    InputElement _inputEl;
    Router _router; QueryWatcher _queryWatcher;
    final AuthenticationController _auth;
    final RestApiController _api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    GroupListComponent(this._auth, this._api, this._element,
                       this._router, this._rp, this._sse, this._ts) {

        this._ts.title = 'Groups';

        RouteHandle rh = this._rp.route.newHandle();
        this._queryWatcher = new QueryWatcher(
            rh,
            ['page', 'rpp'],
            this._fetchCurrentPage
        );

        // Add event listeners...
        UnsubOnRouteLeave(rh, [
            this._sse.onGroup.listen(this._groupListener),
        ]);

        this._fetchSites();
        this._fetchCurrentPage();
    }

    /// Show the "add profile" dialog.
    void showAddDialog(String mode) {
        if(mode == 'edit') {
            this.dialogTitle = 'Edit Group';
            this.dialogClass = 'panel-info';
        } else {
            this.dialogTitle = 'Add Group';
            this.dialogClass = 'panel-success';
            this.newGroupName = '';
            String selector = 'input[name="add-site-checkbox"][type="checkbox"]';
            List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
            siteCheckboxes.forEach((checkbox) {
                checkbox.checked = false;
            });
            String toggleSelector = '#all-sites-toggle[type="checkbox"]';
            CheckboxInputElement toggleSiteCheckbox = this._element.querySelector(toggleSelector);
            toggleSiteCheckbox.checked = false;
        }

        this.showAdd = true;
        this.groupError = null;

        this._inputEl = this._element.querySelector('#group-name');
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
        this.editGroupId = null;
    }

    /// Fetch a page of profiler groups.
    Future _fetchCurrentPage() {
        Completer completer = new Completer();
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
                    };
                });
                this.groupIds = new List<String>.from(this.groups.keys);

                this.pager = new Pager(response.data['total_count'],
                                       int.parse(this._queryWatcher['page'] ?? '1'),
                                       resultsPerPage: int.parse(this._queryWatcher['rpp'] ?? '100'));

            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
                completer.complete();
            });
        return completer.future;
    }


    //void saveGroup(String id_, String key, dynamic value) {
    void saveGroup(Event e, dynamic data, Function resetButton) {
        String selector = 'input[name="add-site-checkbox"][type="checkbox"]:checked';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        this.editGroupSiteIds = new List();
        siteCheckboxes.forEach((checkbox) {
            this.editGroupSiteIds.add(checkbox.value);
        });

        // Validate input
        bool valid = this._validateGroupInput();
        if(!valid) {
            this.submittingGroup = false;
            resetButton();
            this.loading--;
            return;
        }


        String pageUrl = '/api/group/${this.editGroupId}';
        this.loading++;

        Map body = {
            'name': this.newGroupName,
            'sites':  this.editGroupSiteIds
        };

        this._api
            .put(pageUrl, body, needsAuth: true)
            .then((response) {
                String name = this.sites[editGroupId]['name'];
                this._fetchCurrentPage();
                this.showAdd = false;
                this._showMessage('Updated group ${this.newGroupName}', 'info', 3, true);
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

    /// Set group for deletion and show confirmation modal
    void setDeleteId(String id_) {
        this.deleteGroupId = id_;
        String selector = '#confirm-delete-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        Modal.wire(modalDiv).show();
    }

    /// Delete group specified by deleteGroupId.
    void deleteGroup(Event e, dynamic data, Function resetButton) {
        if(this.deleteGroupId == null) {
            return;
        }

        String pageUrl = '/api/group/${this.deleteGroupId}';
        String name = this.groups[deleteGroupId]['name'];
        this.loading++;
        Map body = {};

        this._api
            .delete(pageUrl, urlArgs: {}, needsAuth: true)
            .then((response) {
                this._showMessage('Deleted group ${name}', 'danger', 3, true);
                this._fetchCurrentPage();
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {
                this.loading--;
                Modal.wire($("#confirm-delete-modal")).hide();
                resetButton();
            });
    }

    /// Set group to be edited and show add/edit dialog.
    void editGroup(int id_) {
        this.newGroupName = this.groups[id_]['name'];
        this.siteSearch = '';
        this.editGroupId = id_;
        this.showAddDialog('edit');
        this.editGroupSiteIds = new List.generate(
                this.groups[id_]['sites'].length,
                (index) =>  this.groups[id_]['sites'][index].id);
        String selector = 'input[name="add-site-checkbox"][type="checkbox"]';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        siteCheckboxes.forEach((checkbox) {
            if (this.editGroupSiteIds.contains(int.parse(checkbox.value))) {
                checkbox.checked = true;
            } else {
                checkbox.checked = false;
            }
        });
    }

    void toggleAddSites() {
        String selector = 'input[name="add-site-checkbox"][type="checkbox"]';
        List<CheckboxInputElement> siteCheckboxes = this._element.querySelectorAll(selector);
        this.editGroupSiteIds = new List();
        siteCheckboxes.forEach((checkbox) {
            checkbox.checked = this.allSites;
        });
    }

    void _validateGroupInput() {

        if (this.newGroupName == '' || this.newGroupName == null) {
            this.groupError = 'You must enter a name for the group';
            return  false;
        }

        var query  = $('input[name="add-site-checkbox"]:checked');
        if (query.length == 0) {
            this.groupError = 'You must select at least one site';
            return false;
        }

        return true;
    }

    void addGroup(Event e, dynamic data, Function resetButton) {
        List<int> sites = new List();
        this.siteSearch = '';
        String pageUrl = '/api/group/';
        this.loading++;

        // Validate input
        bool valid = this._validateGroupInput();
        if(!valid) {
            this.submittingGroup = false;
            resetButton();
            this.loading--;
            return;
        }


        var query  = $('input[name="add-site-checkbox"]:checked');
        query.forEach((checkbox) {
            sites.add(checkbox.value);
        });

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
                String msg = 'Added group ${this.newGroupName}';
                this._showMessage(msg, 'success', 3, true);
                this._fetchCurrentPage();
                this.showAdd = false;
            })
            .catchError((response) {
                this.groupError = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
                this.submittingGroup = false;
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
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            });
        return completer.future;
    }

    // Fetch all profiler sites.
    Future _fetchSites() {
        Completer completer = new Completer();
        Map result;
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
        window.console.debug(json);

        if (json['error'] == null) {
            if (json['status'] == 'created') {
                this._showMessage('Group "${json["name"]}" created.', 'success', 3);
            }
            else if (json['status'] == 'updated') {
                this._showMessage('Group "${json["name"]}" updated.', 'info', 3);
            }
            else if (json['status'] == 'deleted') {
                this._showMessage('Group "${json["name"]}" deleted.', 'danger', 3);
            }
            this._fetchCurrentPage();
        }
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
}
