import 'dart:async';

import 'package:route_hierarchical/client.dart';

/// A mixin for tracking the 'page' parameter in the URL query.
abstract class CurrentPageMixin {
    int currentPage;

    /// Initialize the current page and set up a route listener to automatically
    /// update the page when the URL changes.
    void initCurrentPage(Route route, Function currentPageChanged) {
        // Get the current page number if it is set in the URL...
        if (route.queryParameters['page'] != null) {
            this.currentPage = int.parse(route.queryParameters['page']);
        } else {
            this.currentPage = 1;
        }

        // ...and pay attention to new page numbers announced in the URL.
        RouteHandle rh = route.newHandle();
        StreamSubscription subscription = rh.onEnter.listen((e) {
            int newPage;

            if (e.queryParameters['page'] == null) {
                newPage = 1;
            } else {
                newPage = int.parse(e.queryParameters['page']);
            }

            if (this.currentPage != newPage) {
                this.currentPage = newPage;
                currentPageChanged();
            }
        });

        // Clean up the event listener when we leave the route.
        rh.onLeave.listen((e) {
            subscription.cancel();
        });
    }
}
