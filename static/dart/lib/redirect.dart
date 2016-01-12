import 'dart:async';
import 'dart:html';

/// Notifies a user of an attempt to navigate to an external URL and allows the
/// user to stop or continue.
///
/// It is implemented a route handler so that redirects can be treated like
/// regular URLs and we don't have to resort to attaching event handlers to
/// each element that might trigger navigation to an external URL.
void redirect(RoutePreEnterEvent e) {
    e.allowEnter(new Future.value(false));

    String url = Uri.decodeComponent(e.parameters['url']);
    Uri uri = Uri.parse(url);

    // Try to detect referrer scripts and strip them.
    for (var value in uri.queryParameters.values) {
        if (value.contains('://')) {
            url = value;
            break;
        }
    }

    String body = '<p>You have clicked on an external link. HGProfiler has no'
                  ' control over the contents of this remote site.</p>'
                  ' <p>If you understand what you\'re doing and you wish to'
                  ' proceed, copy and paste this URL into a new tab or'
                  ' window.</p>'
                  ' <p class="selectable">$url</p>';

    Map modal = {
        'body': body,
        'icon': 'fa-external-link-square',
        'title': 'WARNING: External Link',
        'type': 'danger',
    };

    document.dispatchEvent(new CustomEvent('modal', detail: modal));
}
