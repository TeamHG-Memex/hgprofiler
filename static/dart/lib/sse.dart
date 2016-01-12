import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/rest_api.dart';

/// Handles server-sent events.
@Injectable()
class SseController {
    Stream<Event> onWorker;
    Stream<Event> onSite;
    Stream<Event> onResult;
    Stream<Event> onGroup;

    RestApiController _api;
    EventSource _eventSource;

    /// Constructor
    SseController(this._api) {
        String url = this._api.authorizeUrl('/api/notification/');
        this._eventSource = new EventSource(url);

        this._eventSource.onError.listen((Event e) {
            window.console.log('Error connecting to SSE!');
        });

        // Set up event streams.
        this.onWorker = this._eventSource.on['worker'];
        this.onSite = this._eventSource.on['site'];
        this.onResult = this._eventSource.on['result'];
        this.onGroup = this._eventSource.on['group'];
    }
}
