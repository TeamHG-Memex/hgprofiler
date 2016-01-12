import 'dart:async';
import 'dart:html';

import 'package:hgprofiler/rest_api.dart';
import 'package:route_hierarchical/client.dart';

/// A mixin for tracking the 'sort' parameter in the URL query.
abstract class SortMixin {
    String sortDefault;
    String sortColumn;
    bool sortDescending;

    /// Initialize the current sort arguments and set up a route listener to
    /// automatically update the page when the URL changes.
    void initSort(Route route, Function sortChanged, String sortDefault) {
        this.sortDefault = sortDefault;

        // Get the current page number if it is set in the URL...
        if (route.queryParameters['sort'] == null) {
            this.sortColumn = this.parseSortColumn(this.sortDefault);
            this.sortDescending = parseSortDescending(this.sortDefault);
        } else {
            this.sortColumn = this.parseSortColumn(route.queryParameters['sort']);
            this.sortDescending = parseSortDescending(route.queryParameters['sort']);
        }

        // ...and pay attention to new sort arguments in the URL.
        RouteHandle rh = route.newHandle();
        StreamSubscription subscription = rh.onEnter.listen((e) {
            String newSortColumn;
            bool newSortDescending;

            if (route.queryParameters['sort'] == null) {
                newSortColumn = this.parseSortColumn(this.sortDefault);
                newSortDescending = this.parseSortDescending(this.sortDefault);
            } else {
                newSortColumn = this.parseSortColumn(route.queryParameters['sort']);
                newSortDescending = this.parseSortDescending(route.queryParameters['sort']);
            }

            if (newSortColumn != this.sortColumn ||
                newSortDescending != this.sortDescending) {

                this.sortColumn = newSortColumn;
                this.sortDescending = newSortDescending;
                sortChanged();
            }
        });

        // Clean up the event listener when we leave the route.
        rh.onLeave.listen((e) {
            subscription.cancel();
        });
    }

    /// Parse the sort column out of a URL argument.
    String parseSortColumn(String sort) {
        if (sort[0] == '-') {
            return sort.substring(1);
        } else {
            return sort;
        }
    }

    /// Parse the sort direction out of a URL argument.
    bool parseSortDescending(String sort) {
        return sort[0] == '-';
    }

    /// Return an href for sorting by this column. If already sorted on this
    /// column, the href will toggle the sort direction.
    String sortHref(String columnName) {
        Uri uri = Uri.parse(window.location.toString());
        Map queryParameters = new Map.from(uri.queryParameters);

        String oldColumn;
        bool oldDescending;

        if (queryParameters['sort'] == null) {
            oldDescending = this.parseSortDescending(this.sortDefault);
            oldColumn = this.parseSortColumn(this.sortDefault);
        } else {
            oldDescending = this.parseSortDescending(queryParameters['sort']);
            oldColumn = this.parseSortColumn(queryParameters['sort']);
        }

        if (oldColumn == columnName) {
            if (oldDescending) {
                queryParameters['sort'] = columnName;
            } else {
                queryParameters['sort'] = '-${columnName}';
            }
        } else {
            queryParameters['sort'] = '-${columnName}';
        }

        return urlWithArgs(uri.path, queryParameters);
    }
}
