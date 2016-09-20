import 'dart:async';
import 'dart:convert';
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/component/breadcrumbs.dart';
import 'package:hgprofiler/component/title.dart';
import 'package:hgprofiler/rest_api.dart';
import 'package:hgprofiler/sse.dart';

/// A controller for administering the application.
@Component(
    selector: 'background-tasks',
    templateUrl: 'packages/hgprofiler/component/admin/background_tasks.html',
    useShadowDom: false
)
class BackgroundTasksComponent {
    List<Breadcrumb> crumbs = [
        new Breadcrumb('Profiler', '/'),
        new Breadcrumb('Administration', '/admin'),
        new Breadcrumb('Background Tasks'),
    ];

    bool loadingFailedTasks = false;
    bool loadingQueues = false;
    bool loadingWorkers = false;
    List<Map> failed;
    List<Map> queues;
    List<Map> workers;

    Map<String, Map> _runningJobs;

    final RestApiController _api;
    final RouteProvider _rp;
    final SseController _sse;
    final TitleService _ts;

    /// Constructor.
    BackgroundTasksComponent(this._api, this._rp, this._sse, this._ts) {
        this._ts.title = 'Background Tasks';

        // Add event listeners...
        RouteHandle rh = this._rp.route.newHandle();
        UnsubOnRouteLeave(rh, [
            this._sse.onWorker.listen(this._workerListener),
        ]);

        // Fetch data.
        this._fetchWorkers()
            .then((_) => this._fetchQueues())
            .then((_) => this._fetchFailedTasks());
    }

    /// Handle a button press to remove a single task.
    void removeFailedTask(Event event, String taskId, Function resetButton) {
        this._api
            .delete('/api/tasks/failed/$taskId', needsAuth: true)
            .then((response) {
                for (int i = 0; i < this.failed.length; i++) {
                    if (this.failed[i]['id'] == taskId) {
                        this.failed.removeAt(i);
                        break;
                    }
                }
            })
            .whenComplete(resetButton);
    }

    /// Fetch failed task data.
    Future _fetchFailedTasks() {
        Completer completer = new Completer();
        this.loadingFailedTasks = true;

        this._api
            .get('/api/tasks/failed', needsAuth: true)
            .then((response) {
                this.failed = response.data['failed'];
            })
            .whenComplete(() {
                this.loadingFailedTasks = false;
                completer.complete();
            });

        return completer.future;
    }

    /// Fetch queue data.
    Future _fetchQueues() {
        Completer completer = new Completer();
        this.loadingQueues = true;

        this._api
            .get('/api/tasks/queues', needsAuth: true)
            .then((response) {
                this.queues = response.data['queues'];
            })
            .whenComplete(() {
                this.loadingQueues = false;
                completer.complete();
            });

        return completer.future;
    }

    /// Fetch worker data.
    Future _fetchWorkers() {
        Completer completer = new Completer();
        this.loadingWorkers = true;

        this._api
            .get('/api/tasks/workers', needsAuth: true)
            .then((response) {
                this.workers = response.data['workers'];

                this._runningJobs = new Map<String, Map>();

                this.workers.forEach((worker) {
                    Map currentJob = worker['current_job'];

                    if (currentJob != null) {
                        this._runningJobs[currentJob['id']] = currentJob;
                    }
                });
            })
            .whenComplete(() {
                this.loadingWorkers = false;
                completer.complete();
            });

        return completer.future;
    }

    /// Listen for updates from background workers.
    void _workerListener(Event e) {
        Map json = JSON.decode(e.data);
        String status = json['status'];

        if (status == 'queued' || status == 'started' || status == 'finished') {
            // This information can only be fetched via REST.
            this._fetchWorkers().then((_) => this._fetchQueues());
        } else if (status == 'progress') {
            Map job = this._runningJobs[json['id']];

            if (job != null) {
                // Event contains all the data we need: no need for REST call.
                job['current'] = json['current'];
                job['progress'] = json['progress'];
            } else {
                // This is a job we don't know about: needs REST call.
                this._fetchWorkers().then((_) => this._fetchQueues());
            }
        } else if (status == 'failed') {
            this._fetchFailedTasks().then((_) => this._fetchWorkers());
        }
    }
}
