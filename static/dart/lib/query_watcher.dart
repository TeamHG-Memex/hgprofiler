import 'dart:async';
import 'dart:html';

import 'package:route_hierarchical/client.dart';

/// Watch a URL query parameter and invoke a callback when it changes.
class QueryWatcher {
    Map<String,String> _currentValues;
    Set<string> _watchedParams;

    operator [](String param) => this._currentValues[param];

    /// Constructor.
    ///
    /// ``rh`` is a RouteHandle.
    /// ``params`` is a list of parameters to watch.
    /// ``callback`` is called when a watched value changes. It takes zero
    ///     arguments.
    QueryWatcher(RouteHandle rh, List<String> params, Function callback) {
        this._watchedParams = new Set<String>.from(params);

        // Get current values for all watched parameters...
        this._currentValues = new Map<String,String>.fromIterable(
            this._watchedParams,
            key: (param) => param,
            value: (param) => rh.queryParameters[param]
        );

        // ...and pay attention to new values announced in the route.
        StreamSubscription subscription = rh.onEnter.listen((e) {
            bool changed = false;

            for (String param in this._watchedParams) {
                if (this._currentValues[param] != e.queryParameters[param]) {
                    changed = true;
                    this._currentValues[param] = e.queryParameters[param];
                }
            }

            if (changed) {
                callback();
            }
        });

        // Clean up the event listener when we leave the route.
        rh.onLeave.take(1).listen((_) {
            subscription.cancel();
        });
    }
}


