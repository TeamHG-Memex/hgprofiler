import 'dart:html';

import 'package:angular/angular.dart';
import 'package:route_hierarchical/client.dart';

/// This decorator modifies UI elements based on the currently selected route.
///
/// For example, when a menu item is clicked, we add an 'active' CSS class
/// to that element so that the user can see where they are.
@Decorator(selector: '[current-route]')
class CurrentRoute {
    Router router;
    Element element;

    /// Constructor.
    ///
    /// Takes an HTML [element] to monitor and the application's [router]. The
    /// element must contain a child <a> element. When the route changes, the
    /// anchor href's first path component will be compared to the new route's
    /// first path component. If it matches, the CSS class `active` will be
    /// added to the element. If the route does not match, then the CSS class
    /// `active` will be removed.
    CurrentRoute(Element element, Router router) {
        this.element = element;
        this.router = router;

        toggleActive(window.location.href);

        router.onRouteStart.listen((e) {
            toggleActive(e.uri);
        });
    }

    /// Returns true if the given URI matches the anchor href for this element.
    bool isRoute(String uri) {
        Element anchor;

        if (this.element is AnchorElement) {
            anchor = this.element;
        } else {
            anchor = this.element.querySelector('a');
        }

        String anchorPath = anchor.pathname.split('/')[1];
        String routePath = Uri.parse(uri).path.split('/')[1];

        return anchorPath == routePath;
    }

    /// Set the `active` CSS class on an element when it matches the currently
    /// selected route.
    void toggleActive(String uri) {
        if (isRoute(uri)) {
            element.classes.add('active');
        } else {
            element.classes.remove('active');
        }
    }
}

