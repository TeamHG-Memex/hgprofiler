import 'dart:html';

import 'package:angular/angular.dart';
import 'package:hgprofiler/rest_api.dart';

/// Handles server-sent events.
@Injectable()
class SseController {

    Stream<Event> onArchive;
    Stream<Event> onGroup;
    Stream<Event> onResult;
    Stream<Event> onSite;
    Stream<Event> onWorker;

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
        this.onArchive = this._eventSource.on['archive'];
        this.onGroup = this._eventSource.on['group'];
        this.onResult = this._eventSource.on['result'];
        this.onSite = this._eventSource.on['site'];
        this.onWorker = this._eventSource.on['worker'];
    }
}

/// A helper that unsubscribes a list of subscriptions when leaving a route.
///
/// This saves a lot of boilerplate code in each controller.
void UnsubOnRouteLeave(RouteHandle rh, List<StreamSubscription> listeners) {
    rh.onLeave.take(1).listen((e) {
        listeners.forEach((listener) => listener.cancel());
    });
}
