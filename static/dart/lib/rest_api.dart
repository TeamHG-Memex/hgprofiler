import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'package:angular/angular.dart';

import 'package:hgprofiler/authentication.dart';

/// Offers convenience functions for interacting with the server's REST API.
@Injectable()
class RestApiController {
    final accepts = 'application/json';
    final contentType = 'application/json';

    AuthenticationController auth;
    Router router;

    /// Constructor.
    RestApiController(this.auth, this.router);

    /// Add xauth query parameter to URL. This is useful for authorizing
    /// requests made from <img> tags, where it is not possible to specify
    /// and X-Auth header.
    String authorizeUrl(String url) {
        if (url == null) {
            // If called from a view template, we may receive a null argument.
            return null;
        }

        Uri uri = Uri.parse(url);
        Map params = new Map.from(uri.queryParameters);
        params['xauth'] = this.auth.token;

        Uri authorizedUri = new Uri(
            scheme: uri.scheme,
            host: uri.host.isEmpty ? null : uri.host,
            port: uri.port,
            path: uri.path,
            queryParameters: params
        );

        return authorizedUri.toString();
    }

    /// Get an API resource and return an API response future.
    Future<ApiResponse> get(String url,
                            {Map urlArgs,
                             Map headers,
                             boolean needsAuth: false}) {

        return this._request('GET', url, headers, urlArgs, null, needsAuth);
    }

    /// Delete an API resource and return an API response future.
    Future<ApiResponse> delete(String url,
                               {Map urlArgs,
                                Map headers,
                                boolean needsAuth: false}) {

        return this._request('DELETE', url, headers, urlArgs, null, needsAuth);
    }

    /// Put an API resource and return an API response future.
    Future<ApiResponse> put(String url,
                            Map body,
                            {Map urlArgs,
                             Map headers,
                             boolean needsAuth: false}) {

        return this._request('PUT', url, headers, urlArgs, body, needsAuth);
    }

    /// Post an API resource and return an API response future.
    Future<ApiResponse> post(String url,
                             Map body,
                             {Map urlArgs,
                              Map headers,
                              boolean needsAuth: false}) {

        return this._request('POST', url, headers, urlArgs, body, needsAuth);
    }

    /// Request a resource and return an ApiResponse future.
    ///
    /// The response includes an HTTP status and a decoded JSON object.
    Future<ApiResponse> _request(String method,
                                 String url,
                                 Map customHeaders,
                                 Map urlArgs,
                                 Map body,
                                 bool needsAuth) {

        var completer = new Completer();
        var payload = null;
        var request = new HttpRequest();

        // Create request.
        var responseHandler = (_) {
            var response = new ApiResponse(request.status, request.response);
            String statusString = request.status.toString();

            if (statusString.startsWith('2')) {
                completer.complete(response);
            } else if (request.status == 401) {
                this.auth.logOut(expired: true);
            } else {
                completer.completeError(response);
            }
        };

        request.onLoadEnd.listen(responseHandler);
        request.onError.listen(responseHandler);

        if (urlArgs != null) {
            url = urlWithArgs(url, urlArgs);
        }

        request.open(method, url, async:true);

        // Assemble headers and body.
        _standardHeaders(needsAuth).forEach((key, value) {
            request.setRequestHeader(key, value);
        });

        if (customHeaders != null) {
            customHeaders.forEach((key, value) {
                request.setRequestHeader(key, value);
            });
        }

        if (body != null) {
            payload = JSON.encode(body);
        }

        // Send request.
        request.send(payload);

        return completer.future;
    }

    /// Return a map of standard headers suitable for most API requests.
    Map _standardHeaders(bool needsAuth) {
        var headers = {
            'Accept': this.accepts,
            'Content-Type': this.contentType,
        };

        if (needsAuth) {
            headers['X-Auth'] = this.auth.token;
        }

        return headers;
    }
}

/// An encapsulation for an API response, including an HTTP code and a decoded
/// JSON payload.
class ApiResponse {
    int status;
    Map data;

    ApiResponse(this.status, String responseText) {
        try {
            this.data = JSON.decode(responseText);
        } catch (e) {
            if (this.status == 0) {
                this.data = {
                    'message': 'Error: the server is not responding.'
                };
            } else {
                this.data = {
                    'message': 'Error (${this.status}): the server is not '
                               'responding correctly.'
                };
            }
        }
    }
}

/// Encode arguments and append them to the URL as a query string.
String urlWithArgs(String url, Map urlArgs) {
    List args = [];

    urlArgs.forEach((key, value) {
        args.add(Uri.encodeFull(key) +
                 '=' +
                 Uri.encodeFull(value.toString()));
    });

    return url + '?' + args.join('&');
}
