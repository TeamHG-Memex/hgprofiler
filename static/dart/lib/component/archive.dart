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
import 'package:hgprofiler/model/archive.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/sse.dart';

/// A component for viewing and modifying result result archives.
@Component(
    selector: 'archive',
    templateUrl: 'packages/hgprofiler/component/archive.html',
    useShadowDom: false
)
class ArchiveComponent extends Object {

    List<Breadcrumb> crumbs = [
        new Breadcrumb('Profiler', '/'),
        new Breadcrumb('Archive', '/archive'),
    ];

    List<String> keys;
    Map<String, Archive> archives;
    List<String> archiveIds;
    int deleteArchiveId;
    final Element _element;
    String error;
    int loading = 0;
    List<Map> messages = new List<Map>();
    Pager pager;

    Router _router;
    QueryWatcher _queryWatcher;

    final AuthenticationController _auth;
    final RestApiController api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    ArchiveComponent(this._auth, this.api, this._element, this._router, this._rp, this._sse, this._ts) {
        this._ts.title = 'Archived Results';

        RouteHandle rh = this._rp.route.newHandle();
        this._queryWatcher = new QueryWatcher(
            rh,
            ['page', 'rpp'],
            this._fetchCurrentPage
        );

        // Add event listeners...
        UnsubOnRouteLeave(rh, [
            this._sse.onArchive.listen(this._archiveListener),
        ]);
        this._fetchCurrentPage();
    }


    /// Fetch a page of profiler result archives.
    void _fetchCurrentPage() {
        this.error = null;
        this.loading++;
        String pageUrl = '/api/archive/';
        Map urlArgs = {
            'page': this._queryWatcher['page'] ?? '1',
            'rpp': this._queryWatcher['rpp'] ?? '10',
        };

        this.api
            .get(pageUrl, urlArgs: urlArgs, needsAuth: true)
            .then((response) {
                this.archives = new Map<String, Archive>();

                response.data['archives'].forEach((archive) {
                    this.archives[archive['id']] = new Archive.fromJson(archive);
                });


                this.pager = new Pager(response.data['total_count'],
                                       int.parse(this._queryWatcher['page'] ?? '1'),
                                       resultsPerPage:int.parse(this._queryWatcher['rpp'] ?? '10'));

                this.archiveIds = new List<String>.from(this.archives.keys);
            })
            .catchError((response) {
                String msg = response.data['message'];
                this._showMessage(msg, 'danger');
            })
            .whenComplete(() {this.loading--;});
    }


    // Listen for archive updates.
    void _archiveListener(Event e) {
        Map json = JSON.decode(e.data);

        if (json['error'] == null) {
            if (json['status'] == 'created') {
                this._showMessage('Archive for username ${json["name"]} created.', 'success', 3);
            }
            else if (json['status'] == 'updated') {
                this._showMessage('Archive for "${json["name"]}" updated.', 'info', 3);
            }
            else if (json['status'] == 'deleted') {
                this._showMessage('Archive for "${json["name"]}" deleted.', 'danger', 3);
            }
            this._fetchCurrentPage();
        }
    }

    /// Set archive for deletion and show confirmation modal.
    void setDeleteId(String id_) {
        this.deleteArchiveId = id_;
        String selector = '#confirm-delete-modal';
        DivElement modalDiv = this._element.querySelector(selector);
        Modal.wire(modalDiv).show();
    }

    /// Delete archive specified by deleteArchiveId.
    void deleteArchive(Event e, dynamic data, Function resetButton) {
        String pageUrl = '/api/archive/${this.deleteArchiveId}';
        this.loading++;
        String name = this.archives[deleteArchiveId].username;

        this.api
            .delete(pageUrl, needsAuth: true)
            .then((response) {
                this._showMessage('Deleted archive ${name}', 'danger', 3, true);
                this._fetchCurrentPage();
            })
            .catchError((response) {
                this.error = response.data['message'];
            })
            .whenComplete(() {
                this.loading--;
                resetButton();
                Modal.wire($("#confirm-delete-modal")).hide();
            });
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
